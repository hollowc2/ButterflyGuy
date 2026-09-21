"""Reconstruct the deployed source/config snapshot from the sanitized raw export."""

import hashlib
import importlib.metadata
import json
import platform
from pathlib import Path

root = Path(__file__).resolve().parent
baseline = json.loads((root / "raw/export.jsonl").open().readline())
(root / "baseline.json").write_text(
    json.dumps({k: v for k, v in baseline.items() if k != "sources"}, indent=2)
)
(root / "baseline.yaml").write_text(baseline["config_yaml"])
assert baseline["config_yaml"].count('strategy: "peakvaluetrailer"') == 1
(root / "candidate.yaml").write_text(
    baseline["config_yaml"].replace('strategy: "peakvaluetrailer"', 'strategy: "profitprotector"')
)
for name, source in baseline["sources"].items():
    assert hashlib.sha256(source["text"].encode()).hexdigest() == source["sha256"]
    path = root / "frozen/butterfly_guy" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source["text"])
(root / "source-hashes.json").write_text(
    json.dumps({k: v["sha256"] for k, v in baseline["sources"].items()}, indent=2)
)
(root / "environment.json").write_text(
    json.dumps(
        {
            "python": platform.python_version(),
            "packages": {
                name: importlib.metadata.version(name)
                for name in ("pydantic", "structlog", "scipy", "pytest", "PyYAML")
            },
        },
        indent=2,
    )
)
