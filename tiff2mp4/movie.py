"""Turn a folder of TIFFs into an .mp4.

Deliberately simple: ONE frame per TIFF, in filename order. No compositing of channels, no z-sweep,
no re-projection — just the frames that are already in the folder, assembled into a movie. This is
the "turn the frames the microscope saved into a movie" step, done post-hoc.

Streamed to the ffmpeg writer one frame at a time (imageio-ffmpeg bundles the encoder — no system
ffmpeg needed), so memory stays at a single frame regardless of how many TIFFs there are.
"""

from __future__ import annotations

import glob
import os

import numpy as np
import tifffile


def list_tiffs(folder: str) -> list:
    """Every .tif/.tiff in *folder*, sorted by name (the frame order)."""
    files: list = []
    for ext in ("*.tif", "*.tiff", "*.TIF", "*.TIFF"):
        files += glob.glob(os.path.join(folder, ext))
    return sorted(set(files))


def _to_uint8(plane: "np.ndarray") -> "np.ndarray":
    """Contrast-stretch a grayscale plane to 8-bit (1st..99.8th percentile) for display encoding."""
    a = plane.astype(np.float32)
    lo, hi = float(np.percentile(a, 1.0)), float(np.percentile(a, 99.8))
    if hi <= lo:
        hi = lo + 1.0
    return (np.clip((a - lo) / (hi - lo), 0.0, 1.0) * 255).astype(np.uint8)


def _as_frame(img: "np.ndarray") -> "np.ndarray":
    """Coerce one TIFF's pixels into an (H, W, 3) uint8 RGB frame."""
    if img.ndim == 3 and img.shape[-1] in (3, 4):          # already colour
        rgb = img[..., :3]
        return rgb.astype(np.uint8) if rgb.dtype == np.uint8 else _to_uint8(rgb.mean(axis=-1))[:, :, None].repeat(3, 2)
    if img.ndim == 3:                                      # a stack/multi-page -> take the first page
        img = img[0]
    gray = _to_uint8(img)
    return np.repeat(gray[:, :, None], 3, axis=2)


def tiffs_to_mp4(folder: str, out_path, fps: int = 5, limit=None, progress=None):
    """Encode the TIFFs in *folder* (name order) into an H.264 ``.mp4`` at *fps*.

    *limit*: if given (> 0), only the FIRST N TIFFs are used — a quick slice to test on a few frames
    without encoding the whole folder. ``progress(i, total, name)`` is called per frame if given.
    Returns (out_path, n_frames). Raises ValueError when the folder has no TIFFs."""
    import imageio.v2 as imageio

    files = list_tiffs(folder)
    if not files:
        raise ValueError(f"no .tif/.tiff files found in {folder}")
    if limit is not None and int(limit) > 0:
        files = files[: int(limit)]
    writer = imageio.get_writer(str(out_path), fps=max(1, int(fps)), codec="libx264",
                                macro_block_size=None, quality=8)
    try:
        for i, f in enumerate(files, 1):
            writer.append_data(np.ascontiguousarray(_as_frame(tifffile.imread(f)), dtype=np.uint8))
            if progress:
                progress(i, len(files), os.path.basename(f))
    finally:
        writer.close()
    return str(out_path), len(files)
