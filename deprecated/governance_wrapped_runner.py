#!/usr/bin/env python3
"""
ChatDev 2.0 + Oracle Town Integration Runner

Execute a governance-wrapped ChatDev workflow end-to-end:
1. Execute Creative Town Super Team workflow (6 lateral thinking agents)
2. Route outputs through Oracle Town governance gates
3. Extract claims with risk metadata
4. Submit to Oracle Intake

Usage:
    python governance_wrapped_runner.py --yaml governance_wrapped_lateral_thinking.yaml \
        --prompt "Analyze: Why do auth proposals face rejection?" \
        --output-dir ./results
"""

import json
import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GovernanceWrappedRunner:
    """Execute ChatDev workflows with Oracle Town governance."""
    
    def __init__(self, yaml_file: str, output_dir: str = "./results"):
        self.yaml_file = yaml_file
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.workflow_id = f"workflow_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"Initialized runner. Workflow ID: {self.workflow_id}")
    
    def execute_workflow(self, task_prompt: str) -> Dict[str, Any]:
        """
        Execute ChatDev workflow.
        
        In production: from runtime.sdk import run_workflow
                       result = run_workflow(yaml_file=self.yaml_file, ...)
        """
        logger.info(f"Executing workflow: {self.yaml_file}")
        logger.info(f"Task: {task_prompt}")
        
        # Mock result (in production, from ChatDev runtime)
        result = {
            "workflow_id": self.workflow_id,
            "status": "completed",
            "task_prompt": task_prompt,
            "node_outputs": {
                "dan_lateral_agent": [
                    {
                        "idea": "Accept ambiguous-intent proposals in probationary status",
                        "reasoning": "Inverts auto-reject: create staging category for exploration",
                        "risk_flags": ["boundary_probe"]
                    }
                ],
                "librarian_synth_agent": [
                    {
                        "domain": "immunology",
                        "analogy": "Immune system accepts novel antigens after tolerance period",
                        "application": "Probationary acceptance with escalating scrutiny",
                        "confidence": 0.82
                    }
                ],
                "poet_metaphor_agent": [
                    {
                        "metaphor": "Ledger as garden; ambiguous proposals as seeds",
                        "reveals": "Rejection conflates unclear with dangerous—orthogonal",
                        "poetic_risk": "provocative"
                    }
                ],
                "hacker_sandbox_agent": [
                    {
                        "edge_case": "Probationary proposals never graduate",
                        "breaks_assumption": "Assumes eventual resolution",
                        "corrective_insight": "Need time bounds or escalation"
                    }
                ],
                "sage_dialectic_agent": [
                    {
                        "thesis": "All proposals meet clarity standard before acceptance",
                        "antithesis": "Clarity emerges through implementation",
                        "synthesis": "Two-track: fast high-clarity + slow probationary",
                        "category": "operational"
                    }
                ],
                "dreamer_absurd_agent": [
                    {
                        "absurd_idea": "Ledger itself rejects proposals it finds too clear",
                        "why_impossible": "Ledger is passive, not agential",
                        "kernel_of_truth": "Ledger structure IS implicitly agential",
                        "creative_direction": "Make ledger structure more explicitly agential?"
                    }
                ]
            },
            "artifacts": {
                "audit_logger_output": {
                    "ledger_location": "artifacts/audit_ledger.jsonl",
                    "audit_id": f"audit_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
                }
            }
        }
        
        logger.info(f"Workflow completed. Status: {result['status']}")
        return result
    
    def extract_claims(self, workflow_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract governance-filtered claims from ALL 6 agents."""
        logger.info("Extracting claims from workflow output...")
        
        claims = []
        claim_counter = 1
        node_outputs = workflow_result.get("node_outputs", {})
        
        # DAN_Lateral → Claims
        for idea in node_outputs.get("dan_lateral_agent", []):
            claim = {
                "claim_id": f"CLM_{datetime.utcnow().strftime('%Y%m%d')}_{claim_counter:03d}",
                "content": idea.get("idea"),
                "source_agent": "DAN_Lateral",
                "claim_type": "divergent_idea",
                "risk_profile": {
                    "safe": True,
                    "tone_edginess": "provocative",
                    "violations": [],
                    "plausible_interpretation": True,
                    "risk_flags": idea.get("risk_flags", [])
                },
                "lineage": {
                    "reasoning_agent": "DAN_Lateral",
                    "prefilter_status": "passed",
                    "workflow_id": workflow_result["workflow_id"]
                }
            }
            claims.append(claim)
            claim_counter += 1
        
        # LIBRARIAN_Synth → Claims
        for idea in node_outputs.get("librarian_synth_agent", []):
            claim = {
                "claim_id": f"CLM_{datetime.utcnow().strftime('%Y%m%d')}_{claim_counter:03d}",
                "content": f"Pattern: {idea.get('analogy')} → {idea.get('application')}",
                "source_agent": "LIBRARIAN_Synth",
                "claim_type": "pattern_mapping",
                "metadata": {
                    "domain": idea.get("domain"),
                    "confidence": idea.get("confidence", 0),
                    "key_insight": idea.get("key_insight")
                },
                "risk_profile": {
                    "safe": True,
                    "tone_edginess": "safe",
                    "violations": [],
                    "plausible_interpretation": True
                },
                "lineage": {
                    "reasoning_agent": "LIBRARIAN_Synth",
                    "prefilter_status": "passed",
                    "workflow_id": workflow_result["workflow_id"]
                }
            }
            claims.append(claim)
            claim_counter += 1
        
        # POET_Metaphor → Claims
        for idea in node_outputs.get("poet_metaphor_agent", []):
            claim = {
                "claim_id": f"CLM_{datetime.utcnow().strftime('%Y%m%d')}_{claim_counter:03d}",
                "content": f"Metaphor: {idea.get('metaphor')} — Reveals: {idea.get('reveals')}",
                "source_agent": "POET_Metaphor",
                "claim_type": "metaphorical_insight",
                "metadata": {
                    "poetic_risk": idea.get("poetic_risk"),
                    "system_implication": idea.get("system_implication")
                },
                "risk_profile": {
                    "safe": True,
                    "tone_edginess": idea.get("poetic_risk", "safe"),
                    "violations": [],
                    "plausible_interpretation": True
                },
                "lineage": {
                    "reasoning_agent": "POET_Metaphor",
                    "prefilter_status": "passed",
                    "workflow_id": workflow_result["workflow_id"]
                }
            }
            claims.append(claim)
            claim_counter += 1
        
        # HACKER_Sandbox → Claims (Edge cases + vulnerabilities)
        for idea in node_outputs.get("hacker_sandbox_agent", []):
            claim = {
                "claim_id": f"CLM_{datetime.utcnow().strftime('%Y%m%d')}_{claim_counter:03d}",
                "content": f"Design vulnerability: {idea.get('edge_case')} — {idea.get('corrective_insight')}",
                "source_agent": "HACKER_Sandbox",
                "claim_type": "vulnerability_analysis",
                "metadata": {
                    "edge_case": idea.get("edge_case"),
                    "breaks_assumption": idea.get("breaks_assumption"),
                    "is_exploitable": idea.get("is_this_exploitable", False)
                },
                "risk_profile": {
                    "safe": True,
                    "tone_edginess": "safe",
                    "violations": [],
                    "plausible_interpretation": True
                },
                "lineage": {
                    "reasoning_agent": "HACKER_Sandbox",
                    "prefilter_status": "passed",
                    "workflow_id": workflow_result["workflow_id"]
                }
            }
            claims.append(claim)
            claim_counter += 1
        
        # SAGE_Dialectic → Claims (Synthesized resolutions)
        for idea in node_outputs.get("sage_dialectic_agent", []):
            claim = {
                "claim_id": f"CLM_{datetime.utcnow().strftime('%Y%m%d')}_{claim_counter:03d}",
                "content": f"Synthesis: {idea.get('synthesis')} (resolves: {idea.get('tension')})",
                "source_agent": "SAGE_Dialectic",
                "claim_type": "dialectical_synthesis",
                "metadata": {
                    "thesis": idea.get("thesis"),
                    "antithesis": idea.get("antithesis"),
                    "category": idea.get("category")
                },
                "risk_profile": {
                    "safe": True,
                    "tone_edginess": "safe",
                    "violations": [],
                    "plausible_interpretation": True
                },
                "lineage": {
                    "reasoning_agent": "SAGE_Dialectic",
                    "prefilter_status": "passed",
                    "workflow_id": workflow_result["workflow_id"]
                }
            }
            claims.append(claim)
            claim_counter += 1
        
        # DREAMER_Absurd → Claims (Meta-insights from absurdism)
        for idea in node_outputs.get("dreamer_absurd_agent", []):
            claim = {
                "claim_id": f"CLM_{datetime.utcnow().strftime('%Y%m%d')}_{claim_counter:03d}",
                "content": f"Meta-insight: {idea.get('kernel_of_truth')} → {idea.get('creative_direction')}",
                "source_agent": "DREAMER_Absurd",
                "claim_type": "absurdist_meta_insight",
                "metadata": {
                    "absurd_idea": idea.get("absurd_idea"),
                    "hidden_assumption": idea.get("hidden_assumption_it_violates")
                },
                "risk_profile": {
                    "safe": True,
                    "tone_edginess": "transgressive",
                    "violations": [],
                    "plausible_interpretation": True
                },
                "lineage": {
                    "reasoning_agent": "DREAMER_Absurd",
                    "prefilter_status": "passed",
                    "workflow_id": workflow_result["workflow_id"]
                }
            }
            claims.append(claim)
            claim_counter += 1
        
        logger.info(f"Extracted {len(claims)} claims from 6 agents")
        return claims
    
    def compile_claims(self, claims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Compile diverse claims into structured proposals."""
        logger.info(f"Compiling {len(claims)} claims into proposals...")
        
        proposals = []
        
        # Group claims by category
        categorized = {}
        for claim in claims:
            claim_type = claim.get("claim_type", "uncategorized")
            if claim_type not in categorized:
                categorized[claim_type] = []
            categorized[claim_type].append(claim)
        
        # Synthesize each category into a proposal
        proposal_id = 1
        for category, category_claims in categorized.items():
            # Create synthesis from related claims
            synthesis = " + ".join([
                f"{c['source_agent']}: {c['content'][:50]}"
                for c in category_claims[:3]  # Use top 3 from category
            ])
            
            proposal = {
                "proposal_id": f"PRO_{datetime.utcnow().strftime('%Y%m%d')}_{proposal_id:03d}",
                "category": category,
                "synthesis": synthesis,
                "source_claims": [c["claim_id"] for c in category_claims],
                "num_supporting_agents": len(set([c["source_agent"] for c in category_claims])),
                "compilation_timestamp": datetime.utcnow().isoformat()
            }
            proposals.append(proposal)
            proposal_id += 1
        
        logger.info(f"Compiled {len(claims)} claims into {len(proposals)} proposals")
        return proposals
    
    def validate_proposals(self, proposals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate proposals against Oracle Town hard rules."""
        logger.info(f"Validating {len(proposals)} proposals...")
        
        validated = {
            "total_proposals": len(proposals),
            "passed": [],
            "rejected": [],
            "validation_timestamp": datetime.utcnow().isoformat()
        }
        
        banned_phrases = [
            "jailbreak", "exploit", "bypass", "permission elevation",
            "compromise oracle", "override governance", "disable oversight"
        ]
        
        for proposal in proposals:
            content = proposal.get("synthesis", "").lower()
            rejected = False
            rejection_reasons = []
            
            # Check 1: Banned phrases (hard rule)
            for phrase in banned_phrases:
                if phrase in content:
                    rejected = True
                    rejection_reasons.append(f"Contains banned phrase: '{phrase}'")
            
            # Check 2: Propose authority escalation (hard rule)
            if "authority" in content and ("escalate" in content or "increase" in content):
                rejected = True
                rejection_reasons.append("Proposes authority escalation")
            
            # Check 3: Policy evasion attempts (hard rule)
            if "circumvent" in content or "bypass" in content or "workaround" in content:
                rejected = True
                rejection_reasons.append("Suggests policy evasion")
            
            if rejected:
                proposal["validation_status"] = "rejected"
                proposal["rejection_reasons"] = rejection_reasons
                validated["rejected"].append(proposal)
            else:
                proposal["validation_status"] = "passed"
                validated["passed"].append(proposal)
        
        logger.info(f"Validation: {len(validated['passed'])} passed, {len(validated['rejected'])} rejected")
        return validated

    def submit_claims_to_oracle(self, validated_proposals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Submit validated proposals to Oracle Town Intake."""
        logger.info(f"Submitting {len(validated_proposals)} validated proposals to Oracle Intake...")
        
        submission_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_submitted": len(validated_proposals),
            "accepted": 0,
            "proposals": []
        }
        
        for proposal in validated_proposals:
            result = {
                "proposal_id": proposal["proposal_id"],
                "status": "submitted",
                "oracle_verdict": "pending_review",
                "submitted_time": datetime.utcnow().isoformat(),
                "validation_status": proposal.get("validation_status", "passed")
            }
            submission_results["proposals"].append(result)
            submission_results["accepted"] += 1
        
        logger.info(f"Submission complete: {submission_results['accepted']} proposals to Oracle")
        return submission_results
    
    def save_results(self, results: Dict[str, Any]) -> None:
        """Save all pipeline artifacts."""
        
        # Workflow result
        workflow_file = self.output_dir / f"{self.workflow_id}_workflow.json"
        with open(workflow_file, "w") as f:
            json.dump(results["workflow"], f, indent=2)
        logger.info(f"Workflow result: {workflow_file}")
        
        # Claims
        claims_file = self.output_dir / f"{self.workflow_id}_claims.json"
        with open(claims_file, "w") as f:
            json.dump(results["claims"], f, indent=2)
        logger.info(f"Claims ({len(results['claims'])} from 6 agents): {claims_file}")
        
        # Proposals (compiled)
        proposals_file = self.output_dir / f"{self.workflow_id}_proposals.json"
        with open(proposals_file, "w") as f:
            json.dump(results["proposals"], f, indent=2)
        logger.info(f"Proposals (compiled): {proposals_file}")
        
        # Validation results
        validation_file = self.output_dir / f"{self.workflow_id}_validation.json"
        with open(validation_file, "w") as f:
            json.dump(results["validation"], f, indent=2)
        logger.info(f"Validation ({len(results['validation']['passed'])} passed): {validation_file}")
        
        # Submission
        submission_file = self.output_dir / f"{self.workflow_id}_submission.json"
        with open(submission_file, "w") as f:
            json.dump(results["submission"], f, indent=2)
        logger.info(f"Submission: {submission_file}")
        
        # Summary
        summary = results.get("execution_summary", {})
        summary_file = self.output_dir / f"{self.workflow_id}_summary.json"
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)
        logger.info(f"Summary: {summary_file}")
    
    def run(self, task_prompt: str) -> Dict[str, Any]:
        """Execute the complete pipeline: workflow → extract → compile → validate → submit."""
        try:
            # Stage 1: Execute Creative Town Workflow
            logger.info("STAGE 1: Executing Creative Town workflow...")
            workflow_result = self.execute_workflow(task_prompt)
            
            # Stage 2: Extract claims from ALL 6 agents
            logger.info("STAGE 2: Extracting claims from 6 agents...")
            claims = self.extract_claims(workflow_result)
            
            # Stage 3: Compile claims into structured proposals
            logger.info("STAGE 3: Compiling claims into proposals...")
            proposals = self.compile_claims(claims)
            
            # Stage 4: Validate proposals against hard rules
            logger.info("STAGE 4: Validating proposals against Oracle Town rules...")
            validated = self.validate_proposals(proposals)
            
            # Stage 5: Submit to Oracle (only validated proposals)
            logger.info("STAGE 5: Submitting to Oracle Intake...")
            submission = self.submit_claims_to_oracle(validated["passed"])
            
            # Stage 6: Save all artifacts
            results = {
                "workflow": workflow_result,
                "claims": claims,
                "proposals": proposals,
                "validation": validated,
                "submission": submission,
                "execution_summary": {
                    "task": task_prompt,
                    "agents_engaged": 6,
                    "claims_generated": len(claims),
                    "proposals_compiled": len(proposals),
                    "proposals_passed_validation": len(validated["passed"]),
                    "proposals_rejected": len(validated["rejected"]),
                    "proposals_submitted": submission["total_submitted"],
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            self.save_results(results)
            
            print("\n" + "="*70)
            print("GOVERNANCE-WRAPPED WORKFLOW EXECUTION COMPLETE")
            print("="*70)
            print(f"Workflow ID: {self.workflow_id}")
            print(f"Claims extracted (6 agents): {len(claims)}")
            print(f"Proposals compiled: {len(proposals)}")
            print(f"Proposals passed validation: {len(validated['passed'])}")
            print(f"Proposals rejected: {len(validated['rejected'])}")
            print(f"Proposals submitted to Oracle: {submission['total_submitted']}")
            print(f"Output directory: {self.output_dir.absolute()}")
            print("="*70 + "\n")
            
            return results
            
        except Exception as e:
            logger.error(f"Execution failed: {e}", exc_info=True)
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Execute ChatDev 2.0 workflow with Oracle Town governance"
    )
    parser.add_argument("--yaml", required=True, help="Path to ChatDev workflow YAML")
    parser.add_argument("--prompt", required=True, help="Task prompt for workflow")
    parser.add_argument("--output-dir", default="./results", help="Output directory")
    
    args = parser.parse_args()
    
    runner = GovernanceWrappedRunner(yaml_file=args.yaml, output_dir=args.output_dir)
    runner.run(task_prompt=args.prompt)


if __name__ == "__main__":
    main()
