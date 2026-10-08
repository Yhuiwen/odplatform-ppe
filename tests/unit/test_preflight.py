"""Read-only final-demo preflight behavior."""

from __future__ import annotations

import hashlib
from importlib.metadata import PackageNotFoundError

from scripts.preflight import REQUIRED_PACKAGES, check_runtime


def _fixture(tmp_path):
    checkpoint = tmp_path / "models/checkpoints/EXP-001/best.pt"
    checkpoint.parent.mkdir(parents=True)
    checkpoint.write_bytes(b"checkpoint")
    inference = tmp_path / "configs/inference.yaml"
    inference.parent.mkdir(parents=True)
    inference.write_text("policy: cpu_only\nauto_download: false\n", encoding="utf-8")
    (tmp_path / "artifacts/events/snapshots").mkdir(parents=True)
    for relative in (
        "artifacts/validation/P4C-1/input/construction-workers-public-domain.jpg",
        "artifacts/validation/P4C-2/input/construction-workers-public-domain.mp4",
    ):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"asset")
    expected = {name.lower(): "1.0" for name in REQUIRED_PACKAGES}
    options = dict(
        package_lookup=lambda name: "1.0",
        python_version=(3, 12, 1),
        os_name="Windows",
        architecture="AMD64",
        expected_packages=expected.copy(),
        installed_packages=expected.copy(),
        checkpoint_sha256=hashlib.sha256(b"checkpoint").hexdigest(),
        checkpoint_size=len(b"checkpoint"),
        inference_sha256=hashlib.sha256(inference.read_bytes()).hexdigest(),
    )
    return options


def _failed(checks):
    return {label for passed, label in checks if not passed}


def test_preflight_pass_projection(tmp_path):
    options = _fixture(tmp_path)
    assert not _failed(check_runtime(tmp_path, **options))


def test_preflight_missing_checkpoint(tmp_path):
    options = _fixture(tmp_path)
    (tmp_path / "models/checkpoints/EXP-001/best.pt").unlink()
    assert "checkpoint exists" in _failed(check_runtime(tmp_path, **options))


def test_preflight_hash_mismatch(tmp_path):
    options = _fixture(tmp_path)
    options["checkpoint_sha256"] = "0" * 64
    assert "checkpoint SHA256" in _failed(check_runtime(tmp_path, **options))


def test_preflight_version_mismatch_and_missing_package(tmp_path):
    options = _fixture(tmp_path)
    options["package_lookup"] = lambda name: "2.0" if name == "torch" else "1.0"
    assert any("torch 2.0" in label for label in _failed(check_runtime(tmp_path, **options)))

    def missing(name):
        if name == "torch":
            raise PackageNotFoundError(name)
        return "1.0"

    options["package_lookup"] = missing
    assert any("torch MISSING" in label for label in _failed(check_runtime(tmp_path, **options)))


def test_preflight_unsupported_python(tmp_path):
    options = _fixture(tmp_path)
    options["python_version"] = (3, 13, 6)
    assert "Python 3.13.6" in _failed(check_runtime(tmp_path, **options))


def test_preflight_detects_lock_mismatch_and_missing_transitive_package(tmp_path):
    options = _fixture(tmp_path)
    options["expected_packages"]["another-package"] = "1.0"
    failures = _failed(check_runtime(tmp_path, **options))
    assert any("lock another-package MISSING" in label for label in failures)
    options["installed_packages"] = {
        **options["installed_packages"], "another-package": "2.0"
    }
    failures = _failed(check_runtime(tmp_path, **options))
    assert any("lock another-package 2.0" in label for label in failures)


def test_preflight_detects_lap_if_dynamically_added_outside_lock(tmp_path):
    options = _fixture(tmp_path)
    options["expected_packages"].pop("lap")
    failures = _failed(check_runtime(tmp_path, **options))
    assert any("lap 1.0 (expected UNLOCKED)" in label for label in failures)
    assert "critical runtime package lap installed but absent from lock" in failures
