"""
ORACLE shipping (final artifact generation)
"""

from __future__ import annotations

import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Literal, Tuple

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mayor.decide import sha256_hex, compute_decision_meta


Format = Literal["latex", "code", "text"]


def _render_latex(payload: Dict[str, Any]) -> str:
    return r"""\documentclass[11pt]{article}
\usepackage{amsmath,amssymb}
\usepackage[T1]{fontenc}
\begin{document}

\section*{WUL-ORACLE Shipment Artifact}

\subsection*{Decision Payload (Deterministic)}
\begin{verbatim}
""" + _pretty(payload) + r"""
\end{verbatim}

\subsection*{Statement}
This artifact is emitted only under SHIP: receipt\_gap = 0 and kill\_switches\_pass = true.

\end{document}
"""


def _render_code(payload: Dict[str, Any]) -> str:
    # Python module-style "receipt" object
    return (
        "# Auto-generated WUL-ORACLE shipment (deterministic payload)\n"
        "DECISION_PAYLOAD = "
        + _pretty(payload)
        + "\n"
    )


def _render_text(payload: Dict[str, Any]) -> str:
    return (
        "WUL-ORACLE Shipment Artifact\n"
        "===========================\n\n"
        "Decision Payload (deterministic):\n"
        + _pretty(payload)
        + "\n\n"
        "Constraint: emitted only under SHIP.\n"
    )


def _pretty(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False)


def make_shipment(payload: Dict[str, Any], fmt: Format) -> Tuple[str, str]:
    """
    Returns (content, extension).
    """
    if fmt == "latex":
        return _render_latex(payload), "tex"
    if fmt == "code":
        return _render_code(payload), "py"
    return _render_text(payload), "txt"


def make_meta() -> Dict[str, Any]:
    ts = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return compute_decision_meta(
        timestamp_utc=ts,
        python_version=sys.version.split()[0],
        platform=f"{platform.system()} {platform.machine()}"
    )


def shipment_hash(content: str) -> str:
    return sha256_hex({"content": content})
