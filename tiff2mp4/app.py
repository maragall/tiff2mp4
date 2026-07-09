"""A tiny GUI: drop a folder of TIFFs, get an .mp4.

Drag a folder onto the window (or Browse), pick the playback fps, click Make MP4. The encode runs on
a background thread so the window never freezes. That is the whole app — no compositing, no z-sweep.
"""

from __future__ import annotations

import os
import sys

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication, QFileDialog, QHBoxLayout, QLabel, QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

from tiff2mp4.movie import list_tiffs, tiffs_to_mp4

_BG, _FG, _ACCENT = "#0b0e14", "#e6edf3", "#58a6ff"
_BTN = ("QPushButton{background:#131824;color:#e6edf3;border:1px solid #2b3550;border-radius:8px;"
        "padding:8px 14px;font-weight:700;} QPushButton:hover{border-color:#58a6ff;}"
        "QPushButton:disabled{color:#57606a;}")


class _Worker(QThread):
    progress = pyqtSignal(int, int, str)
    done = pyqtSignal(str, int)
    failed = pyqtSignal(str)

    def __init__(self, folder, out, fps):
        super().__init__()
        self._folder, self._out, self._fps = folder, out, fps

    def run(self):
        try:
            p, n = tiffs_to_mp4(self._folder, self._out, self._fps,
                                progress=lambda i, t, f: self.progress.emit(i, t, f))
            self.done.emit(p, n)
        except Exception as e:
            self.failed.emit(f"{type(e).__name__}: {e}")


class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TIFFs → MP4")
        self.resize(560, 360)
        self.setAcceptDrops(True)
        self.setStyleSheet(f"QWidget{{background:{_BG};color:{_FG};font-size:13px;}}")
        self._folder = None
        self._worker = None

        v = QVBoxLayout(self)
        v.setContentsMargins(18, 18, 18, 18)
        v.setSpacing(12)

        self._drop = QLabel("Drop a folder of TIFFs here\n\n(or use Browse below)")
        self._drop.setAlignment(Qt.AlignCenter)
        self._drop.setStyleSheet("border:2px dashed #2b3550;border-radius:12px;color:#8b98ad;"
                                 "font-size:15px;padding:40px;")
        v.addWidget(self._drop, 1)

        row = QHBoxLayout()
        browse = QPushButton("Browse…"); browse.setStyleSheet(_BTN); browse.clicked.connect(self._browse)
        row.addWidget(browse)
        row.addWidget(QLabel("fps"))
        self._fps = QSpinBox(); self._fps.setRange(1, 60); self._fps.setValue(5)
        self._fps.setStyleSheet("QSpinBox{background:#0d1420;border:1px solid #2b3550;border-radius:6px;padding:4px 8px;}")
        row.addWidget(self._fps)
        row.addStretch(1)
        self._make = QPushButton("● Make MP4"); self._make.setStyleSheet(_BTN)
        self._make.setEnabled(False); self._make.clicked.connect(self._run)
        row.addWidget(self._make)
        v.addLayout(row)

        self._status = QLabel("Drop a folder to begin.")
        self._status.setWordWrap(True); self._status.setStyleSheet("color:#8b98ad;")
        v.addWidget(self._status)

    # -- folder selection --
    def _set_folder(self, folder):
        self._folder = folder
        n = len(list_tiffs(folder))
        self._drop.setText(f"{folder}\n\n{n} TIFF(s) found")
        self._make.setEnabled(n > 0)
        self._status.setText("Ready — click Make MP4." if n else "No .tif/.tiff files in that folder.")

    def _browse(self):
        d = QFileDialog.getExistingDirectory(self, "Choose a folder of TIFFs")
        if d:
            self._set_folder(d)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        for url in e.mimeData().urls():
            p = url.toLocalFile()
            if os.path.isdir(p):
                self._set_folder(p)
                return
            if os.path.isfile(p):                 # dropped a file -> use its folder
                self._set_folder(os.path.dirname(p))
                return

    # -- encode --
    def _run(self):
        if not self._folder or (self._worker and self._worker.isRunning()):
            return
        out, _ = QFileDialog.getSaveFileName(self, "Save movie as",
                                             os.path.join(self._folder, "movie.mp4"), "MP4 (*.mp4)")
        if not out:
            return
        self._make.setEnabled(False)
        self._worker = _Worker(self._folder, out, self._fps.value())
        self._worker.progress.connect(lambda i, t, f: self._status.setText(f"encoding {i}/{t} · {f}"))
        self._worker.done.connect(lambda p, n: (self._status.setText(f"✓ wrote {n} frames → {p}"),
                                                self._make.setEnabled(True)))
        self._worker.failed.connect(lambda m: (self._status.setText(f"failed: {m}"),
                                               self._make.setEnabled(True)))
        self._worker.start()

    def closeEvent(self, e):
        if self._worker and self._worker.isRunning():
            self._worker.wait(2000)
        super().closeEvent(e)


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
