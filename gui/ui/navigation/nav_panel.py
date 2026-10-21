from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from gui.ui.resources_icons import load_icon
from gui.ui.themes.tokens import DARK, LIGHT
from .nav_items import NAV_SECTIONS, NavItem


class NavPanel(QFrame):
    navigated = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("NavPanel")
        self.setFixedWidth(228)
        self._buttons: dict[str, QPushButton] = {}
        self._section_labels: list[QLabel] = []
        self._items: dict[str, NavItem] = {}
        self._collapsed = False
        self._theme = "light"

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 12, 8, 12)
        root.setSpacing(4)

        self._brand = QLabel("Бібліотека")
        self._brand.setObjectName("PageTitle")
        self._brand.setStyleSheet("font-size: 16px; padding: 4px 8px 12px;")
        root.addWidget(self._brand)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        body = QWidget()
        self._body_layout = QVBoxLayout(body)
        self._body_layout.setContentsMargins(0, 0, 0, 0)
        self._body_layout.setSpacing(2)

        for section_title, items in NAV_SECTIONS:
            sec = QLabel(section_title.upper())
            sec.setObjectName("MutedLabel")
            sec.setStyleSheet(
                "font-size: 10px; letter-spacing: 0.08em; padding: 10px 8px 4px;"
            )
            self._section_labels.append(sec)
            self._body_layout.addWidget(sec)
            for item in items:
                self._items[item.key] = item
                btn = QPushButton(item.label)
                btn.setObjectName("NavButton")
                btn.setCursor(Qt.PointingHandCursor)
                btn.setProperty("active", False)
                btn.setIcon(load_icon(item.icon, self._icon_color()))
                btn.setIconSize(load_icon(item.icon).actualSize(btn.iconSize()) or btn.iconSize())
                from gui.ui.resources_icons import icon_size

                btn.setIconSize(icon_size())
                btn.clicked.connect(lambda checked=False, k=item.key: self._on_click(k))
                self._buttons[item.key] = btn
                self._body_layout.addWidget(btn)

        self._body_layout.addStretch(1)
        scroll.setWidget(body)
        root.addWidget(scroll, 1)

        self._collapse_btn = QPushButton("◂ Згорнути")
        self._collapse_btn.setObjectName("NavButton")
        self._collapse_btn.setToolTip("Згорнути панель")
        self._collapse_btn.clicked.connect(self.toggle_collapse)
        root.addWidget(self._collapse_btn)

    def _icon_color(self) -> str:
        return DARK.accent if self._theme == "dark" else LIGHT.accent

    def apply_theme(self, theme_name: str) -> None:
        self._theme = "dark" if theme_name == "dark" else "light"
        color = self._icon_color()
        for key, btn in self._buttons.items():
            btn.setIcon(load_icon(self._items[key].icon, color))

    def _on_click(self, key: str) -> None:
        self.set_active(key)
        self.navigated.emit(key)

    def set_active(self, key: str) -> None:
        for k, btn in self._buttons.items():
            active = k == key
            btn.setProperty("active", active)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def toggle_collapse(self) -> None:
        self._collapsed = not self._collapsed
        if self._collapsed:
            self.setFixedWidth(56)
            self._brand.setVisible(False)
            for sec in self._section_labels:
                sec.setVisible(False)
            self._collapse_btn.setText("▸")
            self._collapse_btn.setToolTip("Розгорнути панель")
            for key, btn in self._buttons.items():
                item = self._items[key]
                btn.setText("")
                btn.setToolTip(item.label)
                btn.setProperty("collapsed", True)
        else:
            self.setFixedWidth(228)
            self._brand.setVisible(True)
            for sec in self._section_labels:
                sec.setVisible(True)
            self._collapse_btn.setText("◂ Згорнути")
            self._collapse_btn.setToolTip("Згорнути панель")
            for key, btn in self._buttons.items():
                item = self._items[key]
                btn.setText(item.label)
                btn.setToolTip("")
                btn.setProperty("collapsed", False)

    @property
    def button_keys(self) -> set[str]:
        return set(self._buttons.keys())
