# What to test:
# Write 1 or more records 
# Read them back
# Confirm the requested IDs match

from pathlib import Path
from autopsy.traces.jsonl import read_jsonl, write_jsonl
from tests.test_schema import make_record

def test_jsonl_roun_trip(tmp_path: Path) -> None:
    path = tmp_path / "trace.jsonl"
    records = [make_record()]

    write_jsonl(path, records)
    loaded = read_jsonl(path)

    assert len(loaded) == 1
    assert loaded[0].request_id == "req_001"

