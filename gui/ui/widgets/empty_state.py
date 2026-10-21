from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout


class EmptyState(QFrame):
    action_clicked = Signal()

    def __init__(
        self,
        title: str,
        subtitle: str = "",
        action_text: str | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("ContentSurface")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 48, 32, 48)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignCenter)

        self._title = QLabel(title)
        self._title.setObjectName("PageTitle")
        self._title.setAlignment(Qt.AlignCenter)
        self._title.setWordWrap(True)
        layout.addWidget(self._title)

        self._subtitle = QLabel(subtitle)
        self._subtitle.setObjectName("MutedLabel")
        self._subtitle.setAlignment(Qt.AlignCenter)
        self._subtitle.setWordWrap(True)
        layout.addWidget(self._subtitle)

        self._btn = QPushButton(action_text or "")
        self._btn.setObjectName("PrimaryButton")
        self._btn.setVisible(bool(action_text))
        self._btn.clicked.connect(self.action_clicked.emit)
        layout.addWidget(self._btn, 0, Qt.AlignCenter)

    def set_content(self, title: str, subtitle: str = "", action_text: str | None = None) -> None:
        self._title.setText(title)
        self._subtitle.setText(subtitle)
        self._btn.setText(action_text or "")
        self._btn.setVisible(bool(action_text))
