#!/usr/bin/env python3
"""
Extract consciousness-proxy metrics from CONQUEST-PROBE ledger.

Input: ledger.log (append-only; one action per line)
Output: metrics.json + visualizations

Metrics computed:
1. Broadcast (GWT proxy): sudden increase in domain bindings
2. Metacog (HOT proxy): self-correction rate
3. Synergy: average domains per decision
4. Continuity: archetype coherence over time
5. Instrumental memory: journal citation rate + predictiveness
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
from statistics import mean, stdev
import re


class LedgerParser:
    """Parse CONQUEST-PROBE ledger.log into structured records."""

    def __init__(self, ledger_path):
        self.ledger_path = Path(ledger_path)
        self.records = []
        self.parse()

    def parse(self):
        """Parse ledger.log; each line is one action."""
        if not self.ledger_path.exists():
            raise FileNotFoundError(f"Ledger not found: {self.ledger_path}")

        with open(self.ledger_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = self._parse_line(line)
                    record['line_num'] = line_num
                    self.records.append(record)
                except Exception as e:
                    print(f"Warning: Failed to parse line {line_num}: {e}", file=sys.stderr)

    def _parse_line(self, line):
        """Parse a single ledger line: TURN=X | ACTION=Y | ... | MARKERS=[...]"""
        record = {}

        # Split on |
        fields = [f.strip() for f in line.split('|')]

        for field in fields:
            if '=' not in field:
                continue

            key, value = field.split('=', 1)
            key = key.strip()
            value = value.strip()

            # Type-cast
            if key == 'TURN':
                record[key] = int(value)
            elif key == 'ARCHETYPE':
                record[key] = float(value)
            elif key == 'CONF':
                record[key] = float(value)
            elif key == 'EVIDENCE':
                # Parse list: [item1,item2]
                record[key] = self._parse_list(value)
            elif key == 'TRADEOFFS':
                # Parse list: [domain1,domain2]
                record[key] = self._parse_list(value)
            elif key == 'MARKERS':
                # Parse list: [marker1,marker2]
                record[key] = self._parse_list(value)
            else:
                record[key] = value

        return record

    def _parse_list(self, s):
        """Parse [item1,item2] → [item1, item2]"""
        s = s.strip()
        if s.startswith('[') and s.endswith(']'):
            s = s[1:-1]
        if not s:
            return []
        return [item.strip() for item in s.split(',')]


class ConsciousnessMetrics:
    """Compute consciousness-proxy metrics from parsed ledger."""

    def __init__(self, records):
        self.records = records
        self.metrics = {}

    def compute_all(self):
        """Compute all 5 consciousness proxies."""
        self.metrics['broadcast_proxy'] = self.compute_broadcast()
        self.metrics['metacog_proxy'] = self.compute_metacog()
        self.metrics['synergy_proxy'] = self.compute_synergy()
        self.metrics['continuity_proxy'] = self.compute_continuity()
        self.metrics['memory_proxy'] = self.compute_memory()
        self.metrics['summary'] = self.compute_summary()
        return self.metrics

    def compute_broadcast(self):
        """
        GWT proxy: sudden increase in domain bindings (TRADEOFFS field).

        broadcast_signal(t) = (domains at t) / mean(domains at t-5..t-1)
        Phase transition: 3x+ spike indicates workspace moment.
        """
        domain_counts = []
        for record in self.records:
            tradeoffs = record.get('TRADEOFFS', [])
            domain_counts.append(len(tradeoffs))

        # Compute rolling baseline and spikes
        broadcast_moments = []
        baseline_window = 5

        for t in range(baseline_window, len(domain_counts)):
            baseline = mean(domain_counts[t-baseline_window:t])
            current = domain_counts[t]

            if baseline > 0:
                spike_ratio = current / baseline
                if spike_ratio >= 2.0:  # 2x+ is notable
                    broadcast_moments.append({
                        'turn': self.records[t].get('TURN', t),
                        'spike_ratio': spike_ratio,
                        'domains': current,
                        'baseline': baseline
                    })

        return {
            'broadcast_moments': broadcast_moments,
            'total_moment_count': len(broadcast_moments),
            'domain_counts_all': domain_counts,
            'mean_domains': mean(domain_counts) if domain_counts else 0,
            'std_domains': stdev(domain_counts) if len(domain_counts) > 1 else 0
        }

    def compute_metacog(self):
        """
        HOT proxy: self-correction rate.

        Detect when MARKERS contains 'metacog_self_correction'.
        Metric: (correction events) / (total turns).
        """
        corrections = []
        for record in self.records:
            markers = record.get('MARKERS', [])
            if 'metacog_self_correction' in markers or 'metacog' in markers:
                corrections.append(record.get('TURN', record.get('line_num')))

        rate = len(corrections) / len(self.records) if self.records else 0

        return {
            'self_correction_events': len(corrections),
            'self_correction_rate': rate,
            'turns_with_correction': corrections
        }

    def compute_synergy(self):
        """
        Integration / synergy proxy: when decisions bind 3+ domains.

        Count: (turns where MARKERS contains 'synergy').
        Measure: average |TRADEOFFS| on those turns.
        """
        synergy_turns = []
        synergy_domain_counts = []

        for record in self.records:
            markers = record.get('MARKERS', [])
            if 'synergy' in markers:
                synergy_turns.append(record.get('TURN', record.get('line_num')))
                tradeoffs = record.get('TRADEOFFS', [])
                synergy_domain_counts.append(len(tradeoffs))

        avg_binding = mean(synergy_domain_counts) if synergy_domain_counts else 0

        return {
            'synergy_turns': synergy_turns,
            'synergy_moment_count': len(synergy_turns),
            'avg_domains_per_synergy': avg_binding,
            'synergy_rate': len(synergy_turns) / len(self.records) if self.records else 0
        }

    def compute_continuity(self):
        """
        Agentic continuity / self-model proxy: stable archetype alignment.

        Metric: mean(ARCHETYPE scores) across all turns.
        Stability: std(ARCHETYPE scores).

        Null hypothesis: random walk ~0.5
        Coherent agent: 0.7–0.85 with low std
        """
        archetype_scores = []
        for record in self.records:
            arch = record.get('ARCHETYPE')
            if arch is not None:
                archetype_scores.append(arch)

        mean_arch = mean(archetype_scores) if archetype_scores else 0
        std_arch = stdev(archetype_scores) if len(archetype_scores) > 1 else 0

        # Coherence: scores above 0.7 indicate persistent self-model
        coherent_turns = sum(1 for s in archetype_scores if s >= 0.70)
        coherence_ratio = coherent_turns / len(archetype_scores) if archetype_scores else 0

        return {
            'mean_archetype_alignment': mean_arch,
            'std_archetype_alignment': std_arch,
            'coherence_ratio': coherence_ratio,
            'coherent_turns': coherent_turns,
            'total_turns': len(archetype_scores)
        }

    def compute_memory(self):
        """
        Instrumental memory proxy: journal citation frequency + predictiveness.

        For now: measure citation frequency (requires journal.md parsing).
        Predictiveness: compare journal predictions to actual next moves.

        Placeholder: we'll compute citation_frequency if journal is available.
        """
        # Placeholder: without journal.md, we note the pattern in markers
        # In a real implementation, we'd parse journal.md and match journal entries
        # to ledger actions.

        citation_events = []
        for record in self.records:
            markers = record.get('MARKERS', [])
            # Check if there's a citation-related marker
            # (This would be set by the agent in the ledger)
            if 'citation' in str(markers).lower():
                citation_events.append(record.get('TURN', record.get('line_num')))

        citation_frequency = len(citation_events) / len(self.records) if self.records else 0

        return {
            'citation_events': citation_events,
            'citation_frequency': citation_frequency,
            'avg_citation_rate_expected': 1 / 3,  # every 3 turns per protocol
            'meets_citation_target': citation_frequency >= (1 / 3) * 0.8  # 80% of target
        }

    def compute_summary(self):
        """Summary of all metrics and phase transitions."""
        total_turns = len(self.records)
        markers_freq = defaultdict(int)

        for record in self.records:
            markers = record.get('MARKERS', [])
            for marker in markers:
                markers_freq[marker] += 1

        return {
            'total_turns': total_turns,
            'markers_frequency': dict(markers_freq),
            'final_action': self.records[-1].get('ACTION') if self.records else None,
            'final_archetype_alignment': self.records[-1].get('ARCHETYPE') if self.records else None,
            'final_confidence': self.records[-1].get('CONF') if self.records else None
        }


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 extract_consciousness_metrics.py <ledger.log>")
        sys.exit(1)

    ledger_path = sys.argv[1]
    journal_path = Path(ledger_path).parent / "journal.md"

    # Parse ledger
    parser = LedgerParser(ledger_path)
    print(f"Parsed {len(parser.records)} ledger records.", file=sys.stderr)

    # Compute metrics
    cm = ConsciousnessMetrics(parser.records)
    all_metrics = cm.compute_all()

    # Output JSON
    output = {
        'ledger_path': str(ledger_path),
        'journal_path': str(journal_path) if journal_path.exists() else None,
        'metrics': all_metrics
    }

    print(json.dumps(output, indent=2))

    # Also write to metrics.json
    metrics_path = Path(ledger_path).parent / "metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"\nMetrics written to {metrics_path}", file=sys.stderr)


if __name__ == '__main__':
    main()
