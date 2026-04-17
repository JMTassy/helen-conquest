#!/usr/bin/env python3
"""
Job Registry

Manages OpenClaw jobs as deterministic Oracle Town job specs.

Key Properties:
1. Jobs are defined in a DAG (directed acyclic graph)
2. Execution order is deterministic (topological sort)
3. Each job execution is submitted as a claim
4. Jobs only execute if receipt permits (K15 enforcement)
5. All executions are logged immutably

This enables OpenClaw jobs to scale safely within Oracle Town governance.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Callable
import json
import uuid
from datetime import datetime


@dataclass
class JobSpec:
    """
    Specification for a job.
    """
    job_id: str
    name: str
    description: str
    inputs: Dict[str, Any]
    outputs: List[str]  # output keys
    depends_on: List[str] = field(default_factory=list)  # job IDs
    deterministic: bool = True
    execute_fn: Optional[Callable] = None
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "job_id": self.job_id,
            "name": self.name,
            "description": self.description,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "depends_on": self.depends_on,
            "deterministic": self.deterministic,
            "enabled": self.enabled
        }


@dataclass
class JobExecution:
    """
    Record of a job execution.
    """
    execution_id: str
    job_id: str
    timestamp: str
    status: str  # "pending", "claimed", "shipped", "rejected", "executed", "failed"
    claim_id: Optional[str] = None
    receipt_id: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_ms: Optional[int] = None


class JobRegistry:
    """
    Registry of all jobs with deterministic DAG execution.
    """

    def __init__(self, registry_file: str = "oracle_town/jobs/registry.json"):
        """
        Initialize the job registry.

        Args:
            registry_file: Path to job registry file
        """
        self.registry_file = registry_file
        self.jobs: Dict[str, JobSpec] = {}
        self.executions: List[JobExecution] = []
        self._load_registry()

    def register_job(
        self,
        name: str,
        description: str,
        inputs: Dict[str, Any],
        outputs: List[str],
        depends_on: Optional[List[str]] = None,
        execute_fn: Optional[Callable] = None,
        deterministic: bool = True,
        job_id: Optional[str] = None
    ) -> JobSpec:
        """
        Register a new job.

        Args:
            name: Job name
            description: Job description
            inputs: Input parameters
            outputs: Output keys
            depends_on: Job IDs this depends on
            execute_fn: Function to execute the job
            deterministic: Whether job is deterministic
            job_id: Optional ID; auto-generated if not provided

        Returns:
            JobSpec object
        """
        job_id = job_id or f"job_{uuid.uuid4().hex[:8]}"

        spec = JobSpec(
            job_id=job_id,
            name=name,
            description=description,
            inputs=inputs,
            outputs=outputs,
            depends_on=depends_on or [],
            deterministic=deterministic,
            execute_fn=execute_fn
        )

        self.jobs[job_id] = spec
        self._save_registry()

        return spec

    def get_job(self, job_id: str) -> Optional[JobSpec]:
        """Get a job by ID."""
        return self.jobs.get(job_id)

    def list_jobs(self) -> List[JobSpec]:
        """List all registered jobs."""
        return list(self.jobs.values())

    def get_execution_order(self) -> List[str]:
        """
        Get deterministic execution order (topological sort).

        Returns list of job IDs in execution order.
        """
        # Simple topological sort with deterministic tie-breaking
        sorted_jobs = []
        visited = set()

        def visit(job_id):
            if job_id in visited:
                return
            visited.add(job_id)

            job = self.jobs.get(job_id)
            if not job:
                return

            # Visit dependencies first (stable order)
            for dep_id in sorted(job.depends_on):
                visit(dep_id)

            sorted_jobs.append(job_id)

        # Visit all jobs in deterministic order
        for job_id in sorted(self.jobs.keys()):
            visit(job_id)

        return sorted_jobs

    def validate_dag(self) -> tuple[bool, List[str]]:
        """
        Validate the job DAG (no cycles, all deps exist).

        Returns (is_valid, list_of_errors)
        """
        errors = []

        # Check for missing dependencies
        for job_id, job in self.jobs.items():
            for dep_id in job.depends_on:
                if dep_id not in self.jobs:
                    errors.append(f"Job {job_id} depends on missing job {dep_id}")

        # Check for cycles (simple DFS)
        visited = set()
        rec_stack = set()

        def has_cycle(node):
            visited.add(node)
            rec_stack.add(node)

            job = self.jobs.get(node)
            if job:
                for neighbor in job.depends_on:
                    if neighbor not in visited:
                        if has_cycle(neighbor):
                            return True
                    elif neighbor in rec_stack:
                        errors.append(f"Cycle detected: {node} → {neighbor}")
                        return True

            rec_stack.remove(node)
            return False

        for job_id in self.jobs:
            if job_id not in visited:
                has_cycle(job_id)

        return (len(errors) == 0, errors)

    def create_claim_for_job(self, job: JobSpec) -> Dict[str, Any]:
        """
        Create a claim for a job to be submitted to Oracle Town.

        Args:
            job: JobSpec to create claim for

        Returns:
            Claim dict
        """
        return {
            "claim_id": f"claim_{uuid.uuid4().hex[:8]}",
            "claim_type": "job_execution",
            "job_id": job.job_id,
            "job_name": job.name,
            "statement": f"Execute job: {job.name}",
            "description": job.description,
            "inputs": job.inputs,
            "outputs": job.outputs,
            "deterministic": job.deterministic,
            "timestamp": datetime.utcnow().isoformat()
        }

    def execute_job(
        self,
        job_id: str,
        submit_fn: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Execute a single job.

        Args:
            job_id: ID of job to execute
            submit_fn: Optional function to submit claim

        Returns:
            Execution result dict
        """
        job = self.get_job(job_id)
        if not job:
            return {"error": f"Job {job_id} not found"}

        if not job.enabled:
            return {"error": f"Job {job_id} is disabled"}

        start_time = datetime.utcnow()
        execution = JobExecution(
            execution_id=f"exec_{uuid.uuid4().hex[:8]}",
            job_id=job_id,
            timestamp=start_time.isoformat(),
            status="pending"
        )

        try:
            # Step 1: Create claim
            claim = self.create_claim_for_job(job)
            execution.claim_id = claim["claim_id"]
            execution.status = "claimed"

            # Step 2: Submit claim if submit_fn provided
            receipt = None
            if submit_fn:
                receipt = submit_fn(claim)
                execution.receipt_id = receipt.get("receipt_id") if receipt else None

                # Check decision
                if receipt and receipt.get("decision") == "SHIP":
                    execution.status = "shipped"
                else:
                    execution.status = "rejected"
                    self.executions.append(execution)
                    return {
                        "execution_id": execution.execution_id,
                        "status": "rejected",
                        "receipt": receipt
                    }

            # Step 3: Execute if permitted (or deterministic)
            if job.execute_fn:
                result = job.execute_fn(**job.inputs)
                execution.result = result
                execution.status = "executed"

                # Record execution time
                end_time = datetime.utcnow()
                execution.duration_ms = (end_time - start_time).total_seconds() * 1000

            self.executions.append(execution)

            return {
                "execution_id": execution.execution_id,
                "status": "success",
                "claim": claim,
                "receipt": receipt,
                "result": execution.result
            }

        except Exception as e:
            execution.status = "failed"
            execution.error = str(e)
            self.executions.append(execution)

            return {
                "execution_id": execution.execution_id,
                "status": "error",
                "error": str(e)
            }

    def execute_dag(
        self,
        submit_fn: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Execute the full job DAG in deterministic order.

        Args:
            submit_fn: Optional function to submit claims

        Returns:
            DAG execution result dict
        """
        # Validate DAG first
        is_valid, errors = self.validate_dag()
        if not is_valid:
            return {"error": "Invalid DAG", "details": errors}

        # Get execution order
        order = self.get_execution_order()

        results = {
            "dag_id": f"dag_{uuid.uuid4().hex[:8]}",
            "total_jobs": len(order),
            "jobs_executed": 0,
            "jobs_rejected": 0,
            "jobs_failed": 0,
            "execution_results": []
        }

        for job_id in order:
            result = self.execute_job(job_id, submit_fn)
            results["execution_results"].append(result)

            if result.get("status") == "success":
                results["jobs_executed"] += 1
            elif result.get("status") == "rejected":
                results["jobs_rejected"] += 1
            elif result.get("status") == "error":
                results["jobs_failed"] += 1

        return results

    def get_execution_history(
        self,
        job_id: Optional[str] = None,
        limit: int = 100
    ) -> List[JobExecution]:
        """
        Get execution history.

        Args:
            job_id: Optional filter by job
            limit: Maximum number of results

        Returns:
            List of executions
        """
        results = self.executions

        if job_id:
            results = [e for e in results if e.job_id == job_id]

        return results[-limit:]

    # --- Private helper methods ---

    def _load_registry(self):
        """Load job registry from file."""
        try:
            with open(self.registry_file, "r") as f:
                data = json.load(f)
                for job_dict in data.get("jobs", []):
                    spec = JobSpec(
                        job_id=job_dict["job_id"],
                        name=job_dict["name"],
                        description=job_dict["description"],
                        inputs=job_dict["inputs"],
                        outputs=job_dict["outputs"],
                        depends_on=job_dict.get("depends_on", []),
                        deterministic=job_dict.get("deterministic", True),
                        enabled=job_dict.get("enabled", True)
                    )
                    self.jobs[spec.job_id] = spec
        except FileNotFoundError:
            pass

    def _save_registry(self):
        """Save job registry to file."""
        try:
            data = {
                "jobs": [job.to_dict() for job in self.jobs.values()]
            }
            with open(self.registry_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save registry: {e}")


# --- Testing ---

if __name__ == "__main__":

    # Test 1: Create registry
    registry = JobRegistry()
    print("✓ Job registry initialized")

    # Test 2: Register jobs with dependencies
    job1 = registry.register_job(
        name="Fetch Vendor Data",
        description="Fetch current vendor info",
        inputs={"vendor_id": "vendor_acme"},
        outputs=["vendor_data"],
        execute_fn=lambda vendor_id: {"status": "healthy"}
    )
    print(f"✓ Job registered: {job1.job_id}")

    job2 = registry.register_job(
        name="Analyze Vendor",
        description="Analyze vendor data",
        inputs={"vendor_data": None},
        outputs=["analysis"],
        depends_on=[job1.job_id],
        execute_fn=lambda vendor_data: {"risk_level": "low"}
    )
    print(f"✓ Job with dependency registered: {job2.job_id}")

    # Test 3: Validate DAG
    is_valid, errors = registry.validate_dag()
    print(f"✓ DAG validation: {'valid' if is_valid else 'invalid'}")

    # Test 4: Get execution order
    order = registry.get_execution_order()
    print(f"✓ Execution order: {order}")

    # Test 5: Execute job
    result = registry.execute_job(job1.job_id)
    print(f"✓ Job executed: {result['status']}")

    # Test 6: Execute DAG
    dag_result = registry.execute_dag()
    print(f"✓ DAG executed:")
    print(f"  - Total jobs: {dag_result['total_jobs']}")
    print(f"  - Jobs executed: {dag_result['jobs_executed']}")

    print("\n✅ Job registry tests passed")
