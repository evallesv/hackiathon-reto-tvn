"""Safety checks for isolated snapshot candidate generation."""

from pathlib import Path

import pytest

from hackiathon_reto_tvn.services.snapshot_builder import _validate_candidate_path


def test_snapshot_candidate_must_not_target_active_data(tmp_path: Path) -> None:
    repository_data = Path(__file__).resolve().parents[1] / "data"

    with pytest.raises(ValueError, match="dataset activo congelado"):
        _validate_candidate_path(repository_data)

    with pytest.raises(ValueError, match="dataset activo congelado"):
        _validate_candidate_path(repository_data / "candidates" / "candidate")


def test_snapshot_candidate_accepts_separate_directory(tmp_path: Path) -> None:
    candidate = _validate_candidate_path(tmp_path / "candidate")

    assert candidate == (tmp_path / "candidate").resolve()
