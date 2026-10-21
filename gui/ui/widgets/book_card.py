"""Reusable book cover card for library and org grids."""

from __future__ import annotations

from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QFrame, QLabel, QProgressBar, QSizePolicy, QVBoxLayout, QWidget

from gui.ui.utils.formatters import format_authors, format_progress, status_label
from gui.ui.widgets.cover_label import CoverLabel

CARD_W = 150
CARD_H = 268
COVER_W = 122
COVER_H = 148


class BookCard(QFrame):
    def __init__(self, book, container, parent=None) -> None:
        super().__init__(parent)
        self.book = book
        self.setObjectName("BookCard")
        self.setFixedSize(CARD_W, CARD_H)
        self.setProperty("selected", False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 8)
        layout.setSpacing(8)

        self.cover = CoverLabel(COVER_W, COVER_H)
        path = None
        if book.cover_path:
            path = container.path_resolver.resolve(book.cover_path)
        self.cover.set_cover(path, book.title or "")
        layout.addWidget(self.cover, 0, Qt.AlignHCenter | Qt.AlignTop)

        meta = QFrame()
        meta.setObjectName("BookCardMeta")
        meta.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        meta_l = QVBoxLayout(meta)
        meta_l.setContentsMargins(0, 0, 0, 0)
        meta_l.setSpacing(3)

        self.title = QLabel()
        self.title.setObjectName("BookCardTitle")
        self.title.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.title.setFixedHeight(22)
        self.title.setWordWrap(False)
        title_text = book.title or "Без назви"
        self.title.setToolTip(title_text)
        self.title.setText(self.title.fontMetrics().elidedText(title_text, Qt.ElideRight, COVER_W))
        meta_l.addWidget(self.title)

        self.author = QLabel()
        self.author.setObjectName("MutedLabel")
        self.author.setAlignment(Qt.AlignHCenter)
        self.author.setFixedHeight(18)
        self.author.setWordWrap(False)
        author_text = format_authors(book.authors)
        self.author.setText(
            self.author.fontMetrics().elidedText(author_text, Qt.ElideRight, COVER_W)
        )
        meta_l.addWidget(self.author)

        self.status = QLabel(f"{status_label(book.status)} · {format_progress(book.progress)}")
        self.status.setObjectName("StatusBadge")
        self.status.setAlignment(Qt.AlignHCenter)
        self.status.setFixedHeight(16)
        meta_l.addWidget(self.status)

        bar = QProgressBar()
        bar.setRange(0, 100)
        pct = 0
        if book.progress and getattr(book.progress, "progress_percent", None) is not None:
            pct = int(round(float(book.progress.progress_percent)))
        bar.setValue(pct)
        bar.setTextVisible(False)
        bar.setFixedHeight(5)
        meta_l.addWidget(bar)

        layout.addWidget(meta, 0, Qt.AlignTop)

    def set_selected(self, selected: bool) -> None:
        self.setProperty("selected", selected)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    @staticmethod
    def grid_size() -> QSize:
        return QSize(CARD_W + 16, CARD_H + 16)

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(CARD_W, CARD_H)
