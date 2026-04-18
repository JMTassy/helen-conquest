// web-frontend/src/services/domainInference.ts
/**
 * ORACLE SUPERTEAM — Domain Inference Service
 *
 * Automatically infers claim domains from text content using keyword matching.
 */

import { DomainKeywords, InferredDomain } from '../types/oracle';

// Domain keyword definitions with weights
const DOMAIN_KEYWORDS: DomainKeywords[] = [
  {
    domain: 'Legal',
    keywords: [
      'contract', 'agreement', 'nda', 'liability', 'indemnity',
      'compliance', 'regulatory', 'gdpr', 'ccpa', 'terms of service',
      'privacy policy', 'lawsuit', 'arbitration', 'jurisdiction',
      'intellectual property', 'copyright', 'trademark', 'patent'
    ],
    weight: 1.0
  },
  {
    domain: 'Security',
    keywords: [
      'security', 'authentication', 'authorization', 'encryption',
      'vulnerability', 'exploit', 'breach', 'attack', 'penetration',
      'firewall', 'ddos', 'xss', 'sql injection', 'csrf', 'token',
      'certificate', 'ssl', 'tls', 'malware', 'phishing'
    ],
    weight: 1.0
  },
  {
    domain: 'Privacy',
    keywords: [
      'privacy', 'personal data', 'pii', 'biometric', 'facial recognition',
      'tracking', 'anonymous', 'consent', 'data collection', 'gdpr',
      'ccpa', 'right to be forgotten', 'data subject', 'pseudonymous'
    ],
    weight: 1.0
  },
  {
    domain: 'Performance',
    keywords: [
      'latency', 'throughput', 'response time', 'load time', 'performance',
      'optimization', 'speed', 'efficiency', 'scalability', 'bottleneck',
      'caching', 'database query', 'api response', 'memory usage', 'cpu'
    ],
    weight: 0.9
  },
  {
    domain: 'Infrastructure',
    keywords: [
      'backend', 'frontend', 'server', 'database', 'deployment',
      'infrastructure', 'cloud', 'aws', 'azure', 'gcp', 'kubernetes',
      'docker', 'ci/cd', 'devops', 'monitoring', 'logging', 'architecture'
    ],
    weight: 0.9
  },
  {
    domain: 'AI/ML',
    keywords: [
      'machine learning', 'artificial intelligence', 'ai', 'ml', 'model',
      'training', 'inference', 'neural network', 'deep learning',
      'algorithm', 'prediction', 'classification', 'llm', 'gpt',
      'recommendation', 'personalization', 'data science'
    ],
    weight: 0.9
  },
  {
    domain: 'UX/Design',
    keywords: [
      'user experience', 'ux', 'ui', 'interface', 'design', 'usability',
      'accessibility', 'a11y', 'wcag', 'user flow', 'wireframe',
      'prototype', 'user testing', 'feedback', 'interaction', 'layout'
    ],
    weight: 0.8
  },
  {
    domain: 'Business',
    keywords: [
      'roi', 'revenue', 'cost', 'profit', 'business', 'strategy',
      'market', 'customer', 'user', 'growth', 'retention', 'churn',
      'conversion', 'kpi', 'metrics', 'analytics', 'engagement'
    ],
    weight: 0.8
  },
  {
    domain: 'Data',
    keywords: [
      'data', 'database', 'analytics', 'metrics', 'statistics',
      'visualization', 'report', 'dashboard', 'bi', 'etl', 'pipeline',
      'dataset', 'data quality', 'data warehouse', 'sql', 'query'
    ],
    weight: 0.8
  },
  {
    domain: 'Testing',
    keywords: [
      'testing', 'test', 'qa', 'quality assurance', 'unit test',
      'integration test', 'e2e', 'regression', 'bug', 'defect',
      'test coverage', 'automation', 'jest', 'pytest', 'selenium'
    ],
    weight: 0.7
  },
  {
    domain: 'Documentation',
    keywords: [
      'documentation', 'docs', 'readme', 'api documentation', 'guide',
      'tutorial', 'specification', 'requirements', 'manual', 'wiki'
    ],
    weight: 0.6
  },
  {
    domain: 'Compliance',
    keywords: [
      'compliance', 'audit', 'regulatory', 'certification', 'standard',
      'iso', 'soc2', 'hipaa', 'pci', 'gdpr', 'policy', 'procedure'
    ],
    weight: 0.9
  }
];

export class DomainInferenceService {
  /**
   * Infer domains from claim text
   *
   * @param text - Claim assertion text
   * @param threshold - Minimum confidence score (0-1)
   * @param maxDomains - Maximum number of domains to return
   * @returns Array of inferred domains sorted by confidence
   */
  public inferDomains(
    text: string,
    threshold: number = 0.3,
    maxDomains: number = 3
  ): InferredDomain[] {
    const lowerText = text.toLowerCase();
    const results: InferredDomain[] = [];

    for (const domainDef of DOMAIN_KEYWORDS) {
      const matchedKeywords: string[] = [];
      let score = 0;

      for (const keyword of domainDef.keywords) {
        if (lowerText.includes(keyword)) {
          matchedKeywords.push(keyword);
          // Score increases with keyword length (more specific = higher weight)
          score += (keyword.split(' ').length / domainDef.keywords.length) * domainDef.weight;
        }
      }

      if (matchedKeywords.length > 0) {
        // Normalize score to 0-1 range
        const confidence = Math.min(score, 1.0);

        if (confidence >= threshold) {
          results.push({
            domain: domainDef.domain,
            confidence,
            matched_keywords: matchedKeywords
          });
        }
      }
    }

    // Sort by confidence (descending) and return top N
    return results
      .sort((a, b) => b.confidence - a.confidence)
      .slice(0, maxDomains);
  }

  /**
   * Get domain strings for a claim (for API submission)
   */
  public getDomainsForClaim(text: string): string[] {
    const inferred = this.inferDomains(text);
    return inferred.map(d => d.domain);
  }

  /**
   * Get detailed domain analysis
   */
  public analyzeDomains(text: string): {
    primary: InferredDomain | null;
    secondary: InferredDomain[];
    all: InferredDomain[];
  } {
    const all = this.inferDomains(text, 0.2, 10);

    return {
      primary: all.length > 0 ? all[0] : null,
      secondary: all.slice(1, 3),
      all
    };
  }

  /**
   * Check if text matches specific domain
   */
  public matchesDomain(text: string, domain: string): boolean {
    const inferred = this.inferDomains(text, 0.3);
    return inferred.some(d => d.domain.toLowerCase() === domain.toLowerCase());
  }

  /**
   * Get suggested domains for autocomplete
   */
  public getSuggestedDomains(): string[] {
    return DOMAIN_KEYWORDS.map(d => d.domain).sort();
  }

  /**
   * Add custom domain definition (for extensibility)
   */
  public addCustomDomain(domain: DomainKeywords): void {
    DOMAIN_KEYWORDS.push(domain);
  }
}

// Singleton instance
export const domainInference = new DomainInferenceService();
