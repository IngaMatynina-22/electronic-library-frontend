from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from gui.ui.utils.errors import user_message


class MaterialsPage(QWidget):
    open_book = Signal(int)
    open_at = Signal(int, object)
    toast = Signal(str, str)

    def __init__(self, container, parent=None) -> None:
        super().__init__(parent)
        self.container = container
        self._mode = "quotes"

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        title = QLabel("Особисті матеріали")
        title.setObjectName("PageTitle")
        root.addWidget(title)

        row = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Пошук…")
        self.search.textChanged.connect(self.reload)
        refresh = QPushButton("Оновити")
        refresh.clicked.connect(self.reload)
        open_btn = QPushButton("Відкрити в книзі")
        open_btn.setObjectName("PrimaryButton")
        open_btn.clicked.connect(self._open_current)
        delete_btn = QPushButton("Видалити")
        delete_btn.setObjectName("DangerButton")
        delete_btn.clicked.connect(self._delete)
        row.addWidget(self.search, 1)
        row.addWidget(refresh)
        row.addWidget(open_btn)
        row.addWidget(delete_btn)
        root.addLayout(row)

        self.tabs = QTabWidget()
        self.quotes_list = QListWidget()
        self.notes_list = QListWidget()
        self.bookmarks_list = QListWidget()
        self.reviews_list = QListWidget()
        for lst in (self.quotes_list, self.notes_list, self.bookmarks_list, self.reviews_list):
            lst.itemDoubleClicked.connect(self._open_item)
        self.tabs.addTab(self.quotes_list, "Цитати")
        self.tabs.addTab(self.notes_list, "Нотатки")
        self.tabs.addTab(self.bookmarks_list, "Закладки")
        self.tabs.addTab(self.reviews_list, "Відгуки")
        self.tabs.currentChanged.connect(self._tab_changed)
        root.addWidget(self.tabs, 1)

    def show_mode(self, mode: str) -> None:
        mapping = {"quotes": 0, "notes": 1, "bookmarks": 2, "reviews": 3}
        self.tabs.setCurrentIndex(mapping.get(mode, 0))
        self.reload()

    def _tab_changed(self, index: int) -> None:
        self._mode = ["quotes", "notes", "bookmarks", "reviews"][index]
        self.reload()

    def reload(self) -> None:
        q = self.search.text().strip()
        try:
            if self._mode == "quotes":
                items = self.container.quotes.search(q) if q else self.container.quotes.list()
                self.quotes_list.clear()
                for item in items:
                    pos = item.page_number or (item.chapter_title or "")
                    text = (
                        f"{item.book_title or 'Книга'}"
                        + (f" · {pos}" if pos else "")
                        + f"\n{item.text[:220]}"
                    )
                    it = QListWidgetItem(text)
                    it.setData(Qt.UserRole, item)
                    self.quotes_list.addItem(it)
            elif self._mode == "notes":
                items = self.container.notes.search(q) if q else self.container.notes.list()
                self.notes_list.clear()
                for item in items:
                    text = f"Книга #{item.book_id} · {item.title or ''}\n{item.content[:220]}"
                    it = QListWidgetItem(text)
                    it.setData(Qt.UserRole, item)
                    self.notes_list.addItem(it)
            elif self._mode == "bookmarks":
                books = {b.id: b for b in self.container.books.list()}
                self.bookmarks_list.clear()
                for book in books.values():
                    for bm in self.container.bookmarks.list(book.id):
                        label = f"{book.title} · {bm.title or 'Закладка'}"
                        if q and q.lower() not in label.lower():
                            continue
                        it = QListWidgetItem(label)
                        it.setData(Qt.UserRole, (bm, book.id))
                        self.bookmarks_list.addItem(it)
            else:
                self.reviews_list.clear()
                for rev in self.container.reviews.list():
                    book = None
                    try:
                        book = self.container.books.get(rev.book_id)
                    except Exception:  # noqa: BLE001
                        pass
                    title = book.title if book else f"Книга #{rev.book_id}"
                    label = f"{title}"
                    if rev.rating:
                        label += f" · ★ {rev.rating}"
                    label += f"\n{(rev.content or '')[:220]}"
                    if q and q.lower() not in label.lower():
                        continue
                    it = QListWidgetItem(label)
                    it.setData(Qt.UserRole, rev)
                    self.reviews_list.addItem(it)
        except Exception as exc:  # noqa: BLE001
            self.toast.emit(user_message(exc), "error")

    def _current_list(self) -> QListWidget:
        return [
            self.quotes_list,
            self.notes_list,
            self.bookmarks_list,
            self.reviews_list,
        ][self.tabs.currentIndex()]

    def _open_current(self) -> None:
        item = self._current_list().currentItem()
        if item:
            self._open_item(item)

    def _open_item(self, item: QListWidgetItem) -> None:
        data = item.data(Qt.UserRole)
        if self._mode == "bookmarks":
            bm, book_id = data
            loc = bm.location
            if loc is None:
                try:
                    loc = self.container.bookmarks.resolve_location(bm.id)
                except Exception:  # noqa: BLE001
                    loc = None
            if loc is not None:
                self.open_at.emit(book_id, loc)
            else:
                self.open_book.emit(book_id)
        elif self._mode == "reviews":
            self.open_book.emit(data.book_id)
        else:
            loc = getattr(data, "location", None)
            if loc is not None:
                self.open_at.emit(data.book_id, loc)
            else:
                self.open_book.emit(data.book_id)

    def _delete(self) -> None:
        item = self._current_list().currentItem()
        if not item:
            return
        if QMessageBox.question(self, "Видалити", "Видалити вибраний елемент?") != QMessageBox.Yes:
            return
        try:
            data = item.data(Qt.UserRole)
            if self._mode == "quotes":
                self.container.quotes.delete(data.id)
            elif self._mode == "notes":
                self.container.notes.delete(data.id)
            elif self._mode == "bookmarks":
                bm, _ = data
                self.container.bookmarks.delete(bm.id)
            else:
                self.container.reviews.delete(data.book_id)
            self.toast.emit("Видалено", "success")
            self.reload()
        except Exception as exc:  # noqa: BLE001
            self.toast.emit(user_message(exc), "error")
