# AML Immune Reconstitution QC Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a read-only, test-driven foundation that inventories the three AML HSCT source files, normalizes identifiers and dates, reconciles patient coverage, and emits privacy-safe QC artifacts without copying or modifying raw clinical data.

**Architecture:** A small Python package reads source locations from an environment variable, fingerprints each input, inspects CSV and XLSX sources through streaming or read-only adapters, and produces aggregate JSON artifacts. Domain normalization and linkage logic remain independent from file readers so the same rules can be reused by the immune-report, timeline, and statistical-analysis phases.

**Tech Stack:** WSL2 Ubuntu 24.04, Python 3.12, DuckDB 1.5.4, Polars 1.43.1, PyArrow 25.0.0, openpyxl 3.1.5, pytest 9.1.1.

## Global Constraints

- Treat every source file as read-only; never rename, overwrite, delete, or rewrite it.
- Resolve the real source directory only through `AML_DATA_ROOT`; never commit the clinical path.
- Do not copy raw patient-level data into WSL ext4 or the Git repository.
- Write only aggregate, privacy-reviewed artifacts under `aml_immune_qc/artifacts/<run_id>/`.
- Never emit raw patient identifiers, visit identifiers, report text, physician names, or individual clinical records.
- Preserve original values internally when later phases add cleaning; standardized values must never overwrite source values.
- Use Python 3.12 and the exact dependency versions listed above; freeze the installed environment after successful setup.
- Use TDD for every transformation and reconciliation rule.
- The first real-data acceptance counts are: transplant patients 2,820; structured-lab patients 2,819; immune-report patients 2,798; all-three intersection 2,798.
- GPU is out of scope for this phase; RTX 4090 is reserved for validated local NLP or later machine-learning tasks.

---

## Planned File Structure

```text
aml_immune_qc/
├── .gitignore
├── README.md
├── pyproject.toml
├── config/
│   └── datasets.example.toml
├── src/aml_immune_qc/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── config.py
│   ├── manifest.py
│   ├── schema.py
│   ├── linkage.py
│   ├── privacy.py
│   ├── io/
│   │   ├── __init__.py
│   │   ├── csv_source.py
│   │   └── xlsx_source.py
│   ├── normalize/
│   │   ├── __init__.py
│   │   ├── identifiers.py
│   │   └── dates.py
│   └── qc/
│       ├── __init__.py
│       └── foundation.py
└── tests/
    ├── conftest.py
    ├── unit/
    │   ├── test_package.py
    │   ├── test_config.py
    │   ├── test_manifest.py
    │   ├── test_schema.py
    │   ├── test_identifiers.py
    │   ├── test_dates.py
    │   ├── test_linkage.py
    │   └── test_privacy.py
    └── integration/
        └── test_foundation_real_data.py
```

### Task 1: Bootstrap the isolated WSL project

**Files:**
- Create: `aml_immune_qc/pyproject.toml`
- Create: `aml_immune_qc/.gitignore`
- Create: `aml_immune_qc/README.md`
- Create: `aml_immune_qc/src/aml_immune_qc/__init__.py`
- Create: `aml_immune_qc/tests/unit/test_package.py`

**Interfaces:**
- Consumes: Python 3.12 from WSL2.
- Produces: importable package `aml_immune_qc` with `__version__ == "0.1.0"`.

- [ ] **Step 1: Write the failing package test**

```python
from aml_immune_qc import __version__


def test_package_version() -> None:
    assert __version__ == "0.1.0"
```

- [ ] **Step 2: Create the package metadata**

```toml
[build-system]
requires = ["setuptools>=75"]
build-backend = "setuptools.build_meta"

[project]
name = "aml-immune-qc"
version = "0.1.0"
requires-python = "==3.12.*"
dependencies = [
  "duckdb==1.5.4",
  "polars==1.43.1",
  "pyarrow==25.0.0",
  "openpyxl==3.1.5",
]

[project.optional-dependencies]
dev = ["pytest==9.1.1"]

[project.scripts]
aml-immune-qc = "aml_immune_qc.cli:main"

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra"
```

- [ ] **Step 3: Add the minimal package and ignore rules**

```python
"""AML HSCT immune-reconstitution quality-control tools."""

__version__ = "0.1.0"
```

```gitignore
.venv/
__pycache__/
.pytest_cache/
*.pyc
artifacts/
config/datasets.local.toml
```

```markdown
# AML Immune Reconstitution QC

Read-only, test-driven quality control for the AML HSCT immune-reconstitution cohort.

The real clinical source directory is supplied through `AML_DATA_ROOT`. Raw clinical
data must never be copied into this repository. Generated aggregate artifacts are
written below `artifacts/<run_id>/` and are excluded from Git.
```

- [ ] **Step 4: Create and install the isolated environment**

Run:

```bash
python3 -m venv /home/reborn/.venvs/aml-qc-cpu
/home/reborn/.venvs/aml-qc-cpu/bin/python -m pip install --upgrade pip
/home/reborn/.venvs/aml-qc-cpu/bin/python -m pip install -e './aml_immune_qc[dev]'
/home/reborn/.venvs/aml-qc-cpu/bin/python -m pip freeze
```

Expected: installation succeeds; the freeze output contains DuckDB 1.5.4, Polars 1.43.1, PyArrow 25.0.0, openpyxl 3.1.5, and pytest 9.1.1.

- [ ] **Step 5: Run the test and commit**

Run: `/home/reborn/.venvs/aml-qc-cpu/bin/pytest aml_immune_qc/tests/unit/test_package.py -v`  
Expected: `1 passed`.

```bash
git add aml_immune_qc
git commit -m "build: bootstrap AML immune QC package"
```

### Task 2: Resolve source configuration without committing clinical paths

**Files:**
- Create: `aml_immune_qc/config/datasets.example.toml`
- Create: `aml_immune_qc/src/aml_immune_qc/config.py`
- Create: `aml_immune_qc/tests/unit/test_config.py`

**Interfaces:**
- Consumes: environment variable `AML_DATA_ROOT`.
- Produces: `DatasetPaths.from_environment() -> DatasetPaths` and `DatasetPaths.validate() -> None`.

- [ ] **Step 1: Write failing configuration tests**

```python
from pathlib import Path

import pytest

from aml_immune_qc.config import DatasetPaths


def test_resolves_exact_source_names(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("AML_DATA_ROOT", str(tmp_path))
    paths = DatasetPaths.from_environment()
    assert paths.transplant.name == "移植信息.xlsx"
    assert paths.labs.name == "检验数据.csv"
    assert paths.immune_reports.name == "免疫重建+免疫残留.xlsx"


def test_missing_environment_variable_is_rejected(monkeypatch) -> None:
    monkeypatch.delenv("AML_DATA_ROOT", raising=False)
    with pytest.raises(ValueError, match="AML_DATA_ROOT"):
        DatasetPaths.from_environment()
```

- [ ] **Step 2: Run the tests to verify failure**

Run: `pytest aml_immune_qc/tests/unit/test_config.py -v`  
Expected: collection fails because `aml_immune_qc.config` does not exist.

- [ ] **Step 3: Implement immutable path resolution**

```python
from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class DatasetPaths:
    root: Path
    transplant: Path
    labs: Path
    immune_reports: Path

    @classmethod
    def from_environment(cls) -> "DatasetPaths":
        raw_root = os.environ.get("AML_DATA_ROOT")
        if not raw_root:
            raise ValueError("AML_DATA_ROOT is required")
        root = Path(raw_root).expanduser().resolve()
        return cls(
            root=root,
            transplant=root / "移植信息.xlsx",
            labs=root / "检验数据.csv",
            immune_reports=root / "免疫重建+免疫残留.xlsx",
        )

    def validate(self) -> None:
        missing = [
            str(path)
            for path in (self.transplant, self.labs, self.immune_reports)
            if not path.is_file()
        ]
        if missing:
            raise FileNotFoundError("Missing source files: " + ", ".join(missing))
```

- [ ] **Step 4: Add a path-free example configuration**

```toml
[datasets]
root_env = "AML_DATA_ROOT"
transplant = "移植信息.xlsx"
labs = "检验数据.csv"
immune_reports = "免疫重建+免疫残留.xlsx"
```

- [ ] **Step 5: Run tests and commit**

Run: `pytest aml_immune_qc/tests/unit/test_config.py -v`  
Expected: `2 passed`.

```bash
git add aml_immune_qc/config aml_immune_qc/src/aml_immune_qc/config.py aml_immune_qc/tests/unit/test_config.py
git commit -m "feat: resolve clinical sources from environment"
```

### Task 3: Fingerprint sources and prove raw-data immutability

**Files:**
- Create: `aml_immune_qc/src/aml_immune_qc/manifest.py`
- Create: `aml_immune_qc/tests/unit/test_manifest.py`

**Interfaces:**
- Consumes: `Path`.
- Produces: `fingerprint(path: Path, chunk_size: int = 8 * 1024 * 1024) -> FileFingerprint`.

- [ ] **Step 1: Write the failing fingerprint test**

```python
from hashlib import sha256

from aml_immune_qc.manifest import fingerprint


def test_fingerprint_matches_file_bytes(tmp_path) -> None:
    source = tmp_path / "source.bin"
    source.write_bytes(b"clinical-source")
    before = source.stat()
    result = fingerprint(source)
    after = source.stat()
    assert result.sha256 == sha256(b"clinical-source").hexdigest()
    assert result.size_bytes == len(b"clinical-source")
    assert before.st_mtime_ns == after.st_mtime_ns
    assert source.read_bytes() == b"clinical-source"
```

- [ ] **Step 2: Run the test to verify failure**

Run: `pytest aml_immune_qc/tests/unit/test_manifest.py -v`  
Expected: FAIL because `fingerprint` is unavailable.

- [ ] **Step 3: Implement streaming fingerprints**

```python
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path


@dataclass(frozen=True)
class FileFingerprint:
    name: str
    size_bytes: int
    mtime_ns: int
    sha256: str

    def to_dict(self) -> dict[str, str | int]:
        return asdict(self)


def fingerprint(path: Path, chunk_size: int = 8 * 1024 * 1024) -> FileFingerprint:
    digest = sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    stat = path.stat()
    return FileFingerprint(
        name=path.name,
        size_bytes=stat.st_size,
        mtime_ns=stat.st_mtime_ns,
        sha256=digest.hexdigest(),
    )
```

- [ ] **Step 4: Run tests and commit**

Run: `pytest aml_immune_qc/tests/unit/test_manifest.py -v`  
Expected: `1 passed`.

```bash
git add aml_immune_qc/src/aml_immune_qc/manifest.py aml_immune_qc/tests/unit/test_manifest.py
git commit -m "feat: fingerprint immutable clinical sources"
```

### Task 4: Inspect CSV and XLSX schemas through read-only adapters

**Files:**
- Create: `aml_immune_qc/src/aml_immune_qc/io/__init__.py`
- Create: `aml_immune_qc/src/aml_immune_qc/io/csv_source.py`
- Create: `aml_immune_qc/src/aml_immune_qc/io/xlsx_source.py`
- Create: `aml_immune_qc/src/aml_immune_qc/schema.py`
- Create: `aml_immune_qc/tests/unit/test_schema.py`

**Interfaces:**
- Consumes: CSV/XLSX paths.
- Produces: `inspect_csv(path: Path) -> TableSchema` and `inspect_xlsx(path: Path) -> list[TableSchema]`.

- [ ] **Step 1: Write failing schema tests, including embedded CSV newlines**

```python
from pathlib import Path

from openpyxl import Workbook

from aml_immune_qc.io.csv_source import inspect_csv, read_csv_identifiers
from aml_immune_qc.io.xlsx_source import inspect_xlsx, read_xlsx_identifiers


def test_csv_counts_logical_records(tmp_path: Path) -> None:
    path = tmp_path / "source.csv"
    path.write_text('PATIENT_SN,NOTE\n1,"line one\nline two"\n2,ok\n', encoding="utf-8")
    result = inspect_csv(path)
    assert result.rows == 2
    assert result.columns == ("PATIENT_SN", "NOTE")
    assert read_csv_identifiers(path, "PATIENT_SN") == {"1", "2"}


def test_xlsx_reports_sheet_dimensions(tmp_path: Path) -> None:
    path = tmp_path / "source.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Data"
    sheet.append(["患者编号", "移植日期"])
    sheet.append(["P1", "2025-01-01"])
    workbook.save(path)
    result = inspect_xlsx(path)
    assert result[0].sheet == "Data"
    assert result[0].rows == 1
    assert result[0].columns == ("患者编号", "移植日期")
    assert read_xlsx_identifiers(path, "患者编号") == {"P1"}
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest aml_immune_qc/tests/unit/test_schema.py -v`  
Expected: FAIL because the read-only adapters do not exist.

- [ ] **Step 3: Define the shared schema type**

```python
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class TableSchema:
    source: str
    sheet: str | None
    rows: int
    columns: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
```

- [ ] **Step 4: Implement the CSV adapter**

```python
from pathlib import Path

import duckdb

from aml_immune_qc.schema import TableSchema


def _source_expression(path: Path) -> str:
    escaped = str(path).replace("'", "''")
    return f"read_csv_auto('{escaped}', header=true, all_varchar=true)"


def inspect_csv(path: Path) -> TableSchema:
    connection = duckdb.connect()
    try:
        source = _source_expression(path)
        cursor = connection.execute(f"SELECT * FROM {source} LIMIT 0")
        columns = tuple(item[0] for item in cursor.description)
        rows = int(connection.execute(f"SELECT count(*) FROM {source}").fetchone()[0])
        return TableSchema(source=path.name, sheet=None, rows=rows, columns=columns)
    finally:
        connection.close()


def read_csv_identifiers(path: Path, column: str) -> set[str]:
    quoted_column = '"' + column.replace('"', '""') + '"'
    connection = duckdb.connect()
    try:
        source = _source_expression(path)
        values = connection.execute(
            f"SELECT DISTINCT {quoted_column} FROM {source} "
            f"WHERE {quoted_column} IS NOT NULL AND trim({quoted_column}) <> ''"
        ).fetchall()
    finally:
        connection.close()
    return {str(value).strip() for (value,) in values if str(value).strip()}
```

- [ ] **Step 5: Implement the XLSX adapter**

```python
from pathlib import Path

from openpyxl import load_workbook

from aml_immune_qc.schema import TableSchema


def inspect_xlsx(path: Path) -> list[TableSchema]:
    workbook = load_workbook(path, read_only=True, data_only=False)
    results: list[TableSchema] = []
    try:
        for sheet in workbook.worksheets:
            header = next(sheet.iter_rows(min_row=1, max_row=1, values_only=True))
            columns = tuple("" if value is None else str(value).strip() for value in header)
            results.append(
                TableSchema(
                    source=path.name,
                    sheet=sheet.title,
                    rows=max(sheet.max_row - 1, 0),
                    columns=columns,
                )
            )
    finally:
        workbook.close()
    return results


def read_xlsx_identifiers(
    path: Path,
    column: str,
    sheet_name: str | None = None,
) -> set[str]:
    workbook = load_workbook(path, read_only=True, data_only=True)
    sheet = workbook[sheet_name] if sheet_name else workbook.active
    try:
        rows = sheet.iter_rows(values_only=True)
        header = tuple("" if value is None else str(value).strip() for value in next(rows))
        column_index = header.index(column)
        identifiers: set[str] = set()
        for row in rows:
            value = row[column_index]
            if value is not None and str(value).strip():
                identifiers.add(str(value).strip())
        return identifiers
    finally:
        workbook.close()
```

- [ ] **Step 6: Run tests and commit**

Run: `pytest aml_immune_qc/tests/unit/test_schema.py -v`  
Expected: `2 passed`.

```bash
git add aml_immune_qc/src/aml_immune_qc/io aml_immune_qc/src/aml_immune_qc/schema.py aml_immune_qc/tests/unit/test_schema.py
git commit -m "feat: inspect CSV and XLSX source schemas"
```

### Task 5: Normalize identifiers and clinical dates

**Files:**
- Create: `aml_immune_qc/src/aml_immune_qc/normalize/__init__.py`
- Create: `aml_immune_qc/src/aml_immune_qc/normalize/identifiers.py`
- Create: `aml_immune_qc/src/aml_immune_qc/normalize/dates.py`
- Create: `aml_immune_qc/tests/unit/test_identifiers.py`
- Create: `aml_immune_qc/tests/unit/test_dates.py`

**Interfaces:**
- Produces: `normalize_identifier(value: object) -> str | None`.
- Produces: `parse_clinical_datetime(value: object) -> datetime | None`.

- [ ] **Step 1: Write identifier edge-case tests**

```python
import pytest

from aml_immune_qc.normalize.identifiers import normalize_identifier


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, None),
        ("", None),
        ("  P001  ", "P001"),
        (123, "123"),
        (123.0, "123"),
        ("123.0", "123"),
        ("00123", "00123"),
    ],
)
def test_normalize_identifier(value, expected) -> None:
    assert normalize_identifier(value) == expected
```

- [ ] **Step 2: Write date-format tests**

```python
from datetime import datetime

import pytest

from aml_immune_qc.normalize.dates import parse_clinical_datetime


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("2025-01-02 03:04:05", datetime(2025, 1, 2, 3, 4, 5)),
        ("1/2/2025 03:04:05", datetime(2025, 1, 2, 3, 4, 5)),
        ("2025/01/02", datetime(2025, 1, 2)),
        (datetime(2025, 1, 2), datetime(2025, 1, 2)),
        ("not-a-date", None),
        ("", None),
    ],
)
def test_parse_clinical_datetime(value, expected) -> None:
    assert parse_clinical_datetime(value) == expected
```

- [ ] **Step 3: Run both tests to verify failure**

Run: `pytest aml_immune_qc/tests/unit/test_identifiers.py aml_immune_qc/tests/unit/test_dates.py -v`  
Expected: FAIL because normalization functions are unavailable.

- [ ] **Step 4: Implement identifier normalization**

```python
from decimal import Decimal, InvalidOperation


def normalize_identifier(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        number = Decimal(text)
    except InvalidOperation:
        return text
    if "." in text and number == number.to_integral_value():
        return str(number.quantize(Decimal("1")))
    return text
```

- [ ] **Step 5: Implement explicit date parsing**

```python
from datetime import date, datetime


FORMATS = (
    "%Y-%m-%d %H:%M:%S",
    "%m/%d/%Y %H:%M:%S",
    "%Y/%m/%d %H:%M:%S",
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%m/%d/%Y",
)


def parse_clinical_datetime(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    for format_string in FORMATS:
        try:
            return datetime.strptime(text, format_string)
        except ValueError:
            continue
    return None
```

- [ ] **Step 6: Run tests and commit**

Run: `pytest aml_immune_qc/tests/unit/test_identifiers.py aml_immune_qc/tests/unit/test_dates.py -v`  
Expected: all parametrized cases pass.

```bash
git add aml_immune_qc/src/aml_immune_qc/normalize aml_immune_qc/tests/unit/test_identifiers.py aml_immune_qc/tests/unit/test_dates.py
git commit -m "feat: normalize clinical identifiers and dates"
```

### Task 6: Reconcile patient coverage without exporting identifiers

**Files:**
- Create: `aml_immune_qc/src/aml_immune_qc/linkage.py`
- Create: `aml_immune_qc/tests/unit/test_linkage.py`

**Interfaces:**
- Consumes: in-memory identifier sets from read-only adapters.
- Produces: `summarize_linkage(transplant: set[str], labs: set[str], reports: set[str]) -> LinkageSummary`.

- [ ] **Step 1: Write the failing linkage test**

```python
from aml_immune_qc.linkage import summarize_linkage


def test_linkage_summary_exposes_counts_not_identifiers() -> None:
    result = summarize_linkage(
        transplant={"P1", "P2", "P3"},
        labs={"P1", "P2"},
        reports={"P1"},
    )
    assert result.transplant_patients == 3
    assert result.lab_patients == 2
    assert result.report_patients == 1
    assert result.all_three == 1
    assert "P1" not in str(result.to_dict())
```

- [ ] **Step 2: Run the test to verify failure**

Run: `pytest aml_immune_qc/tests/unit/test_linkage.py -v`  
Expected: FAIL because `summarize_linkage` is unavailable.

- [ ] **Step 3: Implement aggregate-only reconciliation**

```python
from dataclasses import asdict, dataclass

from aml_immune_qc.normalize.identifiers import normalize_identifier


@dataclass(frozen=True)
class LinkageSummary:
    transplant_patients: int
    lab_patients: int
    report_patients: int
    transplant_and_labs: int
    transplant_and_reports: int
    all_three: int
    transplant_without_labs: int
    transplant_without_reports: int

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


def summarize_linkage(
    transplant: set[str],
    labs: set[str],
    reports: set[str],
) -> LinkageSummary:
    transplant = {value for item in transplant if (value := normalize_identifier(item)) is not None}
    labs = {value for item in labs if (value := normalize_identifier(item)) is not None}
    reports = {value for item in reports if (value := normalize_identifier(item)) is not None}
    return LinkageSummary(
        transplant_patients=len(transplant),
        lab_patients=len(labs),
        report_patients=len(reports),
        transplant_and_labs=len(transplant & labs),
        transplant_and_reports=len(transplant & reports),
        all_three=len(transplant & labs & reports),
        transplant_without_labs=len(transplant - labs),
        transplant_without_reports=len(transplant - reports),
    )
```

- [ ] **Step 4: Run the unit test and commit**

Run: `pytest aml_immune_qc/tests/unit/test_linkage.py -v`  
Expected: `1 passed`.

```bash
git add aml_immune_qc/src/aml_immune_qc/linkage.py aml_immune_qc/tests/unit/test_linkage.py
git commit -m "feat: add privacy-safe patient reconciliation"
```

### Task 7: Enforce privacy-safe JSON artifacts

**Files:**
- Create: `aml_immune_qc/src/aml_immune_qc/privacy.py`
- Create: `aml_immune_qc/tests/unit/test_privacy.py`

**Interfaces:**
- Produces: `assert_privacy_safe(payload: object) -> None`.
- Rejects keys known to contain direct or row-level identifiers before artifact export.

- [ ] **Step 1: Write failing privacy tests**

```python
import pytest

from aml_immune_qc.privacy import assert_privacy_safe


def test_aggregate_payload_is_allowed() -> None:
    assert_privacy_safe({"patients": 2820, "missing": {"移植日期": 0}})


@pytest.mark.parametrize("key", ["PATIENT_SN", "VISIT_SN", "REPORT_SN", "EXAM_DOCTOR"])
def test_direct_identifier_keys_are_rejected(key: str) -> None:
    with pytest.raises(ValueError, match=key):
        assert_privacy_safe({key: ["raw-value"]})
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest aml_immune_qc/tests/unit/test_privacy.py -v`  
Expected: FAIL because the privacy gate is unavailable.

- [ ] **Step 3: Implement a recursive key gate**

```python
SENSITIVE_KEYS = {
    "PATIENT_SN",
    "PATIENT_SN_ORIGINAL",
    "VISIT_SN",
    "INSPECTION_SN",
    "REPORT_SN",
    "APPLY_SN",
    "EXAM_DOCTOR",
    "REPORT_DOCTOR",
}


def assert_privacy_safe(payload: object) -> None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            if str(key).upper() in SENSITIVE_KEYS:
                raise ValueError(f"Sensitive key is not allowed in artifacts: {key}")
            assert_privacy_safe(value)
    elif isinstance(payload, (list, tuple)):
        for value in payload:
            assert_privacy_safe(value)
```

- [ ] **Step 4: Run tests and commit**

Run: `pytest aml_immune_qc/tests/unit/test_privacy.py -v`  
Expected: all tests pass.

```bash
git add aml_immune_qc/src/aml_immune_qc/privacy.py aml_immune_qc/tests/unit/test_privacy.py
git commit -m "feat: prevent identifiers in QC artifacts"
```

### Task 8: Build the end-to-end foundation command

**Files:**
- Create: `aml_immune_qc/src/aml_immune_qc/qc/__init__.py`
- Create: `aml_immune_qc/src/aml_immune_qc/qc/foundation.py`
- Create: `aml_immune_qc/src/aml_immune_qc/cli.py`
- Create: `aml_immune_qc/src/aml_immune_qc/__main__.py`
- Create: `aml_immune_qc/tests/conftest.py`
- Create: `aml_immune_qc/tests/integration/test_foundation_cli.py`
- Create: `aml_immune_qc/tests/integration/test_foundation_real_data.py`

**Interfaces:**
- Consumes: `AML_DATA_ROOT` and `--output <directory>`.
- Produces: `source_manifest.json`, `schema_summary.json`, `linkage_summary.json`, and `validation_summary.json`.
- Produces: `build_foundation_summary() -> dict[str, object]`.

- [ ] **Step 1: Write the failing CLI integration test with synthetic sources**

```python
import json
from pathlib import Path

from aml_immune_qc.cli import main


def test_foundation_cli_writes_only_expected_artifacts(
    monkeypatch,
    synthetic_source_root: Path,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("AML_DATA_ROOT", str(synthetic_source_root))
    output = tmp_path / "artifacts"
    assert main(["foundation-qc", "--output", str(output)]) == 0
    assert sorted(path.name for path in output.iterdir()) == [
        "linkage_summary.json",
        "schema_summary.json",
        "source_manifest.json",
        "validation_summary.json",
    ]
    validation = json.loads((output / "validation_summary.json").read_text(encoding="utf-8"))
    assert validation["status"] == "PASS"
```

- [ ] **Step 2: Add deterministic synthetic fixtures**

```python
import csv
from pathlib import Path

import pytest
from openpyxl import Workbook


@pytest.fixture
def synthetic_source_root(tmp_path: Path) -> Path:
    root = tmp_path / "sources"
    root.mkdir()

    transplant = Workbook()
    sheet = transplant.active
    sheet.title = "患者移植信息数据"
    sheet.append(["医疗机构编号", "患者编号", "患者移植日期", "移植原发病", "移植类型"])
    sheet.append(["ORG", "P1", "2025-01-01", "1-急性髓系白血病", "异基因"])
    sheet.append(["ORG", "P2", "2025-01-02", "1-急性髓系白血病", "异基因"])
    transplant.save(root / "移植信息.xlsx")

    reports = Workbook()
    sheet = reports.active
    sheet.title = "生物血检查数据"
    sheet.append(["PATIENT_SN", "SPECIMEN_TIME", "INSPECTION_NAME"])
    sheet.append(["P1", "2025-02-01", "免疫重建"])
    reports.save(root / "免疫重建+免疫残留.xlsx")

    with (root / "检验数据.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["PATIENT_SN", "SPECIMEN_TIME", "SUB_INSPECTION_CN"])
        writer.writerow(["P1", "2025-02-01", "淋巴细胞绝对数"])
        writer.writerow(["P2", "2025-02-02", "白细胞计数"])
    return root
```

- [ ] **Step 3: Run the integration test to verify failure**

Run: `pytest aml_immune_qc/tests/integration/test_foundation_cli.py -v`  
Expected: FAIL because `main` and the foundation orchestrator are unavailable.

- [ ] **Step 4: Implement the orchestrator and atomic JSON writer**

```python
import json
from pathlib import Path
from tempfile import NamedTemporaryFile

from aml_immune_qc.config import DatasetPaths
from aml_immune_qc.io.csv_source import inspect_csv, read_csv_identifiers
from aml_immune_qc.io.xlsx_source import inspect_xlsx, read_xlsx_identifiers
from aml_immune_qc.linkage import summarize_linkage
from aml_immune_qc.manifest import fingerprint
from aml_immune_qc.privacy import assert_privacy_safe


def write_json_atomic(path: Path, payload: object) -> None:
    assert_privacy_safe(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2, sort_keys=True)
        temporary = Path(stream.name)
    temporary.replace(path)


def build_foundation_summary() -> dict[str, object]:
    paths = DatasetPaths.from_environment()
    paths.validate()
    manifest = [
        fingerprint(paths.transplant).to_dict(),
        fingerprint(paths.labs).to_dict(),
        fingerprint(paths.immune_reports).to_dict(),
    ]
    schemas = [
        *[schema.to_dict() for schema in inspect_xlsx(paths.transplant)],
        inspect_csv(paths.labs).to_dict(),
        *[schema.to_dict() for schema in inspect_xlsx(paths.immune_reports)],
    ]
    transplant_ids = read_xlsx_identifiers(paths.transplant, "患者编号")
    lab_ids = read_csv_identifiers(paths.labs, "PATIENT_SN")
    report_ids = read_xlsx_identifiers(paths.immune_reports, "PATIENT_SN")
    linkage = summarize_linkage(transplant_ids, lab_ids, report_ids).to_dict()
    checks = {
        "sources_present": len(manifest) == 3,
        "schemas_nonempty": all(schema["rows"] > 0 for schema in schemas),
        "intersection_bounded": linkage["all_three"] <= linkage["transplant_patients"],
    }
    validation = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
    }
    return {
        "manifest": manifest,
        "schemas": schemas,
        "linkage": linkage,
        "validation": validation,
    }
```

- [ ] **Step 5: Implement the CLI**

```python
import argparse
from pathlib import Path
from typing import Sequence

from aml_immune_qc.qc.foundation import build_foundation_summary, write_json_atomic


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="aml-immune-qc")
    subparsers = parser.add_subparsers(dest="command", required=True)
    foundation = subparsers.add_parser("foundation-qc")
    foundation.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    summary = build_foundation_summary()
    output = args.output
    write_json_atomic(output / "source_manifest.json", summary["manifest"])
    write_json_atomic(output / "schema_summary.json", summary["schemas"])
    write_json_atomic(output / "linkage_summary.json", summary["linkage"])
    write_json_atomic(output / "validation_summary.json", summary["validation"])
    return 0
```

```python
from aml_immune_qc.cli import main

raise SystemExit(main())
```

- [ ] **Step 6: Add the opt-in frozen real-data test**

```python
import os

import pytest

from aml_immune_qc.qc.foundation import build_foundation_summary


@pytest.mark.skipif(not os.environ.get("AML_DATA_ROOT"), reason="real data not configured")
def test_frozen_patient_reconciliation() -> None:
    summary = build_foundation_summary()
    assert summary["linkage"]["transplant_patients"] == 2820
    assert summary["linkage"]["lab_patients"] == 2819
    assert summary["linkage"]["report_patients"] == 2798
    assert summary["linkage"]["all_three"] == 2798
```

- [ ] **Step 7: Run the full synthetic test suite**

Run: `pytest aml_immune_qc/tests/unit aml_immune_qc/tests/integration/test_foundation_cli.py -v`  
Expected: all unit and synthetic integration tests pass.

- [ ] **Step 8: Run the frozen real-data reconciliation**

Run:

```bash
AML_DATA_ROOT='/mnt/f/博士课题/免疫重建 CYJ/2018-2025AML' \
  /home/reborn/.venvs/aml-qc-cpu/bin/pytest \
  aml_immune_qc/tests/integration/test_foundation_real_data.py -v
```

Expected: the test passes with 2,820 transplant patients, 2,819 lab patients, 2,798 immune-report patients, and 2,798 patients in all three sources.

- [ ] **Step 9: Generate the first frozen artifact set and verify source hashes**

Run:

```bash
AML_DATA_ROOT='/mnt/f/博士课题/免疫重建 CYJ/2018-2025AML' \
  /home/reborn/.venvs/aml-qc-cpu/bin/aml-immune-qc foundation-qc \
  --output aml_immune_qc/artifacts/foundation-r1
```

Expected: four aggregate JSON files are written; source hashes, sizes, and mtimes match before and after the run; no JSON contains a sensitive key.

- [ ] **Step 10: Commit the verified foundation**

```bash
git add aml_immune_qc
git commit -m "feat: deliver AML immune QC foundation"
```

## Phase Boundary

This plan ends after the privacy-safe foundation is verified on real data. Immune-report text extraction, clinical timeline construction, outcome/risk-set derivation, longitudinal modeling, and the Nature-tier publication evidence package are separate sub-projects with their own TDD plans. Their shared interfaces are the immutable source manifest, normalized identifier/date functions, aggregate schema profiles, and patient-linkage contract produced here.
