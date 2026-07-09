"""tiff2mp4 — turn a folder of TIFFs into an .mp4 (a tiny drop-a-folder GUI + a function)."""

from tiff2mp4.movie import list_tiffs, tiffs_to_mp4

__all__ = ["tiffs_to_mp4", "list_tiffs"]
__version__ = "0.1.0"
