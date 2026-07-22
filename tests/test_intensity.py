"""Tests for the shared (stack-wide) intensity window."""

import numpy as np

from tiff2mp4.movie import _as_frame, _sample_indices, intensity_window


def _plane(level):
    # 64x64 gradient sitting at a given brightness level
    return (np.arange(64 * 64, dtype=np.uint16).reshape(64, 64) % 100 + level).astype(np.uint16)


def test_intensity_window_pools_all_planes():
    lo, hi = intensity_window([_plane(0), _plane(1000)])
    assert lo < 100 and hi > 1000


def test_shared_window_preserves_relative_brightness_between_frames():
    dim, bright = _plane(0), _plane(1000)
    lo, hi = intensity_window([dim, bright])
    assert _as_frame(dim, lo, hi).mean() < _as_frame(bright, lo, hi).mean()


def test_flat_plane_does_not_divide_by_zero():
    flat = np.full((8, 8), 7, dtype=np.uint16)
    lo, hi = intensity_window([flat])
    assert hi > lo
    assert _as_frame(flat, lo, hi).dtype == np.uint8


def test_sample_indices_is_bounded_and_spans_the_stack():
    idx = _sample_indices(149, 16)
    assert len(idx) == 16
    assert idx[0] == 0 and idx[-1] == 148
    assert idx == sorted(set(idx))


def test_sample_indices_handles_stacks_smaller_than_the_sample():
    assert _sample_indices(3, 16) == [0, 1, 2]
