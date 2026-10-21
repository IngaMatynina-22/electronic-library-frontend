from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from app.schemas.dtos import BookFilter
from gui.ui.dialogs.bulk_edit_dialog import BulkEditDialog
from gui.ui.dialogs.metadata_dialog import MetadataDialog
from gui.ui.models.book_table_model import BookTableModel
from gui.ui.utils.errors import user_message
from gui.ui.utils.formatters import format_authors, format_progress, status_label
from gui.ui.widgets.book_card import BookCard
from gui.ui.widgets.cover_label import CoverLabel
from gui.ui.widgets.empty_state import EmptyState


class LibraryPage(QWidget):
    open_book = Signal(int)
    request_import = Signal()
    import_paths = Signal(list)
    status_message = Signal(str)
    toast = Signal(str, str)

    PRESETS = {
        "library_all": {},
        "library_continue": {"status": "reading"},
        "library_planned": {"status": "planned"},
        "library_reading": {"status": "reading"},
        "library_completed": {"status": "completed"},
        "library_favorites": {"is_favorite": True},
    }

    def __init__(self, container, settings, parent=None) -> None:
        super().__init__(parent)
        self.container = container
        self.settings = settings
        self._preset = "library_all"
        self._extra_filter: dict = {}
        self._books: list = []
        self.setAcceptDrops(True)

        self.setObjectName("AppRoot")
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        toolbar_frame = QFrame()
        toolbar_frame.setObjectName("LibraryToolbar")
        toolbar = QHBoxLayout(toolbar_frame)
        toolbar.setContentsMargins(0, 0, 0, 0)
        toolbar.setSpacing(8)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Пошук за назвою, автором…")
        self.search.textChanged.connect(self._on_search_changed)
        self.status_filter = QComboBox()
        self.status_filter.addItem("Усі статуси", None)
        for key, label in [
            ("planned", "Ще не прочитані"),
            ("reading", "Читаю"),
            ("completed", "Прочитані"),
            ("paused", "Пауза"),
            ("abandoned", "Відкладені"),
        ]:
            self.status_filter.addItem(label, key)
        self.status_filter.currentIndexChanged.connect(self.reload)

        self.sort_combo = QComboBox()
        for key, label in [
            ("title", "Назва"),
            ("author", "Автор"),
            ("created_at", "Дата додавання"),
            ("rating", "Рейтинг"),
            ("progress", "Прогрес"),
        ]:
            self.sort_combo.addItem(label, key)
        sort_by, sort_desc = settings.get_library_sort()
        idx = self.sort_combo.findData(sort_by)
        if idx >= 0:
            self.sort_combo.setCurrentIndex(idx)
        self.sort_combo.currentIndexChanged.connect(self.reload)

        self.view_btn = QPushButton("Список")
        self.view_btn.clicked.connect(self._toggle_view)
        reset_btn = QPushButton("Скинути фільтри")
        reset_btn.clicked.connect(self._reset_filters)
        bulk_btn = QPushButton("Масове редагування")
        bulk_btn.clicked.connect(self._bulk_edit)
        dup_btn = QPushButton("Дублікати")
        dup_btn.clicked.connect(self._find_duplicates)

        toolbar.addWidget(self.search, 2)
        toolbar.addWidget(self.status_filter)
        toolbar.addWidget(self.sort_combo)
        toolbar.addWidget(self.view_btn)
        toolbar.addWidget(reset_btn)
        toolbar.addWidget(bulk_btn)
        toolbar.addWidget(dup_btn)
        root.addWidget(toolbar_frame)

        splitter = QSplitter(Qt.Horizontal)
        self.stack = QStackedWidget()
        self.empty = EmptyState(
            "Бібліотека порожня",
            "Додайте PDF або EPUB, щоб почати читати.",
            "Імпортувати книги",
        )
        self.empty.action_clicked.connect(self.request_import.emit)

        self.grid = QListWidget()
        self.grid.setObjectName("CoverGrid")
        self.grid.setViewMode(QListWidget.IconMode)
        self.grid.setResizeMode(QListWidget.Adjust)
        self.grid.setMovement(QListWidget.Static)
        self.grid.setUniformItemSizes(True)
        self.grid.setSpacing(10)
        self.grid.setGridSize(BookCard.grid_size())
        self.grid.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.grid.setContextMenuPolicy(Qt.CustomContextMenu)
        self.grid.customContextMenuRequested.connect(self._context_menu_grid)
        self.grid.itemDoubleClicked.connect(lambda _: self._open_selected())
        self.grid.itemSelectionChanged.connect(self._on_grid_selection)

        self.table = QTableView()
        self.model = BookTableModel()
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._context_menu_table)
        self.table.doubleClicked.connect(lambda _: self._open_selected())
        self.table.selectionModel().selectionChanged.connect(lambda *_: self._sync_detail())

        self.content_stack = QStackedWidget()
        self.content_stack.addWidget(self.empty)
        self.content_stack.addWidget(self.grid)
        self.content_stack.addWidget(self.table)
        splitter.addWidget(self.content_stack)

        self.detail = _DetailPanel(container)
        self.detail.open_book.connect(self.open_book.emit)
        self.detail.changed.connect(self.reload)
        self.detail.toast.connect(self.toast.emit)
        splitter.addWidget(self.detail)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        root.addWidget(splitter, 1)

        self._view = settings.get_library_view()
        self._apply_view()

    def set_preset(self, key: str) -> None:
        self._preset = key if key in self.PRESETS else "library_all"
        self.reload()

    def set_extra_filter(self, **kwargs) -> None:
        self._extra_filter = kwargs
        self.reload()

    def reload(self) -> None:
        try:
            preset = dict(self.PRESETS.get(self._preset, {}))
            status = self.status_filter.currentData()
            if status:
                preset["status"] = status
            preset.update(self._extra_filter)
            filt = BookFilter(
                query=self.search.text().strip() or None,
                status=preset.get("status"),
                is_favorite=preset.get("is_favorite"),
                author_name=preset.get("author_name"),
                genre_name=preset.get("genre_name"),
                collection_id=preset.get("collection_id"),
                sort_by=self.sort_combo.currentData() or "title",
                sort_desc=self.sort_combo.currentData() in ("created_at", "rating", "progress"),
            )
            self.settings.set_library_sort(filt.sort_by, filt.sort_desc)
            books = self.container.search.filter_books(filt)
            # Continue reading: prefer books with progress among reading
            if self._preset == "library_continue":
                books = [
                    b
                    for b in books
                    if b.status == "reading"
                    or (b.progress and getattr(b.progress, "progress_percent", 0))
                ]
                books.sort(
                    key=lambda b: (b.last_opened_at or b.updated_at or b.created_at),
                    reverse=True,
                )
            self._books = books
            self.model.set_books(books)
            self._fill_grid(books)
            if not books:
                self.content_stack.setCurrentWidget(self.empty)
                if self._preset == "library_all" and not self.search.text():
                    self.empty.set_content(
                        "Бібліотека порожня",
                        "Підтримуються формати PDF та EPUB.",
                        "Імпортувати книги",
                    )
                else:
                    self.empty.set_content(
                        "Нічого не знайдено",
                        "Змініть фільтри або пошуковий запит.",
                        None,
                    )
            else:
                self._apply_view()
            self.status_message.emit(f"Книг: {len(books)}")
            self._sync_detail()
        except Exception as exc:  # noqa: BLE001
            self.toast.emit(user_message(exc), "error")

    def _fill_grid(self, books) -> None:
        self.grid.clear()
        for book in books:
            item = QListWidgetItem()
            widget = BookCard(book, self.container)
            item.setSizeHint(BookCard.grid_size())
            item.setData(Qt.UserRole, book.id)
            self.grid.addItem(item)
            self.grid.setItemWidget(item, widget)

    def _on_grid_selection(self) -> None:
        selected = {it.data(Qt.UserRole) for it in self.grid.selectedItems()}
        for i in range(self.grid.count()):
            item = self.grid.item(i)
            w = self.grid.itemWidget(item)
            if isinstance(w, BookCard):
                w.set_selected(item.data(Qt.UserRole) in selected)
        self._sync_detail()

    def _apply_view(self) -> None:
        if not self._books:
            self.content_stack.setCurrentWidget(self.empty)
            return
        if self._view == "list":
            self.content_stack.setCurrentWidget(self.table)
            self.view_btn.setText("Сітка")
        else:
            self.content_stack.setCurrentWidget(self.grid)
            self.view_btn.setText("Список")

    def _toggle_view(self) -> None:
        self._view = "list" if self._view == "grid" else "grid"
        self.settings.set_library_view(self._view)
        self._apply_view()

    def _reset_filters(self) -> None:
        self.search.blockSignals(True)
        self.search.clear()
        self.search.blockSignals(False)
        self.status_filter.setCurrentIndex(0)
        self._extra_filter = {}
        self.reload()

    def _on_search_changed(self, _text: str) -> None:
        self.reload()

    def selected_ids(self) -> list[int]:
        if self.content_stack.currentWidget() is self.table:
            rows = {i.row() for i in self.table.selectionModel().selectedRows()}
            return [self.model.book_at(r).id for r in rows if self.model.book_at(r)]
        return [it.data(Qt.UserRole) for it in self.grid.selectedItems()]

    def _selected_book(self):
        ids = self.selected_ids()
        if not ids:
            return None
        bid = ids[0]
        for b in self._books:
            if b.id == bid:
                return b
        try:
            return self.container.books.get(bid)
        except Exception:  # noqa: BLE001
            return None

    def _sync_detail(self) -> None:
        book = self._selected_book()
        self.detail.show_book(book)

    def _open_selected(self) -> None:
        book = self._selected_book()
        if book:
            self.open_book.emit(book.id)

    def _context_menu_grid(self, pos) -> None:
        if not self.grid.itemAt(pos):
            return
        self._show_menu(self.grid.mapToGlobal(pos))

    def _context_menu_table(self, pos) -> None:
        idx = self.table.indexAt(pos)
        if not idx.isValid():
            return
        self._show_menu(self.table.viewport().mapToGlobal(pos))

    def _show_menu(self, global_pos) -> None:
        book = self._selected_book()
        if not book:
            return
        menu = QMenu(self)
        menu.addAction("Відкрити", lambda: self.open_book.emit(book.id))
        menu.addAction("Продовжити читання", lambda: self.open_book.emit(book.id))
        fav = "Прибрати з обраного" if book.is_favorite else "Додати до обраного"
        menu.addAction(fav, lambda: self._toggle_favorite(book))
        status_menu = menu.addMenu("Змінити статус")
        for key, label in [
            ("planned", "Ще не прочитана"),
            ("reading", "Читаю"),
            ("completed", "Прочитана"),
            ("paused", "Пауза"),
            ("abandoned", "Відкладена"),
        ]:
            status_menu.addAction(label, lambda k=key: self._set_status(book, k))
        menu.addAction("Редагувати метадані", lambda: self._edit_metadata(book))
        menu.addAction("Додати до колекції…", lambda: self._add_to_collection(book))
        menu.addSeparator()
        menu.addAction("Видалити з бібліотеки", lambda: self._delete(book))
        menu.exec(global_pos)

    def _toggle_favorite(self, book) -> None:
        try:
            from app.schemas.dtos import BookUpdateDTO

            self.container.books.update(
                book.id, BookUpdateDTO(is_favorite=not book.is_favorite)
            )
            self.toast.emit("Оновлено обране", "success")
            self.reload()
        except Exception as exc:  # noqa: BLE001
            self.toast.emit(user_message(exc), "error")

    def _set_status(self, book, status: str) -> None:
        try:
            self.container.books.set_status(book.id, status)
            self.toast.emit("Статус оновлено", "success")
            self.reload()
        except Exception as exc:  # noqa: BLE001
            self.toast.emit(user_message(exc), "error")

    def _edit_metadata(self, book) -> None:
        dlg = MetadataDialog(book, self)
        if dlg.exec():
            try:
                self.container.books.update(book.id, dlg.to_update_dto())
                self.toast.emit("Метадані збережено", "success")
                self.reload()
            except Exception as exc:  # noqa: BLE001
                self.toast.emit(user_message(exc), "error")

    def _add_to_collection(self, book) -> None:
        try:
            cols = self.container.collections.list()
        except Exception as exc:  # noqa: BLE001
            self.toast.emit(user_message(exc), "error")
            return
        if not cols:
            self.toast.emit("Спочатку створіть колекцію", "info")
            return
        menu = QMenu(self)
        for c in cols:
            menu.addAction(c.name, lambda cid=c.id: self._do_add_collection(cid, book.id))
        menu.exec(self.cursor().pos())

    def _do_add_collection(self, collection_id: int, book_id: int) -> None:
        try:
            self.container.collections.add_book(collection_id, book_id)
            self.toast.emit("Додано до колекції", "success")
        except Exception as exc:  # noqa: BLE001
            self.toast.emit(user_message(exc), "error")

    def _delete(self, book) -> None:
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Warning)
        box.setWindowTitle("Видалити книгу")
        box.setText(f"Видалити «{book.title}» з бібліотеки?")
        box.setInformativeText(
            "Буде видалено запис бібліотеки та файли книги в сховищі застосунку."
        )
        box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        box.button(QMessageBox.Yes).setText("Видалити")
        box.button(QMessageBox.No).setText("Скасувати")
        if box.exec() != QMessageBox.Yes:
            return
        try:
            self.container.books.delete(book.id, delete_files=True)
            self.toast.emit("Книгу видалено", "success")
            self.reload()
        except Exception as exc:  # noqa: BLE001
            self.toast.emit(user_message(exc), "error")

    def _bulk_edit(self) -> None:
        ids = self.selected_ids()
        if not ids:
            self.toast.emit("Виберіть одну або кілька книг", "info")
            return
        dlg = BulkEditDialog(len(ids), self)
        if not dlg.exec():
            return
        kwargs = dlg.kwargs()
        if not kwargs:
            return
        try:
            n = self.container.library_org.bulk_update(ids, **kwargs)
            self.toast.emit(f"Оновлено записів: {n}", "success")
            self.reload()
        except Exception as exc:  # noqa: BLE001
            self.toast.emit(user_message(exc), "error")

    def _find_duplicates(self) -> None:
        try:
            groups = self.container.library_org.find_duplicates()
            if not groups:
                self.toast.emit("Потенційних дублікатів не знайдено", "success")
            else:
                self.toast.emit(f"Знайдено груп дублікатів: {len(groups)}", "info")
                self.status_message.emit(f"Дублікати: {len(groups)} груп — див. Інструменти")
        except Exception as exc:  # noqa: BLE001
            self.toast.emit(user_message(exc), "error")

    def dragEnterEvent(self, event) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:  # noqa: N802
        paths = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
        paths = [p for p in paths if Path(p).suffix.lower() in {".pdf", ".epub"}]
        if paths:
            self.import_paths.emit(paths)
        event.acceptProposedAction()


class _DetailPanel(QFrame):
    open_book = Signal(int)
    changed = Signal()
    toast = Signal(str, str)

    def __init__(self, container, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("DetailPanel")
        self.container = container
        self._book = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setObjectName("DetailScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        body = QWidget()
        body.setObjectName("DetailBody")
        layout = QVBoxLayout(body)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        self.cover = CoverLabel(140, 200)
        self.cover.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        layout.addWidget(self.cover, 0, Qt.AlignHCenter | Qt.AlignTop)

        self.title = QLabel("Оберіть книгу")
        self.title.setObjectName("BookTitle")
        self.title.setWordWrap(True)
        self.title.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.title.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        layout.addWidget(self.title)

        self.meta = QLabel("")
        self.meta.setObjectName("MutedLabel")
        self.meta.setWordWrap(True)
        layout.addWidget(self.meta)
        self.desc = QLabel("")
        self.desc.setWordWrap(True)
        layout.addWidget(self.desc)
        self.open_btn = QPushButton("Почати читання")
        self.open_btn.setObjectName("PrimaryButton")
        self.open_btn.clicked.connect(self._open)
        layout.addWidget(self.open_btn)
        edit_btn = QPushButton("Редагувати")
        edit_btn.clicked.connect(self._edit)
        layout.addWidget(edit_btn)
        self.cover_btn = QPushButton("Змінити обкладинку…")
        self.cover_btn.clicked.connect(self._change_cover)
        layout.addWidget(self.cover_btn)
        self.review_btn = QPushButton("Відгук")
        self.review_btn.clicked.connect(self._review)
        layout.addWidget(self.review_btn)
        self.review_preview = QLabel("")
        self.review_preview.setObjectName("MutedLabel")
        self.review_preview.setWordWrap(True)
        layout.addWidget(self.review_preview)
        self.ocr_btn = QPushButton("OCR (сканований PDF)")
        self.ocr_btn.clicked.connect(self._ocr)
        self.ocr_btn.setVisible(False)
        layout.addWidget(self.ocr_btn)
        layout.addStretch(1)

        scroll.setWidget(body)
        outer.addWidget(scroll)

    def show_book(self, book) -> None:
        self._book = book
        if book is None:
            self.title.setText("Оберіть книгу")
            self.meta.setText("")
            self.desc.setText("")
            self.cover.set_cover(None)
            self.open_btn.setEnabled(False)
            return
        self.open_btn.setEnabled(True)
        path = self.container.path_resolver.resolve(book.cover_path) if book.cover_path else None
        self.cover.set_cover(path, book.title)
        self.title.setText(book.title)
        genres = ", ".join(g.name for g in (book.genres or [])) or "—"
        self.meta.setText(
            f"{format_authors(book.authors)}\n"
            f"{book.format} · {status_label(book.status)} · {format_progress(book.progress)}\n"
            f"Жанр: {genres}"
            + (f" · ★ {book.rating}" if book.rating else "")
        )
        self.desc.setText((book.description or "")[:400])
        if book.status == "reading" or (book.progress and getattr(book.progress, "progress_percent", 0)):
            self.open_btn.setText("Продовжити читання")
        elif book.status == "completed":
            self.open_btn.setText("Переглянути книгу")
        else:
            self.open_btn.setText("Почати читання")
        try:
            show_ocr = (
                (book.format or "").upper() == "PDF"
                and self.container.ocr.is_available()
            )
        except Exception:  # noqa: BLE001
            show_ocr = False
        self.ocr_btn.setVisible(show_ocr)
        self._load_review_preview()

    def _load_review_preview(self) -> None:
        if not self._book:
            self.review_preview.setText("")
            return
        try:
            rev = self.container.reviews.get_by_book(self._book.id)
            if rev:
                stars = f"★ {rev.rating} · " if rev.rating else ""
                self.review_preview.setText(f"{stars}{(rev.content or '')[:180]}")
                self.review_btn.setText("Редагувати відгук")
            else:
                self.review_preview.setText("Відгуку ще немає")
                self.review_btn.setText("Написати відгук")
        except Exception:  # noqa: BLE001
            self.review_preview.setText("")

    def _open(self) -> None:
        if self._book:
            self.open_book.emit(self._book.id)

    def _edit(self) -> None:
        if not self._book:
            return
        dlg = MetadataDialog(self._book, self)
        if dlg.exec():
            try:
                self.container.books.update(self._book.id, dlg.to_update_dto())
                self.toast.emit("Метадані збережено", "success")
                self.changed.emit()
            except Exception as exc:  # noqa: BLE001
                self.toast.emit(user_message(exc), "error")

    def _change_cover(self) -> None:
        if not self._book:
            return
        from PySide6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Обрати обкладинку",
            "",
            "Зображення (*.jpg *.jpeg *.png *.webp *.bmp)",
        )
        if not path:
            return
        try:
            book = self.container.books.set_cover(self._book.id, path)
            self.show_book(book)
            self.toast.emit("Обкладинку оновлено", "success")
            self.changed.emit()
        except Exception as exc:  # noqa: BLE001
            self.toast.emit(user_message(exc), "error")

    def _review(self) -> None:
        if not self._book:
            return
        from gui.ui.dialogs.review_dialog import ReviewDialog

        existing = None
        try:
            existing = self.container.reviews.get_by_book(self._book.id)
        except Exception:  # noqa: BLE001
            pass
        dlg = ReviewDialog(self._book.title, existing, self)
        if not dlg.exec():
            return
        vals = dlg.values()
        if not vals["content"]:
            self.toast.emit("Текст відгуку обовʼязковий", "error")
            return
        try:
            if existing:
                self.container.reviews.update(
                    self._book.id,
                    content=vals["content"],
                    title=vals["title"],
                    rating=vals["rating"],
                )
            else:
                self.container.reviews.create(
                    self._book.id,
                    vals["content"],
                    title=vals["title"],
                    rating=vals["rating"],
                )
            if vals["rating"] is not None:
                self.container.books.set_rating(self._book.id, vals["rating"])
            self.toast.emit("Відгук збережено", "success")
            self._load_review_preview()
            self.changed.emit()
        except Exception as exc:  # noqa: BLE001
            self.toast.emit(user_message(exc), "error")

    def _ocr(self) -> None:
        if not self._book:
            return
        try:
            if not self.container.ocr.is_available():
                self.toast.emit(
                    "OCR недоступний. Встановіть Tesseract у системі.",
                    "error",
                )
                return
            from gui.ui.workers.base import run_in_thread

            book_id = self._book.id
            self.toast.emit("OCR запущено у фоні…", "info")

            def work():
                return self.container.ocr.process_book(book_id)

            run_in_thread(
                work,
                on_finished=lambda pages: self.toast.emit(
                    f"OCR завершено: сторінок {len(pages)}", "success"
                ),
                on_error=lambda exc: self.toast.emit(user_message(exc), "error"),
            )
        except Exception as exc:  # noqa: BLE001
            self.toast.emit(user_message(exc), "error")
