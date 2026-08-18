"""Static status site for the collected Irish Rail lift-status data.

Reads the SQLite index that `lift_status` rebuilds from the raw JSONL logs and
writes a self-contained site to `out/site/`. Standard library only, like the
collector.
"""

__version__ = "1.0.0"
