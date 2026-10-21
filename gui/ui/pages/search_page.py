from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from gui.ui.utils.errors import user_message
from gui.ui.workers.base import run_in_thread


class SearchPage(QWidget):
    open_book = Signal(int)
    open_at = Signal(int, object)
    toast = Signal(str, str)

    def __init__(self, container, parent=None) -> None:
        super().__init__(parent)
        self.container = container
        self._query = ""
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(350)
        self._timer.timeout.connect(self._run_search)
        self._token = 0

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        title = QLabel("Повнотекстовий пошук")
        title.setObjectName("PageTitle")
        root.addWidget(title)
        self.state = QLabel("Введіть запит у полі пошуку зверху.")
        self.state.setObjectName("MutedLabel")
        root.addWidget(self.state)
        self.list = QListWidget()
        self.list.itemActivated.connect(self._activate)
        root.addWidget(self.list, 1)

    def set_query(self, query: str) -> None:
        self._query = query.strip()
        if not self._query:
            self.list.clear()
            self.state.setText("Введіть запит у полі пошуку зверху.")
            return
        self.state.setText("Пошук…")
        self._timer.start()

    def _run_search(self) -> None:
        query = self._query
        if not query:
            return
        self._token += 1
        token = self._token

        def work():
            return self.container.search.search_fulltext(query, limit=80)

        run_in_thread(
            work,
            on_finished=lambda hits, t=token, q=query: self._done(t, q, hits),
            on_error=lambda exc, t=token: self._err(t, exc),
        )

    def _done(self, token: int, query: str, hits) -> None:
        if token != self._token or query != self._query:
            return
        self.list.clear()
        if not hits:
            self.state.setText("Збігів немає.")
            return
        self.state.setText(f"Знайдено: {len(hits)}")
        groups: dict[str, list] = {}
        labels = {
            "book": "Книги",
            "content": "Текст книг",
            "quote": "Цитати",
            "note": "Нотатки",
        }
        for h in hits:
            groups.setdefault(h.source, []).append(h)
        for source, items in groups.items():
            header = QListWidgetItem(labels.get(source, source))
            header.setFlags(Qt.NoItemFlags)
            font = header.font()
            font.setBold(True)
            header.setFont(font)
            self.list.addItem(header)
            for h in items:
                text = f"{h.book_title or 'Книга'}"
                if h.page_or_chapter:
                    text += f" · {h.page_or_chapter}"
                text += f"\n{h.snippet}"
                item = QListWidgetItem(text)
                item.setData(Qt.UserRole, h)
                self.list.addItem(item)

    def _err(self, token: int, exc) -> None:
        if token != self._token:
            return
        self.state.setText("Помилка пошуку.")
        self.toast.emit(user_message(exc), "error")

    def _activate(self, item: QListWidgetItem) -> None:
        hit = item.data(Qt.UserRole)
        if not hit:
            return
        self.open_book.emit(hit.book_id)
