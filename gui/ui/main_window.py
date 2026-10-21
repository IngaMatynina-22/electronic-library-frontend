from __future__ import annotations

from PySide6.QtCore import Qt, QSize, QTimer, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from gui.ui.navigation.nav_panel import NavPanel
from gui.ui.pages.analytics_page import AnalyticsPage
from gui.ui.pages.import_page import ImportPage
from gui.ui.pages.library_page import LibraryPage
from gui.ui.pages.materials_page import MaterialsPage
from gui.ui.pages.org_page import OrgPage
from gui.ui.pages.reader_page import ReaderPage
from gui.ui.pages.search_page import SearchPage
from gui.ui.pages.settings_page import SettingsPage
from gui.ui.pages.tools_page import ToolsPage
from gui.ui.resources_icons import load_icon
from gui.ui.themes.theme_manager import ThemeManager, apply_theme
from gui.ui.themes.tokens import DARK, LIGHT
from gui.ui.utils.app_settings import AppSettings
from gui.ui.widgets.toast import ToastHost


PAGE_TITLES = {
    "library_all": "Усі книги",
    "library_continue": "Продовжити читання",
    "library_planned": "Ще не прочитані",
    "library_reading": "Читаю зараз",
    "library_completed": "Прочитані",
    "library_favorites": "Вибране",
    "collections": "Колекції",
    "genres": "Жанри",
    "authors": "Автори",
    "tags": "Теги",
    "quotes": "Цитати",
    "notes": "Нотатки",
    "bookmarks": "Закладки",
    "stats": "Статистика читання",
    "calendar": "Календар активності",
    "goals": "Цілі читання",
    "import": "Імпорт книг",
    "tools": "Інструменти організації",
    "settings": "Налаштування",
    "search": "Пошук",
    "reader": "Читання",
}


class MainWindow(QMainWindow):
    logout_requested = Signal()

    def __init__(self, container) -> None:
        super().__init__()
        self.container = container
        self.settings = AppSettings()
        self.theme_manager = ThemeManager()
        self._busy = False
        self.setWindowTitle("Персональна електронна бібліотека")
        self.setMinimumSize(1000, 650)
        self.resize(1280, 800)

        central = QWidget()
        central.setObjectName("AppRoot")
        self.setCentralWidget(central)
        outer = QHBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.nav = NavPanel()
        self.nav.navigated.connect(self.navigate)
        outer.addWidget(self.nav)

        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)

        self.top = QFrame()
        self.top.setObjectName("TopBar")
        top_l = QHBoxLayout(self.top)
        top_l.setContentsMargins(16, 10, 16, 10)
        self.section_title = QLabel("Усі книги")
        self.section_title.setObjectName("PageTitle")
        self.global_search = QLineEdit()
        self.global_search.setPlaceholderText("Пошук у бібліотеці та тексті…")
        self.global_search.returnPressed.connect(self._run_global_search)
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(400)
        self._search_timer.timeout.connect(self._run_global_search)
        self.global_search.textChanged.connect(lambda _: self._search_timer.start())

        add_btn = QPushButton("Додати книгу")
        add_btn.setObjectName("PrimaryButton")
        add_btn.clicked.connect(self._quick_import)
        self.busy_bar = QProgressBar()
        self.busy_bar.setRange(0, 0)
        self.busy_bar.setFixedWidth(120)
        self.busy_bar.setVisible(False)
        self.busy_label = QLabel("")
        self.busy_label.setObjectName("MutedLabel")

        self.theme_btn = QPushButton()
        self.theme_btn.setObjectName("IconToolButton")
        self.theme_btn.setFixedSize(36, 36)
        self.theme_btn.setToolTip("Перемкнути світлу / темну тему")
        self.theme_btn.clicked.connect(self._toggle_theme)
        self.user_label = QLabel("")
        self.user_label.setObjectName("MutedLabel")
        logout_btn = QPushButton("Вийти")
        logout_btn.clicked.connect(self.logout_requested.emit)
        settings_btn = QPushButton("⚙")
        settings_btn.setFixedWidth(36)
        settings_btn.setToolTip("Налаштування")
        settings_btn.clicked.connect(lambda: self.navigate("settings"))

        top_l.addWidget(self.section_title)
        top_l.addStretch(1)
        top_l.addWidget(self.global_search, 2)
        top_l.addWidget(self.busy_label)
        top_l.addWidget(self.busy_bar)
        top_l.addWidget(add_btn)
        top_l.addWidget(self.theme_btn)
        top_l.addWidget(self.user_label)
        top_l.addWidget(logout_btn)
        top_l.addWidget(settings_btn)
        right.addWidget(self.top)

        self.stack = QStackedWidget()
        self.library = LibraryPage(container, self.settings)
        self.import_page = ImportPage(container)
        self.reader = ReaderPage(container)
        self.search_page = SearchPage(container)
        self.materials = MaterialsPage(container)
        self.org = OrgPage(container)
        self.analytics = AnalyticsPage(container)
        self.tools = ToolsPage(container)
        self.settings_page = SettingsPage(container, self.settings, self.theme_manager)

        for page in (
            self.library,
            self.import_page,
            self.reader,
            self.search_page,
            self.materials,
            self.org,
            self.analytics,
            self.tools,
            self.settings_page,
        ):
            self.stack.addWidget(page)

        right.addWidget(self.stack, 1)

        self.status = QFrame()
        self.status.setObjectName("StatusBar")
        status_l = QHBoxLayout(self.status)
        status_l.setContentsMargins(16, 6, 16, 6)
        self.status_label = QLabel("Готово")
        self.status_label.setObjectName("MutedLabel")
        status_l.addWidget(self.status_label)
        status_l.addStretch(1)
        right.addWidget(self.status)

        right_host = QWidget()
        right_host.setObjectName("AppRoot")
        right_host.setLayout(right)
        outer.addWidget(right_host, 1)

        self.toast = ToastHost(central)

        self.library.open_book.connect(lambda bid: self.open_reader(bid))
        self.library.request_import.connect(lambda: self.navigate("import"))
        self.library.import_paths.connect(self.import_paths)
        self.library.status_message.connect(self.status_label.setText)
        self.library.toast.connect(self._toast)
        self.import_page.import_finished.connect(self.library.reload)
        self.import_page.toast.connect(self._toast)
        self.import_page.busy.connect(self._set_busy)
        self.reader.closed.connect(lambda: self.navigate("library_all"))
        self.reader.toast.connect(self._toast)
        self.reader.busy.connect(self._set_busy)
        self.search_page.open_book.connect(lambda bid: self.open_reader(bid))
        self.search_page.toast.connect(self._toast)
        self.materials.open_book.connect(lambda bid: self.open_reader(bid))
        self.materials.open_at.connect(self.open_reader_at)
        self.materials.toast.connect(self._toast)
        self.org.open_library_filter.connect(self._filter_library)
        self.org.open_book.connect(lambda bid: self.open_reader(bid))
        self.org.toast.connect(self._toast)
        self.analytics.toast.connect(self._toast)
        self.tools.toast.connect(self._toast)
        self.settings_page.theme_changed.connect(self._apply_theme)
        self.settings_page.toast.connect(self._toast)

        self._install_shortcuts()
        theme = self.settings.get_theme()
        self._apply_theme(theme)

    def on_user_ready(self, user) -> None:
        name = getattr(user, "display_name", None) or getattr(user, "username", "")
        self.user_label.setText(name)
        self.setWindowTitle(f"Персональна електронна бібліотека — {name}")
        self.navigate("library_all")
        self.library.reload()

    def prepare_logout(self) -> None:
        self.close_reader_safely()
        self.global_search.clear()
        self.status_label.setText("Вийшли з акаунту")

    def is_busy(self) -> bool:
        return self._busy

    def is_reader_open(self) -> bool:
        return self.stack.currentWidget() is self.reader and self.reader.book_id is not None

    def close_reader_safely(self) -> None:
        try:
            if self.reader.book_id is not None:
                self.reader.close_reader()
        except Exception:  # noqa: BLE001
            pass

    def _install_shortcuts(self) -> None:
        QShortcut(QKeySequence("Ctrl+O"), self, self._quick_import)
        QShortcut(QKeySequence("Ctrl+F"), self, lambda: self.global_search.setFocus())
        QShortcut(QKeySequence("Ctrl+1"), self, lambda: self.navigate("library_all"))
        QShortcut(QKeySequence("Ctrl+,"), self, lambda: self.navigate("settings"))

    def navigate(self, key: str) -> None:
        if key.startswith("library_"):
            self.stack.setCurrentWidget(self.library)
            self.library.set_preset(key)
        elif key == "import":
            self.stack.setCurrentWidget(self.import_page)
        elif key in {"collections", "genres", "authors", "tags"}:
            self.stack.setCurrentWidget(self.org)
            self.org.show_mode(key)
        elif key in {"quotes", "notes", "bookmarks"}:
            self.stack.setCurrentWidget(self.materials)
            self.materials.show_mode(key)
        elif key in {"stats", "calendar", "goals"}:
            self.stack.setCurrentWidget(self.analytics)
            self.analytics.show_mode(key)
        elif key == "tools":
            self.stack.setCurrentWidget(self.tools)
            self.tools.reload()
        elif key == "settings":
            self.stack.setCurrentWidget(self.settings_page)
            self.settings_page.reload()
        elif key == "search":
            self.stack.setCurrentWidget(self.search_page)
        elif key == "reader":
            self.stack.setCurrentWidget(self.reader)
        if key in self.nav.button_keys:
            self.nav.set_active(key)
        self.section_title.setText(PAGE_TITLES.get(key, key))

    def open_reader(self, book_id: int, location=None) -> None:
        self.stack.setCurrentWidget(self.reader)
        self.section_title.setText("Читання")
        self.reader.open_book(book_id, location=location)

    def open_reader_at(self, book_id: int, location) -> None:
        self.open_reader(book_id, location=location)

    def _filter_library(self, filt: dict) -> None:
        self.stack.setCurrentWidget(self.library)
        self.library.set_preset("library_all")
        self.library.set_extra_filter(**filt)
        self.nav.set_active("library_all")
        self.section_title.setText("Усі книги")

    def _quick_import(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Додати книги",
            "",
            "Книги (*.pdf *.epub)",
        )
        if not files:
            return
        self.navigate("import")
        self.import_page.add_paths(files)

    def import_paths(self, paths: list[str]) -> None:
        self.navigate("import")
        self.import_page.add_paths(paths)

    def _run_global_search(self) -> None:
        q = self.global_search.text().strip()
        if len(q) < 2:
            if self.stack.currentWidget() is self.search_page:
                self.search_page.set_query("")
            return
        self.navigate("search")
        self.search_page.set_query(q)

    def _set_busy(self, busy: bool, text: str = "") -> None:
        self._busy = busy
        self.busy_bar.setVisible(busy)
        self.busy_label.setText(text if busy else "")
        if text:
            self.status_label.setText(text)

    def _toast(self, message: str, kind: str = "info") -> None:
        self.toast.show_message(message, kind=kind)
        self.status_label.setText(message)

    def _toggle_theme(self) -> None:
        name = "dark" if self.settings.get_theme() != "dark" else "light"
        self.settings.set_theme(name)
        self._apply_theme(name)

    def _apply_theme(self, name: str) -> None:
        apply_theme(name)
        self.theme_manager.set_theme(name)
        self.nav.apply_theme(name)
        self._refresh_theme_icon(name)

    def _refresh_theme_icon(self, name: str) -> None:
        tokens = DARK if name == "dark" else LIGHT
        # Moon in light theme (switch to dark); sun in dark theme (switch to light)
        icon_name = "theme_moon" if name != "dark" else "theme_sun"
        self.theme_btn.setIcon(load_icon(icon_name, tokens.text, 18))
        self.theme_btn.setIconSize(QSize(18, 18))

    def closeEvent(self, event) -> None:  # noqa: N802
        self.close_reader_safely()
        self.settings.sync()
        # Logout path reuses window; only quit app when user closes main window
        event.accept()
        # Do not shutdown backend here — run.py owns lifecycle; if user closes window, quit app
        from PySide6.QtWidgets import QApplication

        QApplication.instance().quit()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self.toast._reposition()
