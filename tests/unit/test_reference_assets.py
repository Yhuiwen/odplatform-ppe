import hashlib
import re

from utils.paths import PROJECT_ROOT


REFERENCE_DOC = PROJECT_ROOT / "docs" / "09_REFERENCE_ASSETS.md"
CHARTER_DOC = PROJECT_ROOT / "docs" / "00_PROJECT_CHARTER.md"
EXPECTED_LOCKED_CHARTER_SHA256 = (
    "9e48d2d5b3960b82cfbe5a93ae67c0ac035702bfd1a022865763fc19fe6d464c"
)

REQUIRED_REFERENCE_FIELDS = [
    "Asset ID",
    "Asset Name",
    "Provider",
    "Original Filename",
    "SHA-256",
    "Asset Type",
    "License / Permission Status",
    "Repository Inclusion",
    "Purpose",
    "Allowed Usage",
    "Forbidden Usage",
    "Known Metadata",
    "Verification Status",
    "Notes",
]

FORBIDDEN_REFERENCE_FILENAMES = {
    "yolo_web_v3.zip",
    "best.pt",
    "history.db",
}

SECRET_ASSIGNMENT = re.compile(
    r"(?i)(api[_-]?key|access[_-]?token|secret[_-]?key|client[_-]?secret)"
    r"\s*[:=]\s*[\"'][^\"']{12,}[\"']"
)
MACHINE_ABSOLUTE_PATH = re.compile(
    r"(?i)(?:[a-z]:[\\/]|\\\\[^\\\s]+\\[^\\\s]+|/(?:users|home|mnt|opt|var)/)"
)

TEXT_FILENAMES = {
    ".gitignore",
    "AGENTS.md",
    "README.md",
    "pyproject.toml",
    "requirements.txt",
}
TEXT_SUFFIXES = {".py", ".md", ".yaml", ".yml", ".toml", ".txt", ".sql"}


def _normalize_charter_for_lock_check(text: str) -> str:
    normalized_lines: list[str] = []
    for line in text.splitlines():
        if re.match(r"^\| (?:M|E)-\d{3} \|", line):
            cells = line.split("|")
            cells[-2] = " STATUS "
            line = "|".join(cells)
        normalized_lines.append(line)
    return "\n".join(normalized_lines)


def test_reference_asset_register_exists_with_required_fields() -> None:
    assert REFERENCE_DOC.is_file()
    content = REFERENCE_DOC.read_text(encoding="utf-8")
    assert "REF-001" in content
    assert "REF-002" in content
    assert "REFERENCE ONLY" in content
    assert "BASELINE / REFERENCE" in content
    assert "POTENTIAL SEMANTIC MAPPING — UNVERIFIED" in content
    for field in REQUIRED_REFERENCE_FIELDS:
        assert field in content, field


def test_agents_requires_reference_asset_register_before_current_phase() -> None:
    agents = (PROJECT_ROOT / "AGENTS.md").read_text(encoding="utf-8")
    position_open_source = agents.index("docs/07_OPEN_SOURCE_USAGE.md")
    position_reference = agents.index("docs/09_REFERENCE_ASSETS.md")
    position_current_phase = agents.index("The current phase document")
    assert position_open_source < position_reference < position_current_phase


def test_teacher_reference_assets_are_not_in_repository() -> None:
    found = [
        path.relative_to(PROJECT_ROOT).as_posix()
        for path in PROJECT_ROOT.rglob("*")
        if path.is_file() and path.name.lower() in FORBIDDEN_REFERENCE_FILENAMES
    ]
    assert found == []


def test_reference_assets_are_explicitly_ignored() -> None:
    ignored = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")
    for filename in FORBIDDEN_REFERENCE_FILENAMES:
        assert filename in ignored


def test_reference_asset_register_has_no_machine_absolute_paths() -> None:
    content = REFERENCE_DOC.read_text(encoding="utf-8")
    assert MACHINE_ABSOLUTE_PATH.search(content) is None


def test_no_obvious_api_key_assignment_is_present() -> None:
    findings: list[str] = []
    for path in PROJECT_ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative_parts = path.relative_to(PROJECT_ROOT).parts
        if any(
            part in {".git", ".pytest_cache", "__pycache__"}
            for part in relative_parts
        ):
            continue
        if path.name not in TEXT_FILENAMES and path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")
        if SECRET_ASSIGNMENT.search(content):
            findings.append(path.relative_to(PROJECT_ROOT).as_posix())
    assert findings == []


def test_charter_locked_body_hash_is_unchanged() -> None:
    charter = CHARTER_DOC.read_text(encoding="utf-8")
    normalized = _normalize_charter_for_lock_check(charter)
    actual = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    assert actual == EXPECTED_LOCKED_CHARTER_SHA256
