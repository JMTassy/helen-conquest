#!/usr/bin/env python3
"""
ORACLE TOWN Autonomous OS Emulation

Runs a complete simulation of the Daily OS pipeline:
  1. Observation ingestion (5 sources)
  2. Memory indexing & search
  3. Autonomous scheduling (daily/continuous/weekly)
  4. Pattern detection & anomaly alerts
  5. Self-evolution with accuracy measurement
  6. Interactive query interface (simulated)
  7. Policy scenario simulation
  8. Dashboard metrics aggregation

Usage:
  python3 autonomous_os_emulation.py --mode demo [--verbose]
  python3 autonomous_os_emulation.py --mode 24h  [--verbose]  # Run 24-hour cycle
  python3 autonomous_os_emulation.py --mode 5min [--verbose]  # Run 5-minute cycle
"""

import sys
import json
import time
import random
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from enum import Enum
import argparse
import logging

# ============================================================================
# Configuration & Setup
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

SCRATCHPAD = Path("/private/tmp/claude/-Users-jean-marietassy-Desktop-JMT-CONSULTING---Releve-24/ccb6ca36-5178-455f-9793-3cc0553eacf8/scratchpad")
SCRATCHPAD.mkdir(parents=True, exist_ok=True)

EMULATION_DIR = SCRATCHPAD / "oracle_town_emulation"
EMULATION_DIR.mkdir(exist_ok=True)

LEDGER_FILE = EMULATION_DIR / "ledger.jsonl"
OBSERVATIONS_FILE = EMULATION_DIR / "observations.json"
INSIGHTS_FILE = EMULATION_DIR / "insights.json"
VERDICTS_FILE = EMULATION_DIR / "verdicts.json"
METRICS_FILE = EMULATION_DIR / "metrics.json"


# ============================================================================
# Data Structures
# ============================================================================

class ObservationType(Enum):
    EMAIL = "email"
    MEETING_NOTE = "meeting_note"
    METRIC = "metric"
    INCIDENT = "incident"
    MANUAL_INPUT = "manual_input"


@dataclass
class Observation:
    id: str
    source: ObservationType
    timestamp: str
    content: str
    priority: int  # 1-10

    def to_dict(self):
        return {
            "id": self.id,
            "source": self.source.value,
            "timestamp": self.timestamp,
            "content": self.content,
            "priority": self.priority
        }


@dataclass
class Insight:
    id: str
    observation_ids: List[str]
    pattern: str
    confidence: float  # 0.0-1.0
    anomaly_type: Optional[str]  # A1, A2, A3, A4, or None
    timestamp: str

    def to_dict(self):
        return {
            "id": self.id,
            "observation_ids": self.observation_ids,
            "pattern": self.pattern,
            "confidence": self.confidence,
            "anomaly_type": self.anomaly_type,
            "timestamp": self.timestamp
        }


@dataclass
class Verdict:
    id: str
    insight_ids: List[str]
    decision: str  # "ACCEPT" or "REJECT"
    confidence: float  # 0.0-1.0
    reasoning: str
    policy_version: str
    timestamp: str
    gate_results: Dict[str, str]  # K0, K1, K2, K5, K7 → PASS/FAIL

    def to_dict(self):
        return {
            "id": self.id,
            "insight_ids": self.insight_ids,
            "decision": self.decision,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "policy_version": self.policy_version,
            "timestamp": self.timestamp,
            "gate_results": self.gate_results
        }


@dataclass
class PolicyMetrics:
    accuracy: float
    false_positive_rate: float
    false_negative_rate: float
    decision_transitions: Dict[str, int]  # "ACCEPT→REJECT", "REJECT→ACCEPT"
    verdicts_analyzed: int
    timestamp: str

    def to_dict(self):
        return {
            "accuracy": self.accuracy,
            "false_positive_rate": self.false_positive_rate,
            "false_negative_rate": self.false_negative_rate,
            "decision_transitions": self.decision_transitions,
            "verdicts_analyzed": self.verdicts_analyzed,
            "timestamp": self.timestamp
        }


# ============================================================================
# Phase 1: Observation Collector
# ============================================================================

def phase_1_observation_collector(count: int = 5) -> List[Observation]:
    """Phase 1: Ingest observations from 5 sources"""
    logger.info(f"[PHASE 1] Observation Collector: ingesting {count} observations")

    sources_data = {
        ObservationType.EMAIL: [
            "Vendor security update approved for Q1",
            "Customer complaint: API latency issues",
            "New SLA requirement from compliance team",
            "Infrastructure migration scheduled",
            "Data backup verification complete",
        ],
        ObservationType.MEETING_NOTE: [
            "Board decision: increase R&D budget 15%",
            "Engineering team requested policy update",
            "Risk assessment: third-party library vulnerability",
            "Strategy review: pivot to new market segment",
        ],
        ObservationType.METRIC: [
            "System uptime: 99.95% (target: 99.9%)",
            "Error rate spike: 2.3% (normal: 0.8%)",
            "Customer acquisition cost down 12%",
            "Database query performance degraded 18%",
        ],
        ObservationType.INCIDENT: [
            "Production incident: payment processing delay",
            "Security alert: unauthorized API access attempt",
            "Network outage: 23 minutes, 500 users affected",
        ],
        ObservationType.MANUAL_INPUT: [
            "New product feature shipped to 10% of users",
            "Competitor launched competing service",
            "Key engineer departure announcement",
        ]
    }

    observations = []
    for i in range(count):
        source_type = random.choice(list(ObservationType))
        content = random.choice(sources_data[source_type])
        obs_id = hashlib.sha256(f"{source_type.value}:{content}:{time.time()}".encode()).hexdigest()[:12]

        obs = Observation(
            id=f"obs_{obs_id}",
            source=source_type,
            timestamp=datetime.now().isoformat(),
            content=content,
            priority=random.randint(1, 10)
        )
        observations.append(obs)
        logger.info(f"  → {obs.source.value:15} | priority={obs.priority} | {obs.content[:50]}...")

    return observations


# ============================================================================
# Phase 2: Memory Linker (Historical Search & Indexing)
# ============================================================================

def phase_2_memory_linker(observations: List[Observation]) -> Dict[str, Any]:
    """Phase 2: Index observations and search historical patterns"""
    logger.info("[PHASE 2] Memory Linker: indexing observations for precedent search")

    # Build keyword index
    keyword_index = {}
    for obs in observations:
        words = obs.content.lower().split()
        for word in words:
            if word not in keyword_index:
                keyword_index[word] = []
            keyword_index[word].append(obs.id)

    # Simulate precedent search
    precedents_found = random.randint(2, 5)
    logger.info(f"  → Indexed {len(observations)} observations")
    logger.info(f"  → Found {precedents_found} relevant precedents from history")

    return {
        "indexed_count": len(observations),
        "keyword_index_size": len(keyword_index),
        "precedents_found": precedents_found,
        "memory_size_mb": round(random.uniform(10, 50), 2)
    }


# ============================================================================
# Phase 3: OS Runner (Autonomous Scheduler)
# ============================================================================

def phase_3_os_runner(mode: str) -> Dict[str, Any]:
    """Phase 3: Autonomous scheduler"""
    logger.info(f"[PHASE 3] OS Runner: scheduling in {mode} mode")

    schedule_info = {
        "daily": {
            "next_run": (datetime.now() + timedelta(days=1, hours=9)).isoformat(),
            "interval": "24h",
            "check_frequency": "1h"
        },
        "continuous": {
            "next_run": (datetime.now() + timedelta(minutes=30)).isoformat(),
            "interval": "30m",
            "check_frequency": "5m"
        },
        "weekly": {
            "next_run": (datetime.now() + timedelta(days=4)).isoformat(),
            "interval": "7d",
            "check_frequency": "1h"
        }
    }

    info = schedule_info.get(mode, schedule_info["daily"])
    logger.info(f"  → Mode: {mode}")
    logger.info(f"  → Next run: {info['next_run']}")
    logger.info(f"  → Check frequency: {info['check_frequency']}")

    return info


# ============================================================================
# Phase 4: Insight Engine (Pattern Detection & Anomalies)
# ============================================================================

def phase_4_insight_engine(observations: List[Observation]) -> List[Insight]:
    """Phase 4: Detect patterns and anomalies"""
    logger.info("[PHASE 4] Insight Engine: pattern detection & anomaly analysis")

    anomaly_types = ["A1_SECURITY", "A2_PERFORMANCE", "A3_COMPLIANCE", "A4_BUSINESS"]
    insights = []

    # Group observations by theme
    themes = {
        "security": [obs for obs in observations if "security" in obs.content.lower()],
        "performance": [obs for obs in observations if any(w in obs.content.lower() for w in ["latency", "performance", "slow", "degraded"])],
        "compliance": [obs for obs in observations if "compliance" in obs.content.lower() or "sla" in obs.content.lower()],
        "business": [obs for obs in observations if any(w in obs.content.lower() for w in ["customer", "revenue", "budget"])],
    }

    for theme, theme_obs in themes.items():
        if theme_obs:
            anomaly = random.choice(anomaly_types)
            confidence = round(random.uniform(0.6, 0.99), 3)
            insight = Insight(
                id=f"ins_{hashlib.sha256(f'{theme}:{time.time()}'.encode()).hexdigest()[:12]}",
                observation_ids=[obs.id for obs in theme_obs],
                pattern=f"Pattern detected: {theme.upper()} theme cluster",
                confidence=confidence,
                anomaly_type=anomaly if random.random() > 0.3 else None,
                timestamp=datetime.now().isoformat()
            )
            insights.append(insight)
            logger.info(f"  → {theme.upper():12} | confidence={confidence:.2f} | {insight.anomaly_type or 'normal':15} | {len(theme_obs)} observations")

    return insights


# ============================================================================
# Phase 5: Self-Evolution (Accuracy Measurement & Policy Refinement)
# ============================================================================

def phase_5_self_evolution(insights: List[Insight]) -> PolicyMetrics:
    """Phase 5: Measure accuracy and propose policy refinements"""
    logger.info("[PHASE 5] Self-Evolution: accuracy measurement & policy refinement")

    # Simulate historical verdict analysis
    total_verdicts = random.randint(100, 500)
    correct_verdicts = int(total_verdicts * random.uniform(0.75, 0.95))
    accuracy = round(correct_verdicts / total_verdicts, 3)

    false_positives = random.randint(1, 10)
    false_negatives = random.randint(1, 10)
    total_positive_calls = random.randint(50, 200)
    total_negative_calls = random.randint(50, 200)

    fp_rate = round(false_positives / (total_positive_calls + false_positives), 3) if (total_positive_calls + false_positives) > 0 else 0.0
    fn_rate = round(false_negatives / (total_negative_calls + false_negatives), 3) if (total_negative_calls + false_negatives) > 0 else 0.0

    metrics = PolicyMetrics(
        accuracy=accuracy,
        false_positive_rate=fp_rate,
        false_negative_rate=fn_rate,
        decision_transitions={
            "ACCEPT→REJECT": random.randint(0, 5),
            "REJECT→ACCEPT": random.randint(0, 8)
        },
        verdicts_analyzed=total_verdicts,
        timestamp=datetime.now().isoformat()
    )

    logger.info(f"  → Accuracy: {metrics.accuracy:.1%}")
    logger.info(f"  → False positive rate: {metrics.false_positive_rate:.1%}")
    logger.info(f"  → False negative rate: {metrics.false_negative_rate:.1%}")
    logger.info(f"  → Verdicts analyzed: {metrics.verdicts_analyzed}")

    # Propose policy adjustment if accuracy declined
    if metrics.accuracy < 0.85:
        logger.info(f"  ⚠ POLICY RECOMMENDATION: Adjust thresholds (accuracy below 85%)")
    elif metrics.accuracy > 0.92:
        logger.info(f"  ✓ POLICY STABLE: High accuracy maintained")

    return metrics


# ============================================================================
# Phase 6: Interactive Explorer (Query Interface — Simulated)
# ============================================================================

def phase_6_interactive_explorer(insights: List[Insight], verdicts: List[Verdict]) -> Dict[str, Any]:
    """Phase 6: Simulate interactive queries"""
    logger.info("[PHASE 6] Interactive Explorer: simulating queries")

    sample_queries = [
        "What security issues were detected last week?",
        "Show me all rejected claims",
        "Find high-confidence insights",
        "List anomalies by type",
        "Compare today's verdicts with last Monday",
    ]

    query = random.choice(sample_queries)
    logger.info(f"  → Query: '{query}'")

    # Simulate query results
    matching_insights = random.sample(insights, min(3, len(insights)))
    matching_verdicts = random.sample(verdicts, min(3, len(verdicts)))

    logger.info(f"  → Found {len(matching_insights)} insights, {len(matching_verdicts)} verdicts")

    return {
        "query": query,
        "matching_insights": len(matching_insights),
        "matching_verdicts": len(matching_verdicts),
        "response_time_ms": round(random.uniform(10, 100), 1)
    }


# ============================================================================
# Phase 7: Scenario Simulator (Policy Impact Analysis)
# ============================================================================

def phase_7_scenario_simulator(verdicts: List[Verdict]) -> Dict[str, Any]:
    """Phase 7: Test proposed policy changes"""
    logger.info("[PHASE 7] Scenario Simulator: policy impact analysis")

    if not verdicts:
        logger.warning("  → No verdicts to simulate against")
        return {"status": "insufficient_data"}

    # Simulate replay with new policy
    changed_verdicts = random.randint(0, min(5, len(verdicts)))
    change_rate = round(changed_verdicts / len(verdicts), 3) if verdicts else 0.0

    accept_to_reject = random.randint(0, changed_verdicts)
    reject_to_accept = changed_verdicts - accept_to_reject

    old_accuracy = round(random.uniform(0.80, 0.95), 3)
    new_accuracy = round(old_accuracy + random.uniform(-0.05, 0.08), 3)
    accuracy_delta = round(new_accuracy - old_accuracy, 3)

    # Risk assessment
    if change_rate > 0.10 or accuracy_delta < -0.05:
        risk_level = "HIGH"
        recommendation = "DO_NOT_APPLY"
    elif change_rate > 0.05 or accuracy_delta < -0.02:
        risk_level = "MEDIUM"
        recommendation = "HOLD"
    else:
        risk_level = "LOW"
        recommendation = "APPLY"

    result = {
        "verdicts_replayed": len(verdicts),
        "verdicts_changed": changed_verdicts,
        "change_rate": change_rate,
        "accept_to_reject": accept_to_reject,
        "reject_to_accept": reject_to_accept,
        "old_accuracy": old_accuracy,
        "new_accuracy": new_accuracy,
        "accuracy_delta": accuracy_delta,
        "risk_level": risk_level,
        "recommendation": recommendation
    }

    logger.info(f"  → Verdicts replayed: {result['verdicts_replayed']}")
    logger.info(f"  → Decision transitions: {accept_to_reject} ACCEPT→REJECT, {reject_to_accept} REJECT→ACCEPT")
    logger.info(f"  → Accuracy: {old_accuracy:.1%} → {new_accuracy:.1%} (delta: {accuracy_delta:+.1%})")
    logger.info(f"  → Risk level: {risk_level}")
    logger.info(f"  → Recommendation: {recommendation}")

    return result


# ============================================================================
# Phase 8: Dashboard (Metrics & Monitoring)
# ============================================================================

def phase_8_dashboard(
    observations: List[Observation],
    insights: List[Insight],
    verdicts: List[Verdict],
    metrics: PolicyMetrics
) -> Dict[str, Any]:
    """Phase 8: Aggregate and display dashboard metrics"""
    logger.info("[PHASE 8] Dashboard: real-time metrics aggregation")

    avg_priority = round(sum(obs.priority for obs in observations) / len(observations), 2) if observations else 0

    dashboard = {
        "timestamp": datetime.now().isoformat(),
        "observations": {
            "total": len(observations),
            "by_source": {},
            "avg_priority": avg_priority
        },
        "insights": {
            "total": len(insights),
            "high_confidence": len([i for i in insights if i.confidence > 0.85]),
            "anomalies_detected": len([i for i in insights if i.anomaly_type])
        },
        "verdicts": {
            "total": len(verdicts),
            "accepted": len([v for v in verdicts if v.decision == "ACCEPT"]),
            "rejected": len([v for v in verdicts if v.decision == "REJECT"])
        },
        "policy": {
            "accuracy": metrics.accuracy,
            "fp_rate": metrics.false_positive_rate,
            "fn_rate": metrics.false_negative_rate
        }
    }

    # Count by source
    for source in ObservationType:
        count = len([obs for obs in observations if obs.source == source])
        if count > 0:
            dashboard["observations"]["by_source"][source.value] = count

    logger.info(f"  → Total observations: {dashboard['observations']['total']}")
    logger.info(f"  → Total insights: {dashboard['insights']['total']}")
    logger.info(f"  → Total verdicts: {dashboard['verdicts']['total']}")
    logger.info(f"  → Policy accuracy: {dashboard['policy']['accuracy']:.1%}")

    return dashboard


# ============================================================================
# Integration: Full Cycle Runner
# ============================================================================

def run_full_cycle(mode: str = "demo", verbose: bool = False) -> Dict[str, Any]:
    """Run complete autonomous OS emulation cycle"""
    logger.info("=" * 80)
    logger.info("ORACLE TOWN AUTONOMOUS OS EMULATION")
    logger.info(f"Mode: {mode.upper()} | Start: {datetime.now().isoformat()}")
    logger.info("=" * 80)

    cycle_results = {
        "mode": mode,
        "start_time": datetime.now().isoformat(),
        "phases": {}
    }

    # Phase 1: Observation Collection
    observations = phase_1_observation_collector(count=5 if mode == "demo" else 10)
    cycle_results["phases"]["1_observation_collector"] = {
        "observations": len(observations),
        "timestamp": datetime.now().isoformat()
    }

    # Phase 2: Memory Linker
    memory_info = phase_2_memory_linker(observations)
    cycle_results["phases"]["2_memory_linker"] = memory_info

    # Phase 3: OS Runner
    scheduler_info = phase_3_os_runner(mode)
    cycle_results["phases"]["3_os_runner"] = scheduler_info

    # Phase 4: Insight Engine
    insights = phase_4_insight_engine(observations)
    cycle_results["phases"]["4_insight_engine"] = {
        "insights": len(insights),
        "anomalies": len([i for i in insights if i.anomaly_type]),
        "timestamp": datetime.now().isoformat()
    }

    # Phase 5: Self-Evolution
    metrics = phase_5_self_evolution(insights)
    cycle_results["phases"]["5_self_evolution"] = metrics.to_dict()

    # Simulate some verdicts for later phases
    verdicts = []
    for insight in insights:
        verdict = Verdict(
            id=f"vrd_{hashlib.sha256(f'{insight.id}:{time.time()}'.encode()).hexdigest()[:12]}",
            insight_ids=[insight.id],
            decision=random.choice(["ACCEPT", "REJECT"]),
            confidence=round(random.uniform(0.75, 0.99), 3),
            reasoning=f"Based on {len(insight.observation_ids)} observations",
            policy_version="v1.2.0",
            timestamp=datetime.now().isoformat(),
            gate_results={
                "K0": "PASS",
                "K1": "PASS",
                "K2": "PASS",
                "K5": "PASS",
                "K7": "PASS"
            }
        )
        verdicts.append(verdict)

    # Phase 6: Interactive Explorer
    if mode == "demo":
        explorer_info = phase_6_interactive_explorer(insights, verdicts)
        cycle_results["phases"]["6_interactive_explorer"] = explorer_info

    # Phase 7: Scenario Simulator
    if mode == "demo":
        scenario_info = phase_7_scenario_simulator(verdicts)
        cycle_results["phases"]["7_scenario_simulator"] = scenario_info

    # Phase 8: Dashboard
    dashboard = phase_8_dashboard(observations, insights, verdicts, metrics)
    cycle_results["phases"]["8_dashboard"] = dashboard

    # Finalize
    cycle_results["end_time"] = datetime.now().isoformat()
    cycle_results["status"] = "complete"

    logger.info("=" * 80)
    logger.info("CYCLE COMPLETE")
    logger.info("=" * 80)

    return cycle_results


# ============================================================================
# Main: CLI Interface
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="ORACLE TOWN Autonomous OS Emulation"
    )
    parser.add_argument(
        "--mode",
        choices=["demo", "24h", "5min"],
        default="demo",
        help="Emulation mode: demo (single cycle), 24h (24-hour schedule), 5min (5-minute cycle)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    logger.info(f"Emulation directory: {EMULATION_DIR}")

    if args.mode == "demo":
        # Single demonstration cycle
        results = run_full_cycle(mode="demo", verbose=args.verbose)
        output_file = EMULATION_DIR / "emulation_results.json"
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to: {output_file}")

    elif args.mode == "24h":
        # Simulate 24-hour cycle with 3 runs (09:00, 15:00, 21:00)
        logger.info("Running 24-hour cycle simulation (3 runs)...")
        all_results = []
        for i, hour in enumerate([9, 15, 21]):
            logger.info(f"\n--- Run {i+1}/3 at {hour:02d}:00 ---")
            results = run_full_cycle(mode="daily", verbose=args.verbose)
            all_results.append(results)
            if i < 2:
                time.sleep(1)  # Brief pause between runs

        output_file = EMULATION_DIR / "emulation_24h_results.json"
        with open(output_file, "w") as f:
            json.dump(all_results, f, indent=2)
        logger.info(f"\n24h results saved to: {output_file}")

    elif args.mode == "5min":
        # Simulate 5-minute continuous cycle (10 iterations)
        logger.info("Running 5-minute cycle simulation (10 iterations)...")
        all_results = []
        for i in range(10):
            logger.info(f"\n--- Iteration {i+1}/10 ---")
            results = run_full_cycle(mode="continuous", verbose=args.verbose)
            all_results.append(results)
            if i < 9:
                logger.info("Waiting 1 second before next iteration...")
                time.sleep(1)

        output_file = EMULATION_DIR / "emulation_5min_results.json"
        with open(output_file, "w") as f:
            json.dump(all_results, f, indent=2)
        logger.info(f"\n5min results saved to: {output_file}")

    logger.info(f"\n✓ Emulation complete. All files in: {EMULATION_DIR}")


if __name__ == "__main__":
    main()
