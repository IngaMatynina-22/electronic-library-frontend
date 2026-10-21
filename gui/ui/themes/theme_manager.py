"""Apply QSS from theme tokens."""

from __future__ import annotations

from PySide6.QtGui import QFont, QPalette, QColor
from PySide6.QtWidgets import QApplication

from .tokens import DARK, LIGHT, ThemeTokens


def _qss(t: ThemeTokens) -> str:
    return f"""
    * {{
        font-family: "Segoe UI", "Ubuntu", sans-serif;
        font-size: 13px;
    }}
    QMainWindow, QDialog {{
        background: {t.bg};
        color: {t.text};
    }}
    QWidget {{
        background: transparent;
        color: {t.text};
    }}
    QWidget#AppRoot, QStackedWidget, QSplitter {{
        background: {t.bg};
    }}
    QFrame#LibraryToolbar {{
        background: {t.bg};
        border: none;
    }}
    QWidget#DetailBody, QScrollArea#DetailScroll {{
        background: {t.surface};
        border: none;
    }}
    QFrame#NavPanel {{
        background: {t.nav_bg};
        border-right: 1px solid {t.border};
    }}
    QFrame#TopBar, QFrame#StatusBar {{
        background: {t.surface};
        border-bottom: 1px solid {t.border};
    }}
    QFrame#StatusBar {{
        border-top: 1px solid {t.border};
        border-bottom: none;
    }}
    QFrame#ContentSurface, QFrame#DetailPanel {{
        background: {t.surface};
        border: 1px solid {t.border};
        border-radius: 6px;
    }}
    QFrame#BookCardMeta {{
        background: transparent;
        border: none;
    }}
    QPushButton {{
        background: {t.surface};
        border: 1px solid {t.border};
        border-radius: 4px;
        padding: 6px 12px;
        min-height: 28px;
    }}
    QPushButton:hover {{
        background: {t.surface_alt};
        border-color: {t.accent};
    }}
    QPushButton:focus {{
        border: 2px solid {t.focus};
    }}
    QPushButton#IconToolButton {{
        padding: 4px;
        min-width: 28px;
        min-height: 28px;
    }}
    QPushButton#PrimaryButton {{
        background: {t.accent};
        color: #FFFFFF;
        border: 1px solid {t.accent};
        font-weight: 600;
    }}
    QPushButton#PrimaryButton:hover {{
        background: {t.accent_hover};
    }}
    QPushButton#DangerButton {{
        background: {t.surface};
        color: {t.danger};
        border: 1px solid {t.danger};
    }}
    QPushButton#NavButton {{
        text-align: left;
        padding: 8px 12px;
        border: none;
        border-radius: 4px;
        background: transparent;
    }}
    QPushButton#NavButton:hover {{
        background: {t.nav_hover};
    }}
    QPushButton#NavButton[active="true"] {{
        background: {t.accent_muted};
        color: {t.accent};
        font-weight: 600;
    }}
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QPlainTextEdit {{
        background: {t.surface};
        border: 1px solid {t.border};
        border-radius: 4px;
        padding: 6px 8px;
        selection-background-color: {t.accent};
        selection-color: #FFFFFF;
    }}
    QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QPlainTextEdit:focus {{
        border: 2px solid {t.focus};
    }}
    QListView, QTableView, QTreeView, QListWidget {{
        background: {t.bg};
        border: 1px solid {t.border};
        border-radius: 8px;
        alternate-background-color: {t.surface_alt};
        outline: none;
    }}
    QListWidget#CoverGrid {{
        background: {t.bg};
        border: none;
        padding: 4px;
    }}
    QListWidget#CoverGrid::item {{
        background: transparent;
        border: none;
        padding: 0px;
        margin: 0px;
    }}
    QListWidget#CoverGrid::item:selected {{
        background: transparent;
        border: none;
    }}
    QListView::item:selected, QTableView::item:selected, QTreeView::item:selected {{
        background: {t.accent_muted};
        color: {t.text};
    }}
    QListWidget#OrgSideList::item {{
        padding: 8px 10px;
        border-radius: 6px;
        margin: 2px 4px;
    }}
    QListWidget#OrgSideList::item:selected {{
        background: {t.accent_muted};
        color: {t.text};
    }}
    QHeaderView::section {{
        background: {t.surface_alt};
        color: {t.text_secondary};
        border: none;
        border-bottom: 1px solid {t.border};
        padding: 6px 8px;
        font-weight: 600;
    }}
    QScrollBar:vertical {{
        background: {t.bg};
        width: 10px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {t.border};
        border-radius: 4px;
        min-height: 24px;
    }}
    QLabel#PageTitle {{
        font-size: 18px;
        font-weight: 600;
        color: {t.text};
    }}
    QLabel#MutedLabel, QLabel#MetaLabel {{
        color: {t.text_secondary};
    }}
    QLabel#BookTitle {{
        font-family: "Georgia", "Times New Roman", serif;
        font-size: 16px;
        font-weight: 600;
        margin-top: 6px;
        padding-top: 4px;
        background: transparent;
    }}
    QProgressBar {{
        border: 1px solid {t.border};
        border-radius: 3px;
        background: {t.surface_alt};
        text-align: center;
        max-height: 10px;
    }}
    QProgressBar::chunk {{
        background: {t.accent};
        border-radius: 2px;
    }}
    QToolTip {{
        background: {t.surface};
        color: {t.text};
        border: 1px solid {t.border};
        padding: 4px 8px;
    }}
    QMenu {{
        background: {t.surface};
        border: 1px solid {t.border};
    }}
    QMenu::item:selected {{
        background: {t.accent_muted};
    }}
    QSplitter::handle {{
        background: {t.border};
        width: 1px;
        height: 1px;
    }}
    QTabWidget::pane {{
        border: 1px solid {t.border};
        background: {t.surface};
        border-radius: 4px;
    }}
    QTabBar::tab {{
        background: {t.surface_alt};
        border: 1px solid {t.border};
        padding: 6px 14px;
        margin-right: 2px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }}
    QTabBar::tab:selected {{
        background: {t.surface};
        color: {t.accent};
        font-weight: 600;
    }}
    QGroupBox {{
        border: 1px solid {t.border};
        border-radius: 4px;
        margin-top: 12px;
        padding-top: 12px;
        font-weight: 600;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 4px;
    }}
    QWidget#AuthRoot {{
        background: {t.bg};
    }}
    QFrame#AuthCard {{
        background: {t.surface};
        border: 1px solid {t.border};
        border-radius: 10px;
    }}
    QLabel#ErrorLabel {{
        color: {t.danger};
        font-weight: 600;
    }}
    QFrame#BookCard {{
        background: {t.surface};
        border: 2px solid {t.border};
        border-radius: 14px;
    }}
    QFrame#BookCard:hover {{
        border-color: {t.accent};
    }}
    QFrame#BookCard[selected="true"] {{
        border: 2px solid {t.accent};
        background: {t.accent_muted};
    }}
    QFrame#FolderCard {{
        background: {t.surface};
        border: 2px solid {t.border};
        border-radius: 14px;
    }}
    QFrame#FolderCard:hover {{
        border-color: {t.accent};
    }}
    QLabel#BookCardTitle {{
        font-family: "Segoe UI", sans-serif;
        font-size: 12px;
        font-weight: 600;
        color: {t.text};
    }}
    QLabel#StatusBadge {{
        color: {t.text_secondary};
        font-size: 11px;
    }}
    QLabel#HintLabel {{
        color: {t.text_secondary};
        font-size: 11px;
        font-weight: 400;
    }}
    QPushButton#ActiveDayButton {{
        background: {t.accent_muted};
        border: 1px solid {t.accent};
        font-weight: 600;
    }}
    QPushButton#NavButton[collapsed="true"] {{
        padding: 10px;
        min-height: 36px;
        text-align: center;
    }}
    QChartView {{
        background: {t.surface};
        border: 1px solid {t.border};
        border-radius: 6px;
    }}
    """


class ThemeManager:
    def __init__(self) -> None:
        self._current = "light"

    @property
    def current(self) -> str:
        return self._current

    def tokens(self) -> ThemeTokens:
        return DARK if self._current == "dark" else LIGHT

    def set_theme(self, name: str, app: QApplication | None = None) -> None:
        self._current = "dark" if name == "dark" else "light"
        apply_theme(self._current, app)


def apply_theme(name: str, app: QApplication | None = None) -> ThemeTokens:
    tokens = DARK if name == "dark" else LIGHT
    application = app or QApplication.instance()
    if application is None:
        return tokens
    application.setStyle("Fusion")
    application.setStyleSheet(_qss(tokens))
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(tokens.bg))
    palette.setColor(QPalette.WindowText, QColor(tokens.text))
    palette.setColor(QPalette.Base, QColor(tokens.surface))
    palette.setColor(QPalette.AlternateBase, QColor(tokens.surface_alt))
    palette.setColor(QPalette.Text, QColor(tokens.text))
    palette.setColor(QPalette.Button, QColor(tokens.surface))
    palette.setColor(QPalette.ButtonText, QColor(tokens.text))
    palette.setColor(QPalette.Highlight, QColor(tokens.accent))
    palette.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
    application.setPalette(palette)
    font = QFont("Segoe UI", 10)
    application.setFont(font)
    return tokens
