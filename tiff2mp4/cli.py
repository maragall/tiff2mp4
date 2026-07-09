"""Headless: make an .mp4 from a folder of TIFFs, from the command line.

    tiff2mp4 <folder>                       # every TIFF -> <folder>/movie.mp4
    tiff2mp4 <folder> --limit 20            # only the first 20 TIFFs (quick test slice)
    tiff2mp4 <folder> --fps 10 -o out.mp4
"""

from __future__ import annotations

import argparse
import os
import sys

from tiff2mp4.movie import list_tiffs, tiffs_to_mp4


def main(argv=None):
    ap = argparse.ArgumentParser(prog="tiff2mp4", description="Turn a folder of TIFFs into an .mp4.")
    ap.add_argument("folder", help="folder containing the .tif/.tiff frames")
    ap.add_argument("-o", "--output", default=None, help="output .mp4 (default: <folder>/movie.mp4)")
    ap.add_argument("--fps", type=int, default=5, help="playback frames per second (default 5)")
    ap.add_argument("--limit", type=int, default=None,
                    help="encode only the FIRST N TIFFs (a quick test slice; default: all)")
    args = ap.parse_args(argv)

    folder = os.path.expanduser(args.folder)
    if not os.path.isdir(folder):
        ap.error(f"not a folder: {folder}")
    out = os.path.expanduser(args.output) if args.output else os.path.join(folder, "movie.mp4")
    total = len(list_tiffs(folder))
    n_use = min(total, args.limit) if args.limit else total
    print(f"encoding {n_use} of {total} TIFF(s) at {args.fps} fps -> {out}")

    def _progress(i, t, name):
        print(f"\r  {i}/{t}  {name}", end="", flush=True)

    path, n = tiffs_to_mp4(folder, out, fps=args.fps, limit=args.limit, progress=_progress)
    print(f"\ndone: wrote {n} frames -> {path}")


if __name__ == "__main__":
    sys.exit(main())
