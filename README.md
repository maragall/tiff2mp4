# tiff2mp4

Turn a folder of TIFFs into an `.mp4`. Drop a folder, pick the playback speed, get a movie.

This is the post-hoc "make a movie out of the frames" step: your microscope's Simple Recording saves
each frame as an individual image; this assembles those frames (one TIFF = one frame, in filename
order) into a video. It does not composite channels or sweep Z — just the frames in the folder.

## Setup (conda)

```bash
conda env create -f environment.yml
conda activate tiff2mp4
```

## Use it

GUI (drop a folder, set fps, Make MP4):

```bash
python -m tiff2mp4
```

Or from Python:

```python
from tiff2mp4 import tiffs_to_mp4
tiffs_to_mp4("/path/to/frames", "/path/to/movie.mp4", fps=5)
```

## Notes

- Frames are ordered by filename. Name your TIFFs so they sort in the order you want them played.
- Grayscale TIFFs are contrast-stretched (1st..99.8th percentile) to 8-bit for display; RGB TIFFs
  are used as-is.
- The encode runs on a background thread, so the window stays responsive; memory stays at one frame
  regardless of how many TIFFs there are (frames are streamed to the encoder).
- The H.264 encoder is bundled via `imageio-ffmpeg` — no system ffmpeg install required.
