// web-frontend/src/utils/claimFiltering.ts
/**
 * ORACLE SUPERTEAM — Claim Filtering & Sorting Utilities
 *
 * Provides filtering and sorting functionality for claim history.
 */

import { RunManifest, ClaimFilter, SortOption, VerdictState, ClaimTier } from '../types/oracle';

export class ClaimFilteringService {
  /**
   * Filter claims based on criteria
   */
  public filterClaims(
    claims: RunManifest[],
    filter: ClaimFilter
  ): RunManifest[] {
    let filtered = [...claims];

    // Filter by decision (SHIP/NO_SHIP)
    if (filter.decision) {
      filtered = filtered.filter(
        c => c.decision.final === filter.decision
      );
    }

    // Filter by date range
    if (filter.dateRange) {
      const start = new Date(filter.dateRange.start);
      const end = new Date(filter.dateRange.end);

      filtered = filtered.filter(c => {
        const claimDate = new Date(c.timestamp_start);
        return claimDate >= start && claimDate <= end;
      });
    }

    // Filter by search query (searches in claim assertion)
    if (filter.searchQuery && filter.searchQuery.trim().length > 0) {
      const query = filter.searchQuery.toLowerCase().trim();

      filtered = filtered.filter(c =>
        c.claim.assertion.toLowerCase().includes(query) ||
        c.claim.domain.some(d => d.toLowerCase().includes(query)) ||
        c.claim.owner_team.toLowerCase().includes(query)
      );
    }

    // Filter by tier
    if (filter.tier) {
      filtered = filtered.filter(c => c.claim.tier === filter.tier);
    }

    // Filter by domain
    if (filter.domain && filter.domain.length > 0) {
      filtered = filtered.filter(c =>
        filter.domain!.some(filterDomain =>
          c.claim.domain.some(claimDomain =>
            claimDomain.toLowerCase() === filterDomain.toLowerCase()
          )
        )
      );
    }

    // Filter by team
    if (filter.team) {
      filtered = filtered.filter(c =>
        c.signals?.some(s => s.team === filter.team) ||
        c.claim.owner_team === filter.team
      );
    }

    return filtered;
  }

  /**
   * Sort claims based on criteria
   */
  public sortClaims(
    claims: RunManifest[],
    sortOption: SortOption
  ): RunManifest[] {
    const sorted = [...claims];

    sorted.sort((a, b) => {
      let comparison = 0;

      switch (sortOption.field) {
        case 'timestamp':
          comparison = new Date(a.timestamp_start).getTime() - new Date(b.timestamp_start).getTime();
          break;

        case 'tier':
          const tierOrder = { 'Tier I': 3, 'Tier II': 2, 'Tier III': 1 };
          comparison = tierOrder[a.claim.tier] - tierOrder[b.claim.tier];
          break;

        case 'decision':
          comparison = a.decision.final.localeCompare(b.decision.final);
          break;

        case 'score':
          comparison = a.derived.qi_int.S_c - b.derived.qi_int.S_c;
          break;

        default:
          comparison = 0;
      }

      return sortOption.direction === 'desc' ? -comparison : comparison;
    });

    return sorted;
  }

  /**
   * Get unique values for filter options
   */
  public getFilterOptions(claims: RunManifest[]): {
    tiers: ClaimTier[];
    domains: string[];
    teams: string[];
    decisions: VerdictState[];
  } {
    const tiers = new Set<ClaimTier>();
    const domains = new Set<string>();
    const teams = new Set<string>();
    const decisions = new Set<VerdictState>();

    for (const claim of claims) {
      tiers.add(claim.claim.tier);
      decisions.add(claim.decision.final);
      teams.add(claim.claim.owner_team);

      for (const domain of claim.claim.domain) {
        domains.add(domain);
      }

      if (claim.signals) {
        for (const signal of claim.signals) {
          teams.add(signal.team);
        }
      }
    }

    return {
      tiers: Array.from(tiers).sort(),
      domains: Array.from(domains).sort(),
      teams: Array.from(teams).sort(),
      decisions: Array.from(decisions).sort()
    };
  }

  /**
   * Get statistics for filtered claims
   */
  public getStatistics(claims: RunManifest[]): {
    total: number;
    shipped: number;
    blocked: number;
    killSwitch: number;
    avgScore: number;
    openObligations: number;
  } {
    const total = claims.length;
    const shipped = claims.filter(c => c.decision.ship_permitted).length;
    const blocked = total - shipped;
    const killSwitch = claims.filter(c => c.derived.kill_switch_triggered).length;

    const avgScore = claims.length > 0
      ? claims.reduce((sum, c) => sum + c.derived.qi_int.S_c, 0) / claims.length
      : 0;

    const openObligations = claims.reduce(
      (sum, c) => sum + c.derived.obligations_open.length,
      0
    );

    return {
      total,
      shipped,
      blocked,
      killSwitch,
      avgScore,
      openObligations
    };
  }

  /**
   * Search claims by multiple criteria (advanced search)
   */
  public advancedSearch(
    claims: RunManifest[],
    criteria: {
      text?: string;
      hasKillSwitch?: boolean;
      hasObligations?: boolean;
      minScore?: number;
      maxScore?: number;
      hasContradictions?: boolean;
    }
  ): RunManifest[] {
    let results = [...claims];

    if (criteria.text) {
      const query = criteria.text.toLowerCase();
      results = results.filter(c =>
        c.claim.assertion.toLowerCase().includes(query) ||
        c.derived.obligations_open.some(o =>
          o.closure_criteria.toLowerCase().includes(query)
        ) ||
        c.decision.reason_codes.some(r => r.toLowerCase().includes(query))
      );
    }

    if (criteria.hasKillSwitch !== undefined) {
      results = results.filter(c =>
        c.derived.kill_switch_triggered === criteria.hasKillSwitch
      );
    }

    if (criteria.hasObligations !== undefined) {
      results = results.filter(c =>
        (c.derived.obligations_open.length > 0) === criteria.hasObligations
      );
    }

    if (criteria.minScore !== undefined) {
      results = results.filter(c =>
        c.derived.qi_int.S_c >= criteria.minScore!
      );
    }

    if (criteria.maxScore !== undefined) {
      results = results.filter(c =>
        c.derived.qi_int.S_c <= criteria.maxScore!
      );
    }

    if (criteria.hasContradictions !== undefined) {
      results = results.filter(c =>
        (c.derived.contradictions.length > 0) === criteria.hasContradictions
      );
    }

    return results;
  }

  /**
   * Group claims by a field
   */
  public groupClaims(
    claims: RunManifest[],
    groupBy: 'decision' | 'tier' | 'domain' | 'team' | 'date'
  ): Record<string, RunManifest[]> {
    const groups: Record<string, RunManifest[]> = {};

    for (const claim of claims) {
      let key: string;

      switch (groupBy) {
        case 'decision':
          key = claim.decision.final;
          break;

        case 'tier':
          key = claim.claim.tier;
          break;

        case 'domain':
          key = claim.claim.domain[0] || 'Unspecified';
          break;

        case 'team':
          key = claim.claim.owner_team;
          break;

        case 'date':
          const date = new Date(claim.timestamp_start);
          key = date.toISOString().split('T')[0]; // YYYY-MM-DD
          break;

        default:
          key = 'Other';
      }

      if (!groups[key]) {
        groups[key] = [];
      }
      groups[key].push(claim);
    }

    return groups;
  }

  /**
   * Export filtered claims to JSON
   */
  public exportToJSON(claims: RunManifest[]): string {
    return JSON.stringify(claims, null, 2);
  }

  /**
   * Export filtered claims to CSV
   */
  public exportToCSV(claims: RunManifest[]): string {
    const headers = [
      'Timestamp',
      'Claim ID',
      'Assertion',
      'Tier',
      'Domain',
      'Decision',
      'Ship Permitted',
      'QI-INT Score',
      'Kill Switch',
      'Obligations',
      'Reason Codes'
    ];

    const rows = claims.map(c => [
      c.timestamp_start,
      c.claim.id,
      `"${c.claim.assertion.replace(/"/g, '""')}"`,
      c.claim.tier,
      c.claim.domain.join('; '),
      c.decision.final,
      c.decision.ship_permitted,
      c.derived.qi_int.S_c.toFixed(4),
      c.derived.kill_switch_triggered,
      c.derived.obligations_open.length,
      c.decision.reason_codes.join('; ')
    ]);

    return [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
  }
}

// Singleton instance
export const claimFiltering = new ClaimFilteringService();
