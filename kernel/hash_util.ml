(** kernel/hash_util.ml

    Hash utilities — Trusted Computing Base component.

    Satisfies the extraction contract for LedgerKernel:
      Hash_util.concat  : string -> string -> string
      Hash_util.genesis : string

    PINNED SCHEME: HELEN_CUM_V1 (domain-separated, finalised forever).

    cum_hash = SHA256("HELEN_CUM_V1" || hex_decode(prev_hex) || hex_decode(ph_hex))

    Where:
      "HELEN_CUM_V1"       = 12 ASCII bytes (domain separator)
      hex_decode(prev_hex) = 32 raw bytes (decoded from 64-char hex string)
      hex_decode(ph_hex)   = 32 raw bytes (decoded from 64-char hex string)
      total input          = 76 bytes

    The domain separator prevents cross-scheme preimage attacks and makes
    the cum_hash scheme unambiguously identifiable in the raw data.

    Python reference (HELEN_CUM_V1 scheme — tests/conftest.py):

      HELEN_CUM_V1_PREFIX = b"HELEN_CUM_V1"

      def chain_hash_v1(prev_hex: str, ph_hex: str) -> str:
          return sha256_hex(
              HELEN_CUM_V1_PREFIX + bytes.fromhex(prev_hex) + bytes.fromhex(ph_hex)
          )

    GENESIS: genesis_hash = "0" * 64 (64 zero hex chars = 32 zero bytes)

    BREAKING CHANGE from pre-v1.2: prior scheme was SHA256(prev_bytes || ph_bytes)
    with no domain prefix. All new ledger entries use HELEN_CUM_V1.
    Historical entries (pre-v1.2) used the unprefixed scheme — validate with
    their original validator.
*)

(** genesis: the initial cumulative hash for an empty ledger.
    64 zero characters = 32 zero bytes when hex-decoded.                  *)
let genesis : string =
  String.make 64 '0'

(** hex_decode s: decode a hex string to raw bytes.
    Raises: Invalid_argument if s has odd length or non-hex characters.   *)
let hex_decode (s : string) : bytes =
  let n = String.length s in
  if n mod 2 <> 0 then
    invalid_arg ("Hash_util.hex_decode: odd-length hex string: " ^ s);
  let b = Bytes.create (n / 2) in
  for i = 0 to (n / 2) - 1 do
    let hi = Char.code s.[2*i]     in
    let lo = Char.code s.[2*i + 1] in
    let nibble c =
      if c >= Char.code '0' && c <= Char.code '9' then c - Char.code '0'
      else if c >= Char.code 'a' && c <= Char.code 'f' then c - Char.code 'a' + 10
      else if c >= Char.code 'A' && c <= Char.code 'F' then c - Char.code 'A' + 10
      else invalid_arg ("Hash_util.hex_decode: non-hex char in input")
    in
    Bytes.set b i (Char.chr ((nibble hi lsl 4) lor (nibble lo)))
  done;
  b

(** HELEN_CUM_V1 domain separator: 12 ASCII bytes. *)
let helen_cum_v1_prefix : bytes = Bytes.of_string "HELEN_CUM_V1"

(** concat prev_hex ph_hex:
    Computes HELEN_CUM_V1 cumulative hash:
      SHA256("HELEN_CUM_V1" || hex_decode(prev_hex) || hex_decode(ph_hex))
    as 64-char lowercase hex.

    Both inputs are 64-char lowercase hex strings (SHA256 digests, 32 bytes each).
    Total input to SHA256: 12 + 32 + 32 = 76 bytes.

    MUST agree with chain_hash_v1() in tests/conftest.py.                *)
let concat (prev_hex : string) (ph_hex : string) : string =
  let prev_bytes = hex_decode prev_hex in
  let ph_bytes   = hex_decode ph_hex   in
  (* Concatenate: domain_prefix || prev_bytes || ph_bytes *)
  let combined =
    Bytes.cat
      (Bytes.cat helen_cum_v1_prefix prev_bytes)
      ph_bytes
  in
  Sha256.digest_bytes combined

(*
   Verification test vectors (HELEN_CUM_V1 scheme):

   Python:
     import hashlib
     PREFIX = b"HELEN_CUM_V1"
     def chain_hash_v1(prev, ph):
         return hashlib.sha256(
             PREFIX + bytes.fromhex(prev) + bytes.fromhex(ph)
         ).hexdigest()

   Test 1 (genesis + payload):
     prev = "0" * 64
     ph   = hashlib.sha256(b"hello").hexdigest()
          = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
     result = chain_hash_v1(prev, ph)
          = sha256(b"HELEN_CUM_V1" + b"\x00"*32 + bytes.fromhex(ph))

   CI contract: run these vectors before accepting any kernel build.
*)
