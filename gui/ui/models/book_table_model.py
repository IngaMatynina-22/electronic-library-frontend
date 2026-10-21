from __future__ import annotations

from typing import Any, Sequence

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from gui.ui.utils.formatters import format_authors, format_progress, status_label

HEADERS = ["Назва", "Автор", "Жанр", "Статус", "Прогрес", "Рейтинг", "Додано"]


class BookTableModel(QAbstractTableModel):
    def __init__(self, books: Sequence[Any] | None = None, parent=None) -> None:
        super().__init__(parent)
        self._books: list[Any] = list(books or [])

    def rowCount(self, parent=QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self._books)

    def columnCount(self, parent=QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(HEADERS)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):  # noqa: N802
        if not index.isValid() or not (0 <= index.row() < len(self._books)):
            return None
        book = self._books[index.row()]
        col = index.column()
        if role == Qt.DisplayRole:
            if col == 0:
                return book.title
            if col == 1:
                return format_authors(book.authors)
            if col == 2:
                genres = getattr(book, "genres", None) or []
                return ", ".join(g.name for g in genres) if genres else "—"
            if col == 3:
                return status_label(book.status)
            if col == 4:
                return format_progress(book.progress)
            if col == 5:
                return str(book.rating) if book.rating else "—"
            if col == 6:
                dt = book.created_at or book.last_opened_at
                return dt.strftime("%Y-%m-%d") if dt else "—"
        if role == Qt.UserRole:
            return book
        if role == Qt.ToolTipRole and col == 0:
            return book.title
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):  # noqa: N802
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return HEADERS[section]
        return None

    def flags(self, index):  # noqa: N802
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def set_books(self, books: Sequence[Any]) -> None:
        self.beginResetModel()
        self._books = list(books)
        self.endResetModel()

    def book_at(self, row: int):
        if 0 <= row < len(self._books):
            return self._books[row]
        return None

    def books(self) -> list[Any]:
        return list(self._books)
