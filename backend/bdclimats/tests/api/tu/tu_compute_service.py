import pytest

from api.services.compute import ComputeError, compute


def test_compute_avg():
    assert compute("avg", [1.0, 3.0]) == 2.0


def test_compute_sum():
    assert compute("sum", [1.0, 3.0]) == 4.0


def test_compute_min():
    assert compute("min", [1.0, 3.0]) == 1.0


def test_compute_max():
    assert compute("max", [1.0, 3.0]) == 3.0


def test_compute_rejects_empty_values():
    with pytest.raises(ComputeError):
        compute("avg", [])


def test_compute_rejects_unknown_operation():
    with pytest.raises(ComputeError):
        compute("median", [1.0, 2.0])
