#!/usr/bin/env python3
"""
Oracle Town Observation Collector

Ingests observations from multiple sources and converts them to claims
for analysis by the kernel.

Sources:
1. Email (IMAP) — Auto-summarize top unread emails
2. Meeting notes (JSON) — Structured fact extraction
3. Metrics/KPIs (JSON) — Daily snapshot ingestion
4. Manual observations (CLI) — Direct typed input
5. Incident reports (JSON) — Structured problem description

Output: Structured claims ready for kernel analysis.

Architecture:
- Modular source handlers
- Deterministic claim generation (same input → same claim)
- Observation provenance tracking (source recorded)
- Immutable claim storage
"""

import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod


@dataclass
class Observation:
    """Raw observation from any source."""
    source: str  # email, meeting, metric, manual, incident
    timestamp: str
    content: str
    metadata: Dict[str, Any]


@dataclass
class Claim:
    """Structured claim for kernel analysis."""
    claim_id: str
    timestamp: str
    observation_source: str
    domain: str  # vendor, technical, business, security, opportunity
    content: str
    severity: str  # low, medium, high
    suggested_action: Optional[str]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict:
        return asdict(self)


class ObservationSource(ABC):
    """Base class for observation sources."""

    @abstractmethod
    def fetch(self) -> List[Observation]:
        """Fetch observations from source."""
        pass


class EmailObserver(ObservationSource):
    """Fetch observations from email (IMAP)."""

    def __init__(self, imap_host: str = None, username: str = None, password: str = None):
        self.imap_host = imap_host or "imap.gmail.com"
        self.username = username
        self.password = password
        # Note: In production, use keyring or environment variables for credentials

    def fetch(self) -> List[Observation]:
        """Fetch recent unread emails."""
        observations = []

        # Placeholder: Actual IMAP implementation would go here
        # This requires `imap_tools` or similar library
        # For now, return empty list or mock data

        # Example mock observation:
        observations.append(Observation(
            source="email",
            timestamp=datetime.utcnow().isoformat() + "Z",
            content="Vendor request for API access approval",
            metadata={
                "from": "vendor@example.com",
                "subject": "API Key Request - Q1 Integration",
                "unread": True,
            }
        ))

        return observations


class MeetingNotesObserver(ObservationSource):
    """Parse meeting notes (JSON format)."""

    def __init__(self, notes_file: str = None):
        self.notes_file = Path(notes_file or "meeting_notes.json")

    def fetch(self) -> List[Observation]:
        """Parse structured meeting notes."""
        observations = []

        if not self.notes_file.exists():
            return observations

        try:
            with open(self.notes_file) as f:
                notes = json.load(f)

            # Extract observations from notes
            for note in notes:
                if "date" not in note:
                    continue

                for obs in note.get("observations", []):
                    observations.append(Observation(
                        source="meeting",
                        timestamp=note.get("date", ""),
                        content=obs,
                        metadata={
                            "meeting": note.get("title", ""),
                            "attendees": note.get("attendees", []),
                        }
                    ))
        except Exception as e:
            print(f"Error parsing meeting notes: {e}")

        return observations


class MetricsObserver(ObservationSource):
    """Ingest KPI snapshots and metrics."""

    def __init__(self, metrics_file: str = None):
        self.metrics_file = Path(metrics_file or "metrics.json")

    def fetch(self) -> List[Observation]:
        """Load daily metrics snapshot."""
        observations = []

        if not self.metrics_file.exists():
            return observations

        try:
            with open(self.metrics_file) as f:
                metrics = json.load(f)

            # Convert metrics to observations
            for metric_name, metric_value in metrics.items():
                observations.append(Observation(
                    source="metric",
                    timestamp=datetime.utcnow().isoformat() + "Z",
                    content=f"{metric_name}: {metric_value}",
                    metadata={
                        "metric_name": metric_name,
                        "value": metric_value,
                    }
                ))

            # Detect anomalies in metrics
            for metric_name, metric_value in metrics.items():
                if isinstance(metric_value, (int, float)):
                    # Example: Flag if metric > 1000
                    if metric_value > 1000:
                        observations.append(Observation(
                            source="metric_anomaly",
                            timestamp=datetime.utcnow().isoformat() + "Z",
                            content=f"Anomaly detected: {metric_name} = {metric_value} (high)",
                            metadata={
                                "metric_name": metric_name,
                                "value": metric_value,
                                "anomaly": "high_value",
                            }
                        ))

        except Exception as e:
            print(f"Error parsing metrics: {e}")

        return observations


class IncidentObserver(ObservationSource):
    """Parse incident reports."""

    def __init__(self, incidents_file: str = None):
        self.incidents_file = Path(incidents_file or "incidents.json")

    def fetch(self) -> List[Observation]:
        """Load incident reports."""
        observations = []

        if not self.incidents_file.exists():
            return observations

        try:
            with open(self.incidents_file) as f:
                incidents = json.load(f)

            for incident in incidents:
                observations.append(Observation(
                    source="incident",
                    timestamp=incident.get("timestamp", ""),
                    content=incident.get("description", ""),
                    metadata={
                        "incident_id": incident.get("id", ""),
                        "severity": incident.get("severity", "medium"),
                        "component": incident.get("component", ""),
                    }
                ))

        except Exception as e:
            print(f"Error parsing incidents: {e}")

        return observations


class ManualObserver(ObservationSource):
    """Accept manually-typed observations."""

    def __init__(self):
        self.observations = []

    def add(self, content: str, metadata: Dict = None):
        """Add a manual observation."""
        self.observations.append(Observation(
            source="manual",
            timestamp=datetime.utcnow().isoformat() + "Z",
            content=content,
            metadata=metadata or {}
        ))

    def fetch(self) -> List[Observation]:
        """Return all manual observations."""
        result = self.observations
        self.observations = []  # Clear for next fetch
        return result


class ObservationCompiler:
    """Convert observations to claims."""

    def __init__(self):
        self.claims = []

    def compile(self, observations: List[Observation]) -> List[Claim]:
        """Convert observations to claims."""
        claims = []

        for obs in observations:
            # Classify domain
            domain = self._classify_domain(obs.content)

            # Extract severity
            severity = self._extract_severity(obs.metadata)

            # Generate claim ID deterministically
            claim_id = self._generate_claim_id(obs)

            # Suggest action
            suggested_action = self._suggest_action(domain, obs.content)

            claim = Claim(
                claim_id=claim_id,
                timestamp=obs.timestamp,
                observation_source=obs.source,
                domain=domain,
                content=obs.content,
                severity=severity,
                suggested_action=suggested_action,
                metadata=obs.metadata,
            )

            claims.append(claim)

        self.claims.extend(claims)
        return claims

    def _generate_claim_id(self, obs: Observation) -> str:
        """Generate deterministic claim ID."""
        content_hash = hashlib.sha256(obs.content.encode()).hexdigest()[:12]
        timestamp = obs.timestamp.replace("-", "").replace(":", "").replace("T", "").replace("Z", "")
        return f"claim_{timestamp}_{content_hash}"

    def _classify_domain(self, content: str) -> str:
        """Classify observation domain."""
        content_lower = content.lower()

        keywords = {
            "vendor": ["vendor", "third-party", "partner", "supplier", "api", "integration"],
            "technical": ["performance", "latency", "cpu", "memory", "error", "crash", "bug", "regression"],
            "business": ["revenue", "cost", "budget", "timeline", "roadmap", "feature", "capacity"],
            "security": ["security", "breach", "vulnerability", "attack", "malware", "credential", "access"],
            "opportunity": ["opportunity", "improvement", "optimization", "efficiency", "growth"],
        }

        for domain, kwords in keywords.items():
            if any(kw in content_lower for kw in kwords):
                return domain

        return "technical"  # Default

    def _extract_severity(self, metadata: Dict) -> str:
        """Extract severity from metadata."""
        # Check explicit severity field
        if "severity" in metadata:
            return metadata["severity"]

        # Infer from source
        source = metadata.get("source", "")
        if "incident" in source:
            return "high"
        elif "metric_anomaly" in source:
            return "medium"
        else:
            return "low"

    def _suggest_action(self, domain: str, content: str) -> Optional[str]:
        """Suggest action based on domain."""
        actions = {
            "vendor": "Review vendor policy and approval thresholds",
            "technical": "File technical investigation ticket",
            "business": "Schedule stakeholder alignment meeting",
            "security": "Escalate to security team immediately",
            "opportunity": "Add to roadmap discussion",
        }
        return actions.get(domain, None)

    def save_claims(self, output_file: str = None) -> str:
        """Save claims to file."""
        output_path = Path(output_file or "claims.jsonl")

        with open(output_path, 'a') as f:
            for claim in self.claims:
                f.write(json.dumps(claim.to_dict(), sort_keys=True) + "\n")

        return str(output_path)


class ObservationCollectorService:
    """Orchestrate observation collection and compilation."""

    def __init__(self):
        self.sources: List[ObservationSource] = []
        self.compiler = ObservationCompiler()

    def add_source(self, source: ObservationSource) -> None:
        """Register an observation source."""
        self.sources.append(source)

    def collect_and_compile(self) -> List[Claim]:
        """Collect from all sources and compile to claims."""
        all_observations = []

        for source in self.sources:
            try:
                observations = source.fetch()
                all_observations.extend(observations)
            except Exception as e:
                print(f"Error fetching from {source.__class__.__name__}: {e}")

        # Compile to claims
        claims = self.compiler.compile(all_observations)

        # Save claims
        self.compiler.save_claims()

        return claims


def main():
    """Example: Collect observations and compile claims."""
    service = ObservationCollectorService()

    # Register sources
    service.add_source(EmailObserver())
    service.add_source(MeetingNotesObserver())
    service.add_source(MetricsObserver())
    service.add_source(ManualObserver())

    # Collect and compile
    claims = service.collect_and_compile()

    print(f"\n📝 Observation Collector\n")
    print(f"Collected {len(claims)} claims\n")

    for claim in claims[:5]:
        print(f"[{claim.severity.upper()}] {claim.domain}: {claim.content[:60]}")
        if claim.suggested_action:
            print(f"  → {claim.suggested_action}")

    if len(claims) > 5:
        print(f"... and {len(claims) - 5} more")


if __name__ == "__main__":
    main()
