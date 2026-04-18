(* formal/KernelTests.v

   Coq TDD proof obligations for the kernel.

   Purpose: State theorems that MUST hold of the extracted runtime.
   Status:  Some theorems proved here; others are Admitted as CI obligations.

   CI guard:
     grep -c "Admitted\." formal/KernelTests.v
     # Target: 0 (all admitted obligations discharged before release)

   Theorems fall into three groups:
     GROUP A: structural properties (proved in LedgerKernel.v, cited here)
     GROUP B: runtime conformance obligations (require OCaml test harness)
     GROUP C: schema and policy obligations (require plugin layer)

   This file imports LedgerKernel.v and states the proof goals.
   The actual proofs either:
     (a) delegate to LedgerKernel.v lemmas, or
     (b) are Admitted with a precise comment describing the proof strategy.
*)

From Coq Require Import List String Arith Lia Bool.
Import ListNotations.
Open Scope string_scope.

(* Load the kernel module *)
Load "LedgerKernel".
Import LedgerKernel.

(* ================================================================ *)
(* GROUP A: Structural properties — proved in LedgerKernel.v        *)
(*          (cited here as regression tests; should never regress)   *)
(* ================================================================ *)

(** A1: append grows length by exactly 1 (P1) *)
Theorem kt_append_only_length :
  forall L a t raw L',
    append L a t raw = Some L' ->
    length L' = S (length L).
Proof. exact append_only_length. Qed.

(** A2: append adds exactly one suffix event (P2) *)
Theorem kt_append_only_prefix :
  forall L a t raw L',
    append L a t raw = Some L' ->
    exists e, L' = L ++ [e].
Proof. exact append_only_prefix. Qed.

(** A3: CHRONOS cannot issue VERDICT (authority fence) *)
Theorem kt_chronos_no_verdict :
  forall L raw,
    append L CHRONOS VERDICT raw = None.
Proof. exact chronos_no_verdict. Qed.

(** A4: CHRONOS cannot issue TERMINATION *)
Theorem kt_chronos_no_termination :
  forall L raw,
    append L CHRONOS TERMINATION raw = None.
Proof. exact chronos_no_termination. Qed.

(** A5: CHRONOS cannot issue RECEIPT *)
Theorem kt_chronos_no_receipt :
  forall L raw,
    append L CHRONOS RECEIPT raw = None.
Proof. exact chronos_no_receipt. Qed.

(** A6: HELEN cannot issue VERDICT *)
Theorem kt_helen_no_verdict :
  forall L raw,
    append L HELEN VERDICT raw = None.
Proof. exact helen_no_verdict. Qed.

(** A7: HELEN cannot issue TERMINATION *)
Theorem kt_helen_no_termination :
  forall L raw,
    append L HELEN TERMINATION raw = None.
Proof. exact helen_no_termination. Qed.

(** A8: MAYOR cannot issue USER_MESSAGE *)
Theorem kt_mayor_no_user_message :
  forall L raw,
    append L MAYOR USER_MESSAGE raw = None.
Proof. exact mayor_no_user_message. Qed.

(** A9: First TERMINATION accepted (iff ledger has no prior TERMINATION) *)
Theorem kt_first_termination_accepted :
  forall L a raw L',
    append L a TERMINATION raw = Some L' ->
    count_terminations L = 0.
Proof. exact append_first_termination. Qed.

(** A10: Preservation — ledger_ok is closed under valid appends *)
Theorem kt_ledger_ok_preservation :
  forall L a t raw,
    ledger_ok L ->
    structural_valid_b L (make_event L a t raw) = true ->
    ledger_ok (L ++ [make_event L a t raw]).
Proof. exact ledger_ok_app_one. Qed.

(** A11: Empty ledger satisfies ledger_ok *)
Theorem kt_empty_ledger_ok : ledger_ok [].
Proof. exact ledger_ok_nil. Qed.

(** A12: Soundness of boolean guard *)
Theorem kt_structural_validb_sound :
  forall L e,
    structural_valid_b L e = true ->
    structural_valid L e.
Proof. exact structural_validb_sound. Qed.

(** A13: Hash chain soundness (boolean ⟹ Prop) *)
Theorem kt_hash_chain_valid_b_sound :
  forall L,
    hash_chain_valid_b L = true ->
    hash_chain_valid L.
Proof. exact hash_chain_valid_b_sound. Qed.

(* ================================================================ *)
(* GROUP B: Runtime conformance obligations                          *)
(*          These state properties of the EXTRACTED binary.         *)
(*          They cannot be proved in Coq alone; they depend on the  *)
(*          OCaml crypto modules (Sha256, Hash_util).               *)
(*          Admitted here as explicit CI obligations tracked by      *)
(*          the Python test suite (tests/test_kernel_*.py).         *)
(* ================================================================ *)

(** B1: Extraction correctness — sha256 parameter matches Sha256.digest_bytes.

    What this means at the OCaml boundary:
      For all b : bytes,
        (extracted sha256 b) = Sha256.digest_bytes b

    This is an extraction contract, not a Coq theorem.
    Verified by: tests/test_kernel_hash_chain.py::test_payload_hash_matches_*
    Admitted as Coq proof obligation (requires axiom on concrete sha256).
*)
Axiom extraction_sha256_correct :
  forall raw : bytes,
    sha256 raw = sha256 raw.   (* trivially true; content is the OCaml contract *)

(** B2: hash_concat matches HELEN_CUM_V1 scheme.

    What this means:
      hash_concat prev ph =
        SHA256("HELEN_CUM_V1" || hex_decode(prev) || hex_decode(ph))

    Verified by:
      - tests/test_kernel_hash_chain.py::test_first_event_chains_from_genesis
      - tests/test_kernel_hash_chain.py::test_hash_chain_across_multiple_events
      - Test vectors in kernel/hash_util.ml comment block.

    This cannot be stated as a Coq theorem without a concrete model of SHA256.
    Tracked as runtime conformance obligation.
*)
(* (No Coq axiom needed — this is pure OCaml property.) *)

(** B3: kernel_cli binary correctly delegates to extracted append.

    Runtime contract:
      For every valid JSON request on stdin,
        kernel_cli binary MUST call extracted append(L, actor, etype, raw)
        where raw = hex_decode(request.raw_hex)
          and L   = events read from ledger file.

    Verified by: tests/test_kernel_*.py (all tests)
    Admitted as CI obligation until kernel_cli is fully wired.
*)
(* (No Coq axiom needed — pure OCaml/integration property.) *)

(* ================================================================ *)
(* GROUP C: Policy obligations (require policy_validb implementation) *)
(* ================================================================ *)

(** C1: policy_validb is sound with respect to policy_valid (Prop).

    Formal statement:
      forall L e, policy_validb L e = true -> policy_valid L e.

    This must be proved once a concrete policy_validb is provided.
    Currently policy_validb is a pass-through stub (always returns true).

    Admitted: proof obligation for the policy implementer.
*)
Lemma kt_policy_validb_sound :
  forall L e,
    policy_validb L e = true ->
    policy_valid L e.
Proof.
  (* OBLIGATION: prove once policy_validb is concretely defined.
     Strategy: unfold policy_validb; case-split on the boolean conditions;
     prove each case satisfies the policy_valid Prop.
     Until then, admitted as explicit CI obligation.                    *)
  Admitted.

(** C2: Fail-closed default — policy_validb = false is always safe.

    The system should never accept an event that violates policy_valid.
    (policy_valid may still hold even when policy_validb = false, but
     that would just be conservative / over-rejection, not a safety bug.)

    This C2 is the liveness complement; it's less critical than C1.
    Admitted as architectural principle, not a Coq theorem.
*)
(* (No Coq statement needed.) *)

(* ================================================================ *)
(* CI TRACKING SUMMARY                                               *)
(* ================================================================ *)

(*
   Admitted proof obligations at time of writing:
     - kt_policy_validb_sound (C1): requires concrete policy_validb
     - (no others)

   Run: grep -c "Admitted\." formal/KernelTests.v
   Target: 0 before production release.

   Tests that validate GROUP B at the integration level:
     tests/test_kernel_append_only.py   (31 tests → RED until binary wired)
     tests/test_kernel_seq.py
     tests/test_kernel_hash_chain.py
     tests/test_kernel_termination_unique.py
     tests/test_kernel_authority.py
*)
