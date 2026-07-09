# tiff2mp4

Turn a folder of TIFFs into an `.mp4`. Drop a folder, pick the playback speed, get a movie.

One TIFF = one frame, in filename order. No compositing, no Z-sweep — just the frames in the folder.
You can slice the **first N** frames to test quickly before encoding the whole folder.

## Setup (conda)

From the repo root:

```bash
conda env create -f environment.yml
conda activate tiff2mp4
```

### Windows: one-command setup + Desktop shortcut

In Windows PowerShell, from the repo root:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\Setup-Windows.ps1
```

This finds conda (even if it is not on PowerShell's PATH), creates the `tiff2mp4` environment if it
is missing, and adds a **"TIFFs to MP4"** shortcut to your Desktop that opens the app with no console
window. Double-click it, then drop a folder of TIFFs.

## Use it

GUI (drop a folder, set fps, optionally set "first N", Make MP4):

```bash
tiff2mp4-gui
```

Command line:

```bash
tiff2mp4 /path/to/frames                 # every TIFF -> /path/to/frames/movie.mp4
tiff2mp4 /path/to/frames --limit 20      # only the FIRST 20 TIFFs (quick test slice)
tiff2mp4 /path/to/frames --fps 10 -o out.mp4
```

Or from Python:

```python
from tiff2mp4 import tiffs_to_mp4
tiffs_to_mp4("/path/to/frames", "/path/to/movie.mp4", fps=5, limit=20)
```

## Notes

- Frames are ordered by filename. Name your TIFFs so they sort in the order you want them played.
- `--limit N` / "first N" encodes only the first N frames — a fast way to preview on his computer.
- Grayscale TIFFs are contrast-stretched (1st..99.8th percentile) to 8-bit; RGB TIFFs are used as-is.
- Encode runs on a background thread (GUI stays responsive) and streams one frame at a time, so memory
  stays flat regardless of how many TIFFs there are. H.264 via bundled `imageio-ffmpeg` (no system
  ffmpeg install).
