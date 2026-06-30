import json
from collections.abc import Iterable
from pathlib import Path

from autopsy.traces.schema import TraceRecord

def write_jsonl(path: Path, records: Iterable[TraceRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for record in records:
            line = record.model_dump_json()
            file.write(line)
            file.write("\n")
    
def append_jsonl_record(path: Path, record: TraceRecord) -> None:
    """Append one completed request trace.

    Benchmarks should write evidence as each request finishes. If the run is
    interrupted halfway through, the trace file still contains every request
    that completed before the interruption.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(record.model_dump_json())
        file.write("\n")

def read_jsonl(path: Path) -> list[TraceRecord]:
    records: list[TraceRecord] = []
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number}: {exc}") from exc
            try:
                records.append(TraceRecord.model_validate(data))
            except Exception as exc:
                raise ValueError(f"Invalid trace record on line {line_number}: {exc}") from exc
    return records
