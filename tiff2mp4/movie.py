"""Turn a folder of TIFFs into an .mp4.

Deliberately simple: ONE frame per TIFF, in filename order. No compositing of channels, no z-sweep,
no re-projection — just the frames that are already in the folder, assembled into a movie. This is
the "turn the frames the microscope saved into a movie" step, done post-hoc.

Streamed to the ffmpeg writer one frame at a time (imageio-ffmpeg bundles the encoder — no system
ffmpeg needed), so memory stays at a single frame regardless of how many TIFFs there are.

Contrast is a SINGLE display window shared by every frame, estimated once from a sample of the
stack. Per-frame windowing would rescale each frame to its own contrast and cancel out the real
intensity changes over time that these movies are made to show.
"""

from __future__ import annotations

import glob
import os
import re

import numpy as np
import tifffile

_DIGIT_RUN = re.compile(r"(\d+)")

_WINDOW_SAMPLE = 16   # frames sampled across the stack to estimate the shared display window


def _natural_key(path: str):
    # unpadded frame numbers must compare numerically: 2_x.tiff before 10_x.tiff
    return [int(part) if part.isdigit() else part for part in _DIGIT_RUN.split(os.path.basename(path))]


def default_output(folder: str) -> str:
    """Default .mp4 path for *folder*: in the PARENT directory, named after the folder.

    Writing next to the folder (not inside it) keeps the movie out of the acquisition data, and
    naming it after the folder keeps siblings from colliding on a shared parent."""
    folder = os.path.abspath(folder)
    name = os.path.basename(folder) or "movie"
    return os.path.join(os.path.dirname(folder), name + ".mp4")


def list_tiffs(folder: str) -> list:
    """Every .tif/.tiff in *folder*, naturally sorted by name (the frame order)."""
    files: list = []
    for ext in ("*.tif", "*.tiff", "*.TIF", "*.TIFF"):
        files += glob.glob(os.path.join(folder, ext))
    return sorted(set(files), key=_natural_key)


def _sample_indices(n: int, k: int = _WINDOW_SAMPLE) -> list:
    """Up to *k* evenly spaced indices spanning 0..n-1 (always including both ends)."""
    if n <= k:
        return list(range(n))
    return sorted({int(round(i * (n - 1) / (k - 1))) for i in range(k)})


def intensity_window(planes) -> tuple:
    """The ONE (lo, hi) display window to apply to every frame, pooled over *planes*.

    A window computed per-frame would rescale each frame to its own contrast, cancelling out the
    real intensity changes over time that these movies exist to show. One shared window keeps
    frame-to-frame brightness comparable."""
    los, his = [], []
    for p in planes:
        a = np.asarray(p, dtype=np.float32)
        los.append(float(np.percentile(a, 1.0)))
        his.append(float(np.percentile(a, 99.8)))
    lo, hi = (min(los), max(his)) if los else (0.0, 1.0)
    if hi <= lo:
        hi = lo + 1.0
    return lo, hi


def _to_uint8(plane: "np.ndarray", lo: float, hi: float) -> "np.ndarray":
    """Map a grayscale plane to 8-bit through the shared display window *lo*..*hi*."""
    a = plane.astype(np.float32)
    return (np.clip((a - lo) / (hi - lo), 0.0, 1.0) * 255).astype(np.uint8)


def _as_frame(img: "np.ndarray", lo: float, hi: float) -> "np.ndarray":
    """Coerce one TIFF's pixels into an (H, W, 3) uint8 RGB frame using the shared window."""
    if img.ndim == 3 and img.shape[-1] in (3, 4):          # already colour
        rgb = img[..., :3]
        if rgb.dtype == np.uint8:
            return rgb.astype(np.uint8)
        return _to_uint8(rgb.mean(axis=-1), lo, hi)[:, :, None].repeat(3, 2)
    if img.ndim == 3:                                      # a stack/multi-page -> take the first page
        img = img[0]
    gray = _to_uint8(img, lo, hi)
    return np.repeat(gray[:, :, None], 3, axis=2)


def _plane_of(img: "np.ndarray") -> "np.ndarray":
    """The single grayscale plane *img* contributes to the window estimate."""
    if img.ndim == 3 and img.shape[-1] in (3, 4):
        return img[..., :3].mean(axis=-1)
    return img[0] if img.ndim == 3 else img


def stack_window(files) -> tuple:
    """Shared display window for *files*, estimated from an evenly spaced sample of the stack.

    Sampling (rather than reading every frame twice) keeps the cost bounded no matter how many
    TIFFs there are, while still spanning the whole acquisition."""
    sample = [_plane_of(tifffile.imread(files[i])) for i in _sample_indices(len(files))]
    return intensity_window(sample)


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
    lo, hi = stack_window(files)
    print(f"[tiff2mp4] shared display window: {lo:.1f}..{hi:.1f} (same for every frame)", flush=True)
    writer = imageio.get_writer(str(out_path), fps=max(1, int(fps)), codec="libx264",
                                macro_block_size=None, quality=8)
    try:
        for i, f in enumerate(files, 1):
            frame = _as_frame(tifffile.imread(f), lo, hi)
            writer.append_data(np.ascontiguousarray(frame, dtype=np.uint8))
            if progress:
                progress(i, len(files), os.path.basename(f))
    finally:
        writer.close()
    return str(out_path), len(files)
