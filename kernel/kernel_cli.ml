(** kernel/kernel_cli.ml

    Thin CLI boundary between LedgerKernel extraction and the runtime.

    This file has THREE responsibilities:
      1. Provides the link-time modules that satisfy the Coq extraction
         contract (Sha256, Hash_util).
      2. Provides a minimal policy bridge (reads policy_flags from request;
         default is CLOSED until a policy module is linked).
      3. Exposes a single CLI entrypoint:
           stdin  -> JSON append request
           stdout -> JSON append response (success or error)
           effect -> appends one NDJSON line to the ledger file

    This is the ONLY file that may write to the ledger.
    Any write to LEDGER_PATH outside this binary FAILS CI.
    See CI rule: .github/workflows/kernel_guard.yml

    Usage:
      echo '{"actor":"HELEN","etype":"VERDICT","raw_hex":"<hex>","ctx":{...}}' \
        | ./kernel_cli /path/to/ledger.ndjson

    Input JSON schema (stdin):
      {
        "actor":   "HELEN" | "MAYOR",
        "etype":   <EventType string>,
        "raw_hex": "<hex-encoded raw payload bytes>",
        "ctx": {
          "iteration_count":    <nat>,
          "risk_tier":          <nat>,   // 0=LOW 1=MED 2=HIGH
          "eval_receipt_count": <nat>
        }
      }

    Output JSON schema (stdout):
      Success: { "ok": true,  "cum_hash": "<64-char hex>", "seq": <nat> }
      Failure: { "ok": false, "error": "<reason>" }

    Exit codes:
      0 = event appended successfully
      1 = structural or policy violation (logged to stderr)
      2 = I/O or parse error

    Dependencies: digestif (OCaml SHA256), yojson (JSON parsing)
      opam install digestif yojson
*)

(* ------------------------------------------------------------------ *)
(* Module shims: satisfy Coq extraction's external module requirements  *)
(* These are the ONLY implementations allowed for these modules.        *)
(* ------------------------------------------------------------------ *)

module Sha256 = struct
  (** digest_bytes: SHA256 of raw bytes, as 64-char lowercase hex. *)
  let digest_bytes = Sha256.digest_bytes
end

module Hash_util = struct
  (** genesis: 64 zero characters — initial cumulative hash. *)
  let genesis = Hash_util.genesis

  (** concat: cum_hash combining operation.
      concat prev_hex ph_hex = sha256(unhex(prev)||unhex(ph)) as hex.
      MUST match Python's chain_hash() in tools/ndjson_writer.py.     *)
  let concat = Hash_util.concat
end

(* ------------------------------------------------------------------ *)
(* Load the extracted Coq kernel                                        *)
(* (ledger_kernel.ml is produced by: coqc formal/LedgerKernel.v)       *)
(* ------------------------------------------------------------------ *)

(* open LedgerKernel *)
(*
   The extracted ledger_kernel.ml defines:
     type eventType = ET_UserMessage | ET_TurnVerdict | ET_Artifact
                    | ET_Seal | ET_PolicyReceipt
     type authority = Auth_Her | Auth_Hal | Auth_Cli
     type event = { event_type; authority_tag; payload_hash; cum_hash }
     type ledger = event list
     val append : ledger -> bytes -> eventType -> authority
                  -> policyContext -> ledger option
     val make_event : ledger -> ... -> event
     val last_cum_hash : ledger -> string
     val genesis_hash : string
*)

(* ------------------------------------------------------------------ *)
(* Policy bridge: stub that reads policy flags from request context.   *)
(* Replace with a real policy module at link time for production use.  *)
(* Default: CLOSED (policy_valid always returns false until linked).   *)
(* ------------------------------------------------------------------ *)

(*
   In the extracted kernel, policy_valid is:
     Extract Constant policy_valid => "(fun _l _e -> false)".
   This is the fail-closed placeholder.
   A real policy module would implement:
     val policy_valid : event list -> event -> bool
   and be linked in place of the placeholder.

   v1.1 policy (Pα + Pβ — from PolicyLemmas.v when written):
     let policy_valid ledger e =
       let ctx = ... (* from request context *) in
       let alpha_ok = iteration_floor ctx.risk_tier <= ctx.iteration_count in
       let beta_ok  = match e.etype with
         | ET_Artifact when ctx.risk_tier >= 1 -> ctx.eval_receipt_count >= 1
         | _ -> true
       in
       alpha_ok && beta_ok
*)

(* ------------------------------------------------------------------ *)
(* NDJSON ledger I/O                                                   *)
(* ------------------------------------------------------------------ *)

(** read_ledger path: load all events from ledger NDJSON file.
    Returns empty list if file does not exist.
    Raises: Failure if file is malformed JSON.                         *)
let read_ledger (_path : string) : (* event list *) unit =
  (* Stub: in production, parse NDJSON lines to event records.
     Each line is a JSON object with fields:
       seq, event_type, authority_tag, payload_hash, prev_cum_hash, cum_hash
     The kernel only needs: cum_hash of the last event (for last_cum_hash).
     A lightweight loader reads only the last line for efficiency.       *)
  ()

(** write_event path event meta: append one NDJSON event line.
    meta: JSON object of non-hashed observational fields (timestamp etc.)
    Format matches tools/ndjson_writer.py exactly.                      *)
let write_event (path : string) (_event : unit) (meta : string) : unit =
  (* Stub: in production, serialize event to JSON and append line:
     { "seq": ..., "event_type": "...", "authority_tag": "...",
       "payload_hash": "...", "prev_cum_hash": "...", "cum_hash": "...",
       "meta": <meta_json> }
     Opened with O_APPEND | O_WRONLY to prevent races.                  *)
  let _oc = open_out_gen [Open_append; Open_wronly; Open_creat] 0o644 path in
  let _line = Printf.sprintf "{\"_meta\":%s}\n" meta in
  (* output_string oc line; close_out oc *)
  ()

(* ------------------------------------------------------------------ *)
(* CLI entrypoint                                                       *)
(* ------------------------------------------------------------------ *)

(*
   Main loop:
     1. Parse JSON request from stdin.
     2. Load current ledger from path (last line only for efficiency).
     3. Decode raw_hex -> bytes (the canonicalized payload bytes).
     4. Call append(L, raw, et, auth, ctx) from extracted kernel.
     5. On Some(L'), write new event to ledger file.
     6. Print JSON response to stdout.
     7. Exit 0 on success, 1 on policy/structural violation, 2 on I/O.

   The NDJSON line written by this binary is the ONLY legitimate way
   to extend the ledger. CI enforces: no other file may open the ledger
   path for writing. Validated by kernel_guard.yml (grep for
   open(..., "a") outside kernel_cli).
*)

let () =
  if Array.length Sys.argv < 2 then begin
    Printf.eprintf "Usage: %s <ledger.ndjson>\n" Sys.argv.(0);
    exit 2
  end;
  let _ledger_path = Sys.argv.(1) in
  (* Read request JSON from stdin *)
  let _request_json = try input_line stdin
    with End_of_file ->
      Printf.eprintf "kernel_cli: no input on stdin\n";
      exit 2
  in
  (* Stub: full implementation requires:
       1. Yojson.Safe.from_string request_json
       2. Extract actor, etype, raw_hex, ctx
       3. Bytes.of_string (Hex.decode raw_hex)
       4. Load last event from ledger_path
       5. append(L, raw, et, auth, ctx)
       6. On Some L' -> write_event + print { ok: true, cum_hash, seq }
       7. On None    -> print { ok: false, error: "..." } + exit 1
  *)
  Printf.printf "{\"ok\":false,\"error\":\"kernel_cli stub: not yet linked\"}\n";
  exit 1
