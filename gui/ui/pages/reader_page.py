from __future__ import annotations

import html
import re

from PySide6.QtCore import Qt, QTimer, Signal, QByteArray
from PySide6.QtGui import QPixmap, QKeySequence, QShortcut, QTextCursor
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from gui.ui.utils.errors import user_message
from gui.ui.utils.formatters import format_progress


class ReaderPage(QWidget):
    closed = Signal()
    toast = Signal(str, str)
    busy = Signal(bool, str)

    def __init__(self, container, parent=None) -> None:
        super().__init__(parent)
        self.container = container
        self._book_id: int | None = None
        self._format: str | None = None
        self._location = None
        self._total = 0
        self._session_guard = False
        self._zoom = 1.5
        self._quotes: list = []

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.top = QFrame()
        self.top.setObjectName("TopBar")
        top_l = QHBoxLayout(self.top)
        top_l.setContentsMargins(12, 8, 12, 8)
        self.back_btn = QPushButton("← Бібліотека")
        self.back_btn.clicked.connect(self.close_reader)
        self.title_lbl = QLabel("")
        self.title_lbl.setObjectName("BookTitle")
        self.progress_lbl = QLabel("")
        self.progress_lbl.setObjectName("MutedLabel")
        self.toggle_chrome = QPushButton("Панелі")
        self.toggle_chrome.setCheckable(True)
        self.toggle_chrome.setChecked(True)
        self.toggle_chrome.toggled.connect(self._toggle_side)
        top_l.addWidget(self.back_btn)
        top_l.addWidget(self.title_lbl, 1)
        top_l.addWidget(self.progress_lbl)
        top_l.addWidget(self.toggle_chrome)
        root.addWidget(self.top)

        self.splitter = QSplitter(Qt.Horizontal)
        self.side = QFrame()
        self.side.setObjectName("DetailPanel")
        self.side.setMinimumWidth(260)
        side_l = QVBoxLayout(self.side)
        side_l.setContentsMargins(8, 8, 8, 8)

        nav_row = QHBoxLayout()
        self.prev_btn = QPushButton("◀")
        self.next_btn = QPushButton("▶")
        self.prev_btn.clicked.connect(self.prev_page)
        self.next_btn.clicked.connect(self.next_page)
        self.page_spin = QSpinBox()
        self.page_spin.setMinimum(1)
        self.page_spin.valueChanged.connect(self._goto_page)
        nav_row.addWidget(self.prev_btn)
        nav_row.addWidget(self.page_spin)
        nav_row.addWidget(self.next_btn)
        side_l.addLayout(nav_row)

        side_l.addWidget(QLabel("Зміст"))
        self.toc = QListWidget()
        self.toc.itemClicked.connect(self._toc_clicked)
        side_l.addWidget(self.toc, 1)

        side_l.addWidget(QLabel("Матеріали"))
        bm_row = QHBoxLayout()
        add_bm = QPushButton("Закладка")
        add_bm.clicked.connect(self._add_bookmark)
        add_q = QPushButton("Цитата")
        add_q.clicked.connect(self._add_quote_from_selection)
        add_n = QPushButton("Нотатка")
        add_n.clicked.connect(self._add_note)
        bm_row.addWidget(add_bm)
        bm_row.addWidget(add_q)
        bm_row.addWidget(add_n)
        side_l.addLayout(bm_row)
        self.materials = QListWidget()
        self.materials.itemDoubleClicked.connect(self._material_activated)
        side_l.addWidget(self.materials, 1)

        side_l.addWidget(QLabel("Налаштування"))
        self.font_size = QSpinBox()
        self.font_size.setRange(12, 32)
        self.font_size.setValue(16)
        self.font_size.valueChanged.connect(self._apply_prefs)
        self.line_spacing = QDoubleSpinBox()
        self.line_spacing.setRange(1.0, 2.5)
        self.line_spacing.setSingleStep(0.1)
        self.line_spacing.setValue(1.5)
        self.line_spacing.valueChanged.connect(self._apply_prefs)
        self.theme_combo = QComboBox()
        for data, label in (("light", "Світла"), ("dark", "Темна"), ("paper", "Папір")):
            self.theme_combo.addItem(label, data)
        self.theme_combo.currentIndexChanged.connect(self._apply_prefs)
        self.zoom_spin = QDoubleSpinBox()
        self.zoom_spin.setRange(0.5, 3.0)
        self.zoom_spin.setSingleStep(0.1)
        self.zoom_spin.setValue(1.5)
        self.zoom_spin.valueChanged.connect(self._zoom_changed)
        side_l.addWidget(QLabel("Текст (EPUB)"))
        text_prefs = QFormLayout()
        text_prefs.addRow("Розмір шрифту", self.font_size)
        text_prefs.addRow("Міжрядковий інтервал", self.line_spacing)
        text_prefs.addRow("Тема читача", self.theme_combo)
        side_l.addLayout(text_prefs)
        side_l.addWidget(QLabel("PDF"))
        pdf_prefs = QFormLayout()
        pdf_prefs.addRow("Масштаб сторінки", self.zoom_spin)
        side_l.addLayout(pdf_prefs)

        # Content: PDF page OR text (toggled), or EPUB browser
        self.content_stack = QStackedWidget()

        pdf_host = QWidget()
        pdf_l = QVBoxLayout(pdf_host)
        pdf_l.setContentsMargins(0, 0, 0, 0)
        pdf_l.setSpacing(8)
        mode_row = QHBoxLayout()
        self.btn_page_view = QPushButton("Сторінка")
        self.btn_page_view.setCheckable(True)
        self.btn_page_view.setChecked(True)
        self.btn_page_view.setObjectName("PrimaryButton")
        self.btn_text_view = QPushButton("Текст сторінки")
        self.btn_text_view.setCheckable(True)
        self.btn_page_view.clicked.connect(lambda: self._set_pdf_mode(0))
        self.btn_text_view.clicked.connect(lambda: self._set_pdf_mode(1))
        mode_row.addWidget(self.btn_page_view)
        mode_row.addWidget(self.btn_text_view)
        mode_row.addStretch(1)
        pdf_l.addLayout(mode_row)

        self.pdf_mode_stack = QStackedWidget()
        self.pdf_scroll = QScrollArea()
        self.pdf_scroll.setWidgetResizable(True)
        self.pdf_scroll.setAlignment(Qt.AlignCenter)
        self.pdf_label = QLabel()
        self.pdf_label.setAlignment(Qt.AlignCenter)
        self.pdf_scroll.setWidget(self.pdf_label)
        text_wrap = QFrame()
        text_wrap.setObjectName("ContentSurface")
        tw_l = QVBoxLayout(text_wrap)
        tw_l.setContentsMargins(12, 12, 12, 12)
        tw_l.addWidget(QLabel("Виділіть фрагмент, щоб зберегти цитату з поточної сторінки"))
        self.pdf_text = QPlainTextEdit()
        self.pdf_text.setReadOnly(False)
        self.pdf_text.setPlaceholderText(
            "Текст сторінки з’явиться тут, якщо PDF має текстовий шар."
        )
        self.pdf_text.setContextMenuPolicy(Qt.CustomContextMenu)
        self.pdf_text.customContextMenuRequested.connect(self._pdf_text_menu)
        tw_l.addWidget(self.pdf_text)
        self.pdf_mode_stack.addWidget(self.pdf_scroll)
        self.pdf_mode_stack.addWidget(text_wrap)
        pdf_l.addWidget(self.pdf_mode_stack, 1)

        self.epub_view = QTextBrowser()
        self.epub_view.setOpenExternalLinks(False)
        self.epub_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.epub_view.customContextMenuRequested.connect(self._epub_menu)

        self.content_stack.addWidget(pdf_host)
        self.content_stack.addWidget(self.epub_view)

        self.splitter.addWidget(self.side)
        self.splitter.addWidget(self.content_stack)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        root.addWidget(self.splitter, 1)

        self._save_timer = QTimer(self)
        self._save_timer.setInterval(15000)
        self._save_timer.timeout.connect(self._autosave)

        for key, slot in [
            (QKeySequence(Qt.Key_Left), self.prev_page),
            (QKeySequence(Qt.Key_Right), self.next_page),
            (QKeySequence(Qt.Key_Escape), self.close_reader),
        ]:
            sc = QShortcut(key, self)
            sc.activated.connect(slot)

    @property
    def book_id(self) -> int | None:
        return self._book_id

    def open_book(self, book_id: int, location=None) -> None:
        if self._session_guard and self._book_id == book_id and location is None:
            return
        if self._book_id is not None and self._book_id != book_id:
            self._close_current(save=True)
        self._session_guard = True
        self.busy.emit(True, "Відкриття книги…")
        try:
            info = self.container.reader.open_book(book_id)
            book = self.container.books.get(book_id)
            self._book_id = book_id
            self._format = info["format"]
            self._location = location or info["location"]
            self._total = info["total_units"] or 1
            self.title_lbl.setText(book.title)
            self.page_spin.blockSignals(True)
            self.page_spin.setMaximum(max(1, self._total))
            self.page_spin.blockSignals(False)
            try:
                prefs = self.container.reader_prefs.get(book_id)
                if prefs.font_size:
                    self.font_size.setValue(prefs.font_size)
                if prefs.line_spacing:
                    self.line_spacing.setValue(prefs.line_spacing)
                if prefs.theme:
                    i = self.theme_combo.findData(prefs.theme)
                    if i >= 0:
                        self.theme_combo.setCurrentIndex(i)
                if prefs.pdf_zoom:
                    self.zoom_spin.setValue(prefs.pdf_zoom)
                    self._zoom = prefs.pdf_zoom
            except Exception:  # noqa: BLE001
                pass
            self._load_toc()
            self._load_materials()
            self._show_location()
            self._save_timer.start()
            try:
                self.container.books.touch_opened(book_id)
            except Exception:  # noqa: BLE001
                pass
            if location is not None:
                self._autosave()
        except Exception as exc:  # noqa: BLE001
            self.toast.emit(user_message(exc), "error")
            self._session_guard = False
        finally:
            self.busy.emit(False, "")

    def close_reader(self) -> None:
        self._close_current(save=True)
        self._session_guard = False
        self.closed.emit()

    def _close_current(self, *, save: bool) -> None:
        self._save_timer.stop()
        if self._book_id is None:
            return
        try:
            loc = self._location if save else None
            self.container.reader.close_book(self._book_id, loc)
        except Exception as exc:  # noqa: BLE001
            self.toast.emit(user_message(exc), "error")
        self._book_id = None
        self._location = None
        self._quotes = []

    def _load_toc(self) -> None:
        self.toc.clear()
        if self._book_id is None:
            return
        try:
            entries = self.container.reader.get_toc(self._book_id)
        except Exception:  # noqa: BLE001
            return

        def add(entries, prefix=""):
            for e in entries:
                item = QListWidgetItem(f"{prefix}{e.title}")
                item.setData(Qt.UserRole, e.location)
                self.toc.addItem(item)
                if e.children:
                    add(e.children, prefix + "  ")

        add(entries)

    def _load_materials(self) -> None:
        self.materials.clear()
        self._quotes = []
        if self._book_id is None:
            return
        try:
            self._quotes = list(self.container.quotes.get_by_book(self._book_id))
            for b in self.container.bookmarks.list(self._book_id):
                it = QListWidgetItem(f"Закладка · {b.title or 'без назви'}")
                it.setData(Qt.UserRole, ("bookmark", b))
                self.materials.addItem(it)
            for q in self._quotes:
                it = QListWidgetItem(f"Цитата · {q.text[:80]}")
                it.setData(Qt.UserRole, ("quote", q))
                self.materials.addItem(it)
            for n in self.container.notes.list(self._book_id):
                it = QListWidgetItem(f"Нотатка · {n.title or n.content[:80]}")
                it.setData(Qt.UserRole, ("note", n))
                self.materials.addItem(it)
        except Exception as exc:  # noqa: BLE001
            self.toast.emit(user_message(exc), "error")

    def _show_location(self) -> None:
        if self._book_id is None or self._location is None:
            return
        try:
            if (self._format or "").upper() == "PDF":
                self.content_stack.setCurrentIndex(0)
                self.btn_page_view.setVisible(True)
                self.btn_text_view.setVisible(True)
                page = self._location.page_number or int(self._location.locator or 1)
                self.page_spin.blockSignals(True)
                self.page_spin.setValue(page)
                self.page_spin.blockSignals(False)
                data = self.container.reader.render_page(self._book_id, page, zoom=self._zoom)
                pix = QPixmap()
                pix.loadFromData(QByteArray(data))
                self.pdf_label.setPixmap(pix)
                content = self.container.reader.get_content(self._book_id, self._location)
                text = content.content or ""
                self.pdf_text.blockSignals(True)
                self.pdf_text.setPlainText(text)
                self.pdf_text.blockSignals(False)
                if not text.strip():
                    self.pdf_text.setPlaceholderText(
                        "На цій сторінці немає текстового шару. "
                        "Для сканів скористайтеся OCR у картці книги."
                    )
                else:
                    self._highlight_pdf_quotes(text)
            else:
                self.content_stack.setCurrentIndex(1)
                self.btn_page_view.setVisible(False)
                self.btn_text_view.setVisible(False)
                page = self.container.reader.get_content(self._book_id, self._location)
                body = self._inject_epub_highlights(page.content or "")
                css = self._epub_css()
                html_doc = f"<html><head><style>{css}</style></head><body>{body}</body></html>"
                self.epub_view.setHtml(html_doc)
                try:
                    loc_idx = int(getattr(self._location, "page_number", None) or 1)
                except Exception:  # noqa: BLE001
                    loc_idx = 1
                self.page_spin.blockSignals(True)
                self.page_spin.setValue(max(1, min(loc_idx, self._total)))
                self.page_spin.blockSignals(False)
            prog = self.container.reading.get_progress(self._book_id)
            self.progress_lbl.setText(format_progress(prog))
        except Exception as exc:  # noqa: BLE001
            self.toast.emit(user_message(exc), "error")

    def _highlight_pdf_quotes(self, page_text: str) -> None:
        # Visual cue: select first matching quote snippet in the text panel
        page_no = getattr(self._location, "page_number", None)
        for q in self._quotes:
            if q.page_number and page_no and q.page_number != page_no:
                continue
            snippet = (q.text or "").strip()
            if len(snippet) < 8:
                continue
            idx = page_text.find(snippet[:80])
            if idx >= 0:
                cursor = self.pdf_text.textCursor()
                cursor.setPosition(idx)
                cursor.setPosition(
                    idx + min(len(snippet), 80), QTextCursor.KeepAnchor
                )
                self.pdf_text.setTextCursor(cursor)
                break

    def _inject_epub_highlights(self, body: str) -> str:
        loc_key = getattr(self._location, "locator", None) or ""
        for q in self._quotes:
            qloc = getattr(q.location, "locator", None) if q.location else None
            same = (not qloc) or (qloc.split("#")[0] == loc_key.split("#")[0])
            if not same:
                continue
            snippet = (q.text or "").strip()
            if len(snippet) < 6:
                continue
            # Escape and wrap first occurrence
            esc = re.escape(snippet[:120])
            marked = f'<mark class="quote-hl">{html.escape(snippet[:120])}</mark>'
            body, n = re.subn(esc, marked, body, count=1, flags=re.IGNORECASE)
            if n:
                continue
            # fallback: plain replace on unescaped text fragments
            if snippet[:40] in body:
                body = body.replace(snippet[:40], f'<mark class="quote-hl">{snippet[:40]}</mark>', 1)
        return body

    def _epub_css(self) -> str:
        theme = self.theme_combo.currentData()
        if theme == "dark":
            bg, fg = "#22231F", "#E8E4DC"
        elif theme == "paper":
            bg, fg = "#F4ECD8", "#2C2A26"
        else:
            bg, fg = "#FBF8F2", "#2C2A26"
        return (
            f"body {{ background:{bg}; color:{fg}; font-size:{self.font_size.value()}px; "
            f"line-height:{self.line_spacing.value()}; max-width:42rem; margin:1.5rem auto; "
            f"font-family: Georgia, 'Times New Roman', serif; padding:0 1rem; }}"
            "img { max-width: 100%; height: auto; }"
            "mark.quote-hl { background: #E8D48A; color: inherit; padding: 0 2px; }"
        )

    def prev_page(self) -> None:
        if self._book_id is None or self._location is None:
            return
        loc = self.container.reader.get_previous_location(self._book_id, self._location)
        if loc:
            self._location = loc
            self._show_location()
            self._autosave()

    def next_page(self) -> None:
        if self._book_id is None or self._location is None:
            return
        loc = self.container.reader.get_next_location(self._book_id, self._location)
        if loc:
            self._location = loc
            self._show_location()
            self._autosave()

    def _goto_page(self, value: int) -> None:
        if self._book_id is None or (self._format or "").upper() != "PDF":
            return
        from app.readers.location_mapper import pdf_location

        self._location = pdf_location(self._book_id, value, self._total)
        self._show_location()
        self._autosave()

    def _toc_clicked(self, item: QListWidgetItem) -> None:
        loc = item.data(Qt.UserRole)
        if loc is None:
            return
        self._location = loc
        self._show_location()
        self._autosave()

    def _autosave(self) -> None:
        if self._book_id is None or self._location is None:
            return
        try:
            self.container.reader.save_position(self._book_id, self._location)
            prog = self.container.reading.get_progress(self._book_id)
            self.progress_lbl.setText(format_progress(prog))
        except Exception:  # noqa: BLE001
            pass

    def _toggle_side(self, on: bool) -> None:
        self.side.setVisible(on)

    def _set_pdf_mode(self, index: int) -> None:
        """Switch between page image and page text without changing location."""
        self.pdf_mode_stack.setCurrentIndex(index)
        self.btn_page_view.setChecked(index == 0)
        self.btn_text_view.setChecked(index == 1)
        self.btn_page_view.setObjectName("PrimaryButton" if index == 0 else "")
        self.btn_text_view.setObjectName("PrimaryButton" if index == 1 else "")
        for btn in (self.btn_page_view, self.btn_text_view):
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _zoom_changed(self, value: float) -> None:
        self._zoom = value
        self._apply_prefs()
        if (self._format or "").upper() == "PDF":
            self._show_location()

    def _apply_prefs(self) -> None:
        if self._book_id is None:
            return
        try:
            self.container.reader_prefs.set(
                book_id=self._book_id,
                font_size=self.font_size.value(),
                line_spacing=self.line_spacing.value(),
                theme=self.theme_combo.currentData(),
                pdf_zoom=self.zoom_spin.value(),
            )
            if (self._format or "").upper() != "PDF":
                self._show_location()
        except Exception as exc:  # noqa: BLE001
            self.toast.emit(user_message(exc), "error")

    def _selected_text(self) -> str:
        if (self._format or "").upper() == "PDF":
            return self.pdf_text.textCursor().selectedText().replace("\u2029", "\n").strip()
        return self.epub_view.textCursor().selectedText().replace("\u2029", "\n").strip()

    def _add_bookmark(self) -> None:
        if self._book_id is None or self._location is None:
            return
        title, ok = QInputDialog.getText(self, "Закладка", "Назва закладки:")
        if not ok:
            return
        try:
            self.container.bookmarks.create(
                self._book_id, self._location, title=title.strip() or None
            )
            self.toast.emit("Закладку створено", "success")
            self._load_materials()
        except Exception as exc:  # noqa: BLE001
            self.toast.emit(user_message(exc), "error")

    def _add_quote_from_selection(self) -> None:
        if self._book_id is None:
            return
        text = self._selected_text()
        if not text:
            text, ok = QInputDialog.getMultiLineText(
                self, "Цитата", "Виділіть текст у книзі або введіть цитату:"
            )
            if not ok or not text.strip():
                return
        try:
            self.container.quotes.create(
                self._book_id,
                text.strip(),
                location=self._location,
                page_number=getattr(self._location, "page_number", None),
                chapter_title=getattr(self._location, "chapter_title", None),
            )
            self.toast.emit("Цитату збережено з позиції в тексті", "success")
            self._load_materials()
            self._show_location()
        except Exception as exc:  # noqa: BLE001
            self.toast.emit(user_message(exc), "error")

    def _add_note(self) -> None:
        if self._book_id is None:
            return
        selected = self._selected_text()
        prompt = "Текст нотатки:"
        if selected:
            prompt = "Нотатка до виділеного фрагмента:"
        text, ok = QInputDialog.getMultiLineText(self, "Нотатка", prompt, selected)
        if not ok or not text.strip():
            return
        try:
            self.container.notes.create(
                self._book_id, text.strip(), location=self._location
            )
            self.toast.emit("Нотатку збережено", "success")
            self._load_materials()
        except Exception as exc:  # noqa: BLE001
            self.toast.emit(user_message(exc), "error")

    def _pdf_text_menu(self, pos) -> None:
        menu = QMenu(self)
        menu.addAction("Зберегти цитату", self._add_quote_from_selection)
        menu.addAction("Нотатка до виділення", self._add_note)
        menu.addAction("Закладка на сторінці", self._add_bookmark)
        menu.exec(self.pdf_text.mapToGlobal(pos))

    def _epub_menu(self, pos) -> None:
        menu = QMenu(self)
        menu.addAction("Зберегти цитату", self._add_quote_from_selection)
        menu.addAction("Нотатка до виділення", self._add_note)
        menu.addAction("Закладка тут", self._add_bookmark)
        menu.exec(self.epub_view.mapToGlobal(pos))

    def _material_activated(self, item: QListWidgetItem) -> None:
        data = item.data(Qt.UserRole)
        if not data:
            return
        kind, obj = data
        loc = getattr(obj, "location", None)
        if kind == "bookmark" and loc is None:
            try:
                loc = self.container.bookmarks.resolve_location(obj.id)
            except Exception:  # noqa: BLE001
                loc = None
        if loc is not None:
            self._location = loc
            self._show_location()
            self._autosave()
