// web-frontend/src/services/geminiService.ts
/**
 * ORACLE SUPERTEAM — Gemini AI Service
 *
 * Handles AI-powered claim analysis and conditional team activation.
 */

import { TeamType, Signal, SignalType, ObligationType, Claim } from '../types/oracle';

// Legal keywords that trigger Legal Office team
const LEGAL_KEYWORDS = [
  'contract', 'nda', 'non-disclosure', 'liability', 'indemnity',
  'warranty', 'terms of service', 'tos', 'privacy policy',
  'gdpr', 'ccpa', 'compliance', 'regulatory', 'lawsuit',
  'intellectual property', 'copyright', 'trademark', 'patent',
  'license', 'agreement', 'jurisdiction', 'arbitration'
];

// Security keywords
const SECURITY_KEYWORDS = [
  'encryption', 'authentication', 'authorization', 'vulnerability',
  'exploit', 'attack', 'breach', 'security', 'penetration',
  'firewall', 'ddos', 'xss', 'sql injection', 'csrf',
  'password', 'credential', 'token', 'certificate'
];

// Privacy keywords
const PRIVACY_KEYWORDS = [
  'personal data', 'pii', 'biometric', 'facial recognition',
  'tracking', 'anonymous', 'pseudonymous', 'consent',
  'data collection', 'user data', 'privacy'
];

export class GeminiService {
  private apiKey: string | null = null;
  private baseUrl = 'https://generativelanguage.googleapis.com/v1beta';

  constructor() {
    this.loadApiKey();
  }

  /**
   * Load API key from localStorage
   */
  private loadApiKey(): void {
    const stored = localStorage.getItem('oracle_gemini_key');
    if (stored) {
      try {
        const config = JSON.parse(stored);
        this.apiKey = config.key;
      } catch (e) {
        console.error('Failed to parse stored API key:', e);
      }
    }
  }

  /**
   * Set and persist API key
   */
  public setApiKey(key: string): void {
    this.apiKey = key;
    const config = {
      key,
      provider: 'gemini',
      encrypted: false,
      created_at: new Date().toISOString()
    };
    localStorage.setItem('oracle_gemini_key', JSON.stringify(config));
  }

  /**
   * Check if API key is configured
   */
  public hasApiKey(): boolean {
    return this.apiKey !== null && this.apiKey.length > 0;
  }

  /**
   * Clear API key
   */
  public clearApiKey(): void {
    this.apiKey = null;
    localStorage.removeItem('oracle_gemini_key');
  }

  /**
   * Detect if Legal team should be activated based on claim keywords
   */
  public shouldActivateLegalTeam(claimText: string): boolean {
    const lowerText = claimText.toLowerCase();
    return LEGAL_KEYWORDS.some(keyword => lowerText.includes(keyword));
  }

  /**
   * Detect if Security team should be activated
   */
  public shouldActivateSecurityTeam(claimText: string): boolean {
    const lowerText = claimText.toLowerCase();
    return SECURITY_KEYWORDS.some(keyword => lowerText.includes(keyword));
  }

  /**
   * Detect privacy concerns
   */
  public hasPrivacyConcerns(claimText: string): boolean {
    const lowerText = claimText.toLowerCase();
    return PRIVACY_KEYWORDS.some(keyword => lowerText.includes(keyword));
  }

  /**
   * Get activated teams based on claim content
   */
  public getActivatedTeams(claim: Claim): TeamType[] {
    const teams: TeamType[] = [
      TeamType.STRATEGY, // Always active
      TeamType.ENGINEERING, // Always active for technical review
    ];

    // Conditional activation
    if (this.shouldActivateLegalTeam(claim.assertion)) {
      teams.push(TeamType.LEGAL);
    }

    if (this.shouldActivateSecurityTeam(claim.assertion)) {
      teams.push(TeamType.SECURITY);
    }

    if (this.hasPrivacyConcerns(claim.assertion)) {
      if (!teams.includes(TeamType.LEGAL)) {
        teams.push(TeamType.LEGAL);
      }
      if (!teams.includes(TeamType.SECURITY)) {
        teams.push(TeamType.SECURITY);
      }
    }

    // Add data validation for Tier I claims
    if (claim.tier === 'Tier I') {
      teams.push(TeamType.DATA_VALIDATION);
    }

    return teams;
  }

  /**
   * Analyze claim using Gemini AI (if API key available)
   */
  public async analyzeClaim(claim: Claim): Promise<Signal[]> {
    if (!this.hasApiKey()) {
      // Fallback: Basic rule-based analysis
      return this.analyzeClaimRuleBased(claim);
    }

    try {
      const response = await fetch(
        `${this.baseUrl}/models/gemini-pro:generateContent?key=${this.apiKey}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            contents: [{
              parts: [{
                text: this.buildAnalysisPrompt(claim)
              }]
            }],
            generationConfig: {
              temperature: 0.1, // Low temperature for deterministic output
              maxOutputTokens: 1000,
            }
          })
        }
      );

      if (!response.ok) {
        console.error('Gemini API error:', await response.text());
        return this.analyzeClaimRuleBased(claim);
      }

      const data = await response.json();
      const text = data.candidates?.[0]?.content?.parts?.[0]?.text;

      if (text) {
        return this.parseGeminiResponse(text, claim);
      }

      return this.analyzeClaimRuleBased(claim);
    } catch (error) {
      console.error('Failed to analyze with Gemini:', error);
      return this.analyzeClaimRuleBased(claim);
    }
  }

  /**
   * Build analysis prompt for Gemini
   */
  private buildAnalysisPrompt(claim: Claim): string {
    return `You are an expert governance analyst for ORACLE SUPERTEAM, a constitutional decision-making framework.

Analyze this claim and provide signals for each relevant team:

CLAIM: "${claim.assertion}"
TIER: ${claim.tier}
DOMAIN: ${claim.domain.join(', ')}

Your task:
1. Identify which teams should review this claim
2. For each team, determine if they should:
   - APPROVE (no concerns)
   - OBLIGATION_OPEN (request specific evidence/action)
   - RISK_FLAG (surface concern for review)
   - EVIDENCE_WEAK (insufficient evidence quality)
   - KILL_REQUEST (critical issue, authorized teams only)

Available teams:
- Legal Office (contracts, compliance, regulatory)
- Security Sector (security, vulnerabilities, threats)
- Engineering Wing (technical feasibility, metrics)
- Data Validation Office (evidence quality, statistical rigor)
- Strategy HQ (business alignment, strategic fit)

Respond in JSON format:
{
  "signals": [
    {
      "team": "Team Name",
      "signal_type": "SIGNAL_TYPE",
      "obligation_type": "OBLIGATION_TYPE" (if OBLIGATION_OPEN),
      "rationale": "Brief explanation"
    }
  ]
}

Be conservative: flag concerns rather than approve without evidence.`;
  }

  /**
   * Parse Gemini response into signals
   */
  private parseGeminiResponse(text: string, claim: Claim): Signal[] {
    try {
      // Extract JSON from response
      const jsonMatch = text.match(/\{[\s\S]*\}/);
      if (!jsonMatch) {
        return this.analyzeClaimRuleBased(claim);
      }

      const parsed = JSON.parse(jsonMatch[0]);
      const signals: Signal[] = [];

      for (const sig of parsed.signals || []) {
        // Map team name to TeamType enum
        const teamMap: Record<string, TeamType> = {
          'Legal Office': TeamType.LEGAL,
          'Security Sector': TeamType.SECURITY,
          'Engineering Wing': TeamType.ENGINEERING,
          'Data Validation Office': TeamType.DATA_VALIDATION,
          'Strategy HQ': TeamType.STRATEGY,
          'COO HQ': TeamType.COO,
          'UX/Impact Bureau': TeamType.UX_IMPACT
        };

        const team = teamMap[sig.team];
        if (!team) continue;

        signals.push({
          team,
          signal_type: sig.signal_type as SignalType,
          obligation_type: sig.obligation_type as ObligationType,
          rationale: sig.rationale,
          timestamp: new Date().toISOString()
        });
      }

      return signals.length > 0 ? signals : this.analyzeClaimRuleBased(claim);
    } catch (error) {
      console.error('Failed to parse Gemini response:', error);
      return this.analyzeClaimRuleBased(claim);
    }
  }

  /**
   * Rule-based analysis (fallback when no API key)
   */
  private analyzeClaimRuleBased(claim: Claim): Signal[] {
    const signals: Signal[] = [];
    const activatedTeams = this.getActivatedTeams(claim);

    // Strategy HQ
    if (activatedTeams.includes(TeamType.STRATEGY)) {
      signals.push({
        team: TeamType.STRATEGY,
        signal_type: 'OBLIGATION_OPEN',
        rationale: 'Strategic alignment review required',
        timestamp: new Date().toISOString()
      });
    }

    // Engineering Wing
    if (activatedTeams.includes(TeamType.ENGINEERING)) {
      signals.push({
        team: TeamType.ENGINEERING,
        signal_type: 'OBLIGATION_OPEN',
        obligation_type: 'METRICS_INSUFFICIENT',
        rationale: 'Need technical feasibility analysis and metrics',
        timestamp: new Date().toISOString()
      });
    }

    // Legal Office (conditional)
    if (activatedTeams.includes(TeamType.LEGAL)) {
      signals.push({
        team: TeamType.LEGAL,
        signal_type: 'OBLIGATION_OPEN',
        obligation_type: 'LEGAL_COMPLIANCE',
        rationale: 'Legal/compliance review required for contract-related claim',
        timestamp: new Date().toISOString()
      });
    }

    // Security Sector (conditional)
    if (activatedTeams.includes(TeamType.SECURITY)) {
      signals.push({
        team: TeamType.SECURITY,
        signal_type: 'OBLIGATION_OPEN',
        obligation_type: 'SECURITY_THREAT',
        rationale: 'Security assessment required',
        timestamp: new Date().toISOString()
      });
    }

    // Data Validation for Tier I
    if (activatedTeams.includes(TeamType.DATA_VALIDATION)) {
      signals.push({
        team: TeamType.DATA_VALIDATION,
        signal_type: 'OBLIGATION_OPEN',
        obligation_type: 'EVIDENCE_MISSING',
        rationale: 'Tier I claim requires verified evidence and receipts',
        timestamp: new Date().toISOString()
      });
    }

    return signals;
  }
}

// Singleton instance
export const geminiService = new GeminiService();
