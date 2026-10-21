from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.schemas.dtos import BookFilter
from gui.ui.utils.errors import user_message
from gui.ui.widgets.book_card import BookCard


def _tag_name(tag) -> str:
    if isinstance(tag, str):
        return tag
    return getattr(tag, "name", "") or str(tag)


class FolderCard(QFrame):
    def __init__(self, name: str, count: int, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("FolderCard")
        self.setFixedSize(150, 130)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 16, 12, 12)
        icon = QLabel("📁")
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet("font-size: 28px;")
        title = QLabel(name)
        title.setObjectName("BookCardTitle")
        title.setAlignment(Qt.AlignCenter)
        title.setWordWrap(True)
        meta = QLabel(f"{count} книг")
        meta.setObjectName("MutedLabel")
        meta.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon)
        layout.addWidget(title)
        layout.addWidget(meta)

    def sizeHint(self):  # noqa: N802
        from PySide6.QtCore import QSize

        return QSize(166, 146)


class OrgPage(QWidget):
    """Collections as folders; genres/authors/tags as list + cover grid."""

    open_library_filter = Signal(dict)
    open_book = Signal(int)
    toast = Signal(str, str)

    def __init__(self, container, parent=None) -> None:
        super().__init__(parent)
        self.container = container
        self._mode = "collections"
        self._folder_id: int | None = None
        self._folder_name: str | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        self.title = QLabel("Організація")
        self.title.setObjectName("PageTitle")
        root.addWidget(self.title)

        self.breadcrumb = QLabel("")
        self.breadcrumb.setObjectName("MutedLabel")
        root.addWidget(self.breadcrumb)

        row = QHBoxLayout()
        self.back_btn = QPushButton("← Назад")
        self.back_btn.clicked.connect(self._back_to_folders)
        self.back_btn.setVisible(False)
        self.add_btn = QPushButton("Створити")
        self.add_btn.setObjectName("PrimaryButton")
        self.add_btn.clicked.connect(self._create)
        self.del_btn = QPushButton("Видалити")
        self.del_btn.setObjectName("DangerButton")
        self.del_btn.clicked.connect(self._delete)
        self.open_btn = QPushButton("Відкрити")
        self.open_btn.clicked.connect(self._open_selected)
        self.remove_btn = QPushButton("Прибрати з колекції")
        self.remove_btn.clicked.connect(self._remove_from_collection)
        self.remove_btn.setVisible(False)
        row.addWidget(self.back_btn)
        row.addWidget(self.add_btn)
        row.addWidget(self.del_btn)
        row.addWidget(self.open_btn)
        row.addWidget(self.remove_btn)
        row.addStretch(1)
        root.addLayout(row)

        self.stack = QStackedWidget()

        # Collections root: folder grid
        self.folder_grid = QListWidget()
        self.folder_grid.setObjectName("CoverGrid")
        self.folder_grid.setViewMode(QListWidget.IconMode)
        self.folder_grid.setResizeMode(QListWidget.Adjust)
        self.folder_grid.setMovement(QListWidget.Static)
        self.folder_grid.setSpacing(12)
        self.folder_grid.setGridSize(FolderCard( "", 0).sizeHint())
        self.folder_grid.itemDoubleClicked.connect(self._open_folder_item)
        self.stack.addWidget(self.folder_grid)

        # Split: side list + cover grid (genres/authors/tags or books in folder)
        split_host = QWidget()
        split_l = QHBoxLayout(split_host)
        split_l.setContentsMargins(0, 0, 0, 0)
        splitter = QSplitter(Qt.Horizontal)
        self.side_list = QListWidget()
        self.side_list.setObjectName("OrgSideList")
        self.side_list.currentItemChanged.connect(lambda *_: self._show_covers_for_side())
        self.cover_grid = QListWidget()
        self.cover_grid.setObjectName("CoverGrid")
        self.cover_grid.setViewMode(QListWidget.IconMode)
        self.cover_grid.setResizeMode(QListWidget.Adjust)
        self.cover_grid.setMovement(QListWidget.Static)
        self.cover_grid.setSpacing(10)
        self.cover_grid.setGridSize(BookCard.grid_size())
        self.cover_grid.itemDoubleClicked.connect(self._open_book_item)
        self.cover_grid.itemSelectionChanged.connect(self._sync_cover_selection)
        splitter.addWidget(self.side_list)
        splitter.addWidget(self.cover_grid)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        split_l.addWidget(splitter)
        self.stack.addWidget(split_host)

        # Folder books only (full width cover grid)
        self.folder_books = QListWidget()
        self.folder_books.setObjectName("CoverGrid")
        self.folder_books.setViewMode(QListWidget.IconMode)
        self.folder_books.setResizeMode(QListWidget.Adjust)
        self.folder_books.setMovement(QListWidget.Static)
        self.folder_books.setSpacing(10)
        self.folder_books.setGridSize(BookCard.grid_size())
        self.folder_books.itemDoubleClicked.connect(self._open_book_item)
        self.folder_books.itemSelectionChanged.connect(
            lambda: self._paint_selected(self.folder_books)
        )
        self.stack.addWidget(self.folder_books)

        root.addWidget(self.stack, 1)

    def show_mode(self, mode: str) -> None:
        self._mode = mode
        self._folder_id = None
        self._folder_name = None
        titles = {
            "collections": "Колекції",
            "genres": "Жанри",
            "authors": "Автори",
            "tags": "Теги",
        }
        self.title.setText(titles.get(mode, "Організація"))
        creatable = mode in {"collections", "tags"}
        self.add_btn.setVisible(creatable and self._folder_id is None)
        self.del_btn.setVisible(creatable)
        self.reload()

    def reload(self) -> None:
        try:
            if self._mode == "collections":
                if self._folder_id is None:
                    self._show_folder_root()
                else:
                    self._show_folder_books()
            else:
                self._show_side_and_covers()
        except Exception as exc:  # noqa: BLE001
            self.toast.emit(user_message(exc), "error")

    def _show_folder_root(self) -> None:
        self.stack.setCurrentWidget(self.folder_grid)
        self.breadcrumb.setText("Колекції — відкрийте папку подвійним кліком")
        self.back_btn.setVisible(False)
        self.remove_btn.setVisible(False)
        self.add_btn.setVisible(True)
        self.open_btn.setText("Відкрити папку")
        self.folder_grid.clear()
        for c in self.container.collections.list():
            item = QListWidgetItem()
            card = FolderCard(c.name, c.book_count)
            item.setSizeHint(card.sizeHint())
            item.setData(Qt.UserRole, c)
            self.folder_grid.addItem(item)
            self.folder_grid.setItemWidget(item, card)

    def _show_folder_books(self) -> None:
        self.stack.setCurrentWidget(self.folder_books)
        self.breadcrumb.setText(f"Колекції / {self._folder_name}")
        self.back_btn.setVisible(True)
        self.remove_btn.setVisible(True)
        self.add_btn.setVisible(False)
        self.open_btn.setText("Відкрити книгу")
        self.folder_books.clear()
        books = self.container.collections.list_books(self._folder_id)
        if not books:
            empty = QListWidgetItem("Папка порожня")
            empty.setFlags(Qt.NoItemFlags)
            self.folder_books.addItem(empty)
            return
        for b in books:
            self._add_book_card(self.folder_books, b)

    def _show_side_and_covers(self) -> None:
        self.stack.setCurrentIndex(1)
        self.breadcrumb.setText("Оберіть елемент ліворуч — книги показуються обкладинками")
        self.back_btn.setVisible(False)
        self.remove_btn.setVisible(False)
        self.add_btn.setVisible(self._mode == "tags")
        self.del_btn.setVisible(self._mode == "tags")
        self.open_btn.setText("Показати в бібліотеці")
        self.side_list.clear()
        self.cover_grid.clear()
        if self._mode == "tags":
            for t in self.container.tags.list():
                it = QListWidgetItem(_tag_name(t))
                it.setData(Qt.UserRole, t)
                self.side_list.addItem(it)
        else:
            books = self.container.books.list()
            counts: dict[str, int] = {}
            for b in books:
                items = b.authors if self._mode == "authors" else b.genres
                for x in items or []:
                    name = _tag_name(x)
                    if name:
                        counts[name] = counts.get(name, 0) + 1
            for name, count in sorted(counts.items(), key=lambda kv: kv[0].lower()):
                it = QListWidgetItem(f"{name} ({count})")
                it.setData(Qt.UserRole, name)
                self.side_list.addItem(it)
        if self.side_list.count():
            self.side_list.setCurrentRow(0)

    def _show_covers_for_side(self) -> None:
        self.cover_grid.clear()
        item = self.side_list.currentItem()
        if not item or self._mode == "collections":
            return
        try:
            if self._mode == "tags":
                tag = item.data(Qt.UserRole)
                tname = _tag_name(tag)
                # Books aren't tagged directly — show quotes/notes context as empty books message
                # Filter books that have quotes/notes with this tag is heavy; show books from library filter if any
                shown = set()
                for q in self.container.quotes.list():
                    names = {_tag_name(t) for t in (q.tags or [])}
                    if tname in names and q.book_id not in shown:
                        try:
                            b = self.container.books.get(q.book_id)
                            self._add_book_card(self.cover_grid, b)
                            shown.add(q.book_id)
                        except Exception:  # noqa: BLE001
                            pass
                if not shown:
                    msg = QListWidgetItem("Немає книг із матеріалами за цим тегом")
                    msg.setFlags(Qt.NoItemFlags)
                    self.cover_grid.addItem(msg)
            else:
                name = item.data(Qt.UserRole)
                key = "author_name" if self._mode == "authors" else "genre_name"
                books = self.container.search.filter_books(BookFilter(**{key: name}))
                for b in books:
                    self._add_book_card(self.cover_grid, b)
                if not books:
                    msg = QListWidgetItem("Немає книг")
                    msg.setFlags(Qt.NoItemFlags)
                    self.cover_grid.addItem(msg)
        except Exception as exc:  # noqa: BLE001
            self.toast.emit(user_message(exc), "error")

    def _add_book_card(self, grid: QListWidget, book) -> None:
        item = QListWidgetItem()
        card = BookCard(book, self.container)
        item.setSizeHint(BookCard.grid_size())
        item.setData(Qt.UserRole, book.id)
        grid.addItem(item)
        grid.setItemWidget(item, card)

    def _paint_selected(self, grid: QListWidget) -> None:
        selected = {it.data(Qt.UserRole) for it in grid.selectedItems()}
        for i in range(grid.count()):
            item = grid.item(i)
            w = grid.itemWidget(item)
            if isinstance(w, BookCard):
                w.set_selected(item.data(Qt.UserRole) in selected)

    def _sync_cover_selection(self) -> None:
        self._paint_selected(self.cover_grid)

    def _open_folder_item(self, item: QListWidgetItem) -> None:
        col = item.data(Qt.UserRole)
        if col is None:
            return
        self._folder_id = col.id
        self._folder_name = col.name
        self.reload()

    def _back_to_folders(self) -> None:
        self._folder_id = None
        self._folder_name = None
        self.reload()

    def _open_selected(self) -> None:
        if self._mode == "collections":
            if self._folder_id is None:
                item = self.folder_grid.currentItem()
                if item:
                    self._open_folder_item(item)
            else:
                item = self.folder_books.currentItem()
                if item and item.data(Qt.UserRole):
                    self.open_book.emit(item.data(Qt.UserRole))
            return
        item = self.side_list.currentItem()
        if not item:
            return
        obj = item.data(Qt.UserRole)
        if self._mode == "authors":
            self.open_library_filter.emit({"author_name": obj})
        elif self._mode == "genres":
            self.open_library_filter.emit({"genre_name": obj})
        else:
            self.toast.emit("Оберіть книгу з сітки обкладинок", "info")

    def _open_book_item(self, item: QListWidgetItem) -> None:
        bid = item.data(Qt.UserRole)
        if isinstance(bid, int):
            self.open_book.emit(bid)

    def _remove_from_collection(self) -> None:
        if self._folder_id is None:
            return
        item = self.folder_books.currentItem()
        if not item or not isinstance(item.data(Qt.UserRole), int):
            return
        try:
            self.container.collections.remove_book(self._folder_id, item.data(Qt.UserRole))
            self.toast.emit("Книгу прибрано з колекції", "success")
            self.reload()
        except Exception as exc:  # noqa: BLE001
            self.toast.emit(user_message(exc), "error")

    def _create(self) -> None:
        if self._mode == "collections" and self._folder_id is None:
            name, ok = QInputDialog.getText(self, "Папка-колекція", "Назва папки:")
            if not ok or not name.strip():
                return
            desc, _ = QInputDialog.getText(self, "Папка-колекція", "Опис (необовʼязково):")
            try:
                self.container.collections.create(name.strip(), description=desc.strip() or None)
                self.toast.emit("Папку створено", "success")
                self.reload()
            except Exception as exc:  # noqa: BLE001
                self.toast.emit(user_message(exc), "error")
        elif self._mode == "tags":
            name, ok = QInputDialog.getText(self, "Тег", "Назва:")
            if not ok or not name.strip():
                return
            try:
                self.container.tags.create(name.strip())
                self.toast.emit("Тег створено", "success")
                self.reload()
            except Exception as exc:  # noqa: BLE001
                self.toast.emit(user_message(exc), "error")

    def _delete(self) -> None:
        if self._mode == "collections" and self._folder_id is None:
            item = self.folder_grid.currentItem()
            if not item:
                return
            col = item.data(Qt.UserRole)
            if QMessageBox.question(self, "Видалити", f"Видалити папку «{col.name}»?") != QMessageBox.Yes:
                return
            try:
                self.container.collections.delete(col.id)
                self.toast.emit("Папку видалено", "success")
                self.reload()
            except Exception as exc:  # noqa: BLE001
                self.toast.emit(user_message(exc), "error")
        elif self._mode == "tags":
            item = self.side_list.currentItem()
            if not item:
                return
            tag = item.data(Qt.UserRole)
            if QMessageBox.question(self, "Видалити", f"Видалити тег «{_tag_name(tag)}»?") != QMessageBox.Yes:
                return
            try:
                self.container.tags.delete(tag.id)
                self.toast.emit("Тег видалено", "success")
                self.reload()
            except Exception as exc:  # noqa: BLE001
                self.toast.emit(user_message(exc), "error")
