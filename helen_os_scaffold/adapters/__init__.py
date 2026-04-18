"""
adapters/ — Single sovereign write-gate layer.

ONLY these modules may append to storage channels.

  adapters/write_gate.py     -> canonical choke-point
  adapters/town_adapter.py   -> Channel A (town ledger)
  adapters/memory_adapter.py -> Channel B (memory)
  adapters/trace_adapter.py  -> Channel C (run trace)

FORBIDDEN in all other modules:
  direct open() / write() to storage/*.ndjson
  any import of write_gate from outside adapters/
"""
