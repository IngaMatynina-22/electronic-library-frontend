from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QLabel, QSizePolicy

from gui.ui.themes.tokens import LIGHT


class CoverLabel(QLabel):
    def __init__(self, width: int = 120, height: int = 170, parent=None) -> None:
        super().__init__(parent)
        self._w = width
        self._h = height
        self._bg = LIGHT.surface_alt
        self._fg = LIGHT.accent
        self._border = LIGHT.border
        self.setFixedSize(width, height)
        self.setMinimumSize(width, height)
        self.setMaximumSize(width, height)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setAlignment(Qt.AlignCenter)
        self.setScaledContents(False)
        # No objectName / QSS: stylesheets on QLabel break fixed geometry and cause overlap
        self._placeholder("?")

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(self._w, self._h)

    def minimumSizeHint(self) -> QSize:  # noqa: N802
        return QSize(self._w, self._h)

    def set_theme_colors(self, bg: str, fg: str, border: str | None = None) -> None:
        self._bg = bg
        self._fg = fg
        if border:
            self._border = border

    def set_cover(self, path: Path | str | None, title: str = "") -> None:
        if path:
            p = Path(path)
            if p.is_file():
                pix = QPixmap(str(p))
                if not pix.isNull():
                    canvas = QPixmap(self._w, self._h)
                    canvas.fill(QColor(self._bg))
                    scaled = pix.scaled(
                        self._w,
                        self._h,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation,
                    )
                    painter = QPainter(canvas)
                    x = (self._w - scaled.width()) // 2
                    y = (self._h - scaled.height()) // 2
                    painter.drawPixmap(x, y, scaled)
                    pen = QPen(QColor(self._border))
                    pen.setWidth(1)
                    painter.setPen(pen)
                    painter.setBrush(Qt.NoBrush)
                    painter.drawRect(0, 0, self._w - 1, self._h - 1)
                    painter.end()
                    self.setPixmap(canvas)
                    return
        self._placeholder(self._initials(title))

    def _initials(self, title: str) -> str:
        parts = [p for p in (title or "").split() if p]
        if not parts:
            return "?"
        if len(parts) == 1:
            return parts[0][:2].upper()
        return (parts[0][0] + parts[1][0]).upper()

    def _placeholder(self, text: str) -> None:
        pix = QPixmap(self._w, self._h)
        pix.fill(QColor(self._bg))
        painter = QPainter(pix)
        painter.setPen(QColor(self._fg))
        font = QFont("Georgia", 18, QFont.DemiBold)
        painter.setFont(font)
        painter.drawText(pix.rect(), Qt.AlignCenter, text[:3])
        pen = QPen(QColor(self._border))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(0, 0, self._w - 1, self._h - 1)
        painter.end()
        self.setPixmap(pix)
