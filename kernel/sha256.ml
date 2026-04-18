(** kernel/sha256.ml

    SHA256 concrete implementation — Trusted Computing Base component.

    This module is part of the TCB for the extracted LedgerKernel.
    It satisfies the extraction contract:
      Sha256.digest_bytes : bytes -> string
      where string = 64-char lowercase hex digest

    CRITICAL: The output MUST match Python's hashlib.sha256(b).hexdigest()
    for identical byte inputs.  The Python runtime (tools/ndjson_writer.py)
    is the reference implementation; this module must agree bit-for-bit.

    Dependency: digestif >= 1.1.0  (pure-OCaml, no C bindings required)
      opam install digestif

    If digestif is unavailable, the fallback via Cstruct/Nocrypto is noted
    in the comments, but digestif is strongly preferred.
*)

(** digest_bytes b: SHA256 hash of raw bytes b, returned as 64-char hex string. *)
let digest_bytes (b : bytes) : string =
  (* digestif.SHA256: pure OCaml SHA256, FIPS 180-4 compliant *)
  let ctx   = Digestif.SHA256.empty in
  let ctx   = Digestif.SHA256.feed_bytes ctx b in
  let hash  = Digestif.SHA256.get ctx in
  Digestif.SHA256.to_hex hash

(*
   Verification: the following must hold for all b:
     digest_bytes b = Python's hashlib.sha256(bytes(b)).hexdigest()

   Quick test (compare with Python):
     Python:  import hashlib; hashlib.sha256(b"hello").hexdigest()
              => "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
     OCaml:   Sha256.digest_bytes (Bytes.of_string "hello")
              => "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"

   CI contract: run this test before accepting any ledger-kernel build.
*)
