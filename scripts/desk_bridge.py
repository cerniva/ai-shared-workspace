#!/usr/bin/env python3
"""Loader: concatenates part1+part2 then execs (restore after PLACEHOLDER accident)."""
from pathlib import Path
_here = Path(__file__).resolve()
_p = _here.parent
_code = (_p / "desk_bridge_part1.py").read_text(encoding="utf-8") + (
    _p / "desk_bridge_part2.py"
).read_text(encoding="utf-8")
_g = globals()
_g["__file__"] = str(_here)
_g["__name__"] = __name__
exec(compile(_code, str(_here), "exec"), _g)
