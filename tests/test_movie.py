"""Tests for frame ordering in movie.list_tiffs."""

import os

from tiff2mp4.movie import list_tiffs


def _make(folder, names):
    for n in names:
        open(os.path.join(folder, n), "wb").close()


def _prefixes(files):
    return [os.path.basename(f).split("_")[0] for f in files]


def test_unpadded_numeric_prefixes_sort_in_frame_order(tmp_path):
    _make(tmp_path, [f"{i}_BF_LED_matrix_full.tiff" for i in range(1, 150)])
    assert _prefixes(list_tiffs(str(tmp_path))) == [str(i) for i in range(1, 150)]


def test_zero_padded_prefixes_keep_working(tmp_path):
    _make(tmp_path, [f"{i:04d}_BF_LED_matrix_full.tiff" for i in range(1, 150)])
    assert _prefixes(list_tiffs(str(tmp_path))) == [f"{i:04d}" for i in range(1, 150)]


def test_mixed_extensions_still_deduped_and_ordered(tmp_path):
    _make(tmp_path, ["2_a.tif", "10_a.tiff", "1_a.TIFF"])
    assert _prefixes(list_tiffs(str(tmp_path))) == ["1", "2", "10"]
