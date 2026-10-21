from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from gui.ui.utils.errors import user_message


class AuthPage(QWidget):
    authenticated = Signal(object)

    def __init__(self, container, parent=None) -> None:
        super().__init__(parent)
        self.container = container
        self.setObjectName("AuthRoot")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)

        card = QFrame()
        card.setObjectName("AuthCard")
        card.setMaximumWidth(420)
        card_l = QVBoxLayout(card)
        card_l.setContentsMargins(28, 28, 28, 28)
        card_l.setSpacing(16)

        brand = QLabel("Персональна бібліотека")
        brand.setObjectName("PageTitle")
        brand.setAlignment(Qt.AlignCenter)
        subtitle = QLabel("Увійдіть або створіть акаунт, щоб відкрити свою бібліотеку.")
        subtitle.setObjectName("MutedLabel")
        subtitle.setWordWrap(True)
        subtitle.setAlignment(Qt.AlignCenter)
        card_l.addWidget(brand)
        card_l.addWidget(subtitle)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_login(), "Вхід")
        self.tabs.addTab(self._build_register(), "Реєстрація")
        card_l.addWidget(self.tabs)

        self.error = QLabel("")
        self.error.setObjectName("ErrorLabel")
        self.error.setWordWrap(True)
        self.error.setVisible(False)
        card_l.addWidget(self.error)

        hint = QLabel("Демо (після seed): demo / demo1234")
        hint.setObjectName("MutedLabel")
        hint.setAlignment(Qt.AlignCenter)
        card_l.addWidget(hint)

        outer.addStretch(1)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(card)
        row.addStretch(1)
        outer.addLayout(row)
        outer.addStretch(1)

        last = container.auth.last_username()
        if last:
            self.login_user.setText(last)

    def _build_login(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        form.setSpacing(10)
        self.login_user = QLineEdit()
        self.login_user.setPlaceholderText("Імʼя користувача")
        self.login_pass = QLineEdit()
        self.login_pass.setEchoMode(QLineEdit.Password)
        self.login_pass.setPlaceholderText("Пароль")
        self.login_pass.returnPressed.connect(self._do_login)
        btn = QPushButton("Увійти")
        btn.setObjectName("PrimaryButton")
        btn.clicked.connect(self._do_login)
        form.addRow("Користувач", self.login_user)
        form.addRow("Пароль", self.login_pass)
        form.addRow(btn)
        return w

    def _build_register(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        form.setSpacing(10)
        self.reg_user = QLineEdit()
        self.reg_display = QLineEdit()
        self.reg_pass = QLineEdit()
        self.reg_pass.setEchoMode(QLineEdit.Password)
        self.reg_pass2 = QLineEdit()
        self.reg_pass2.setEchoMode(QLineEdit.Password)
        btn = QPushButton("Створити акаунт")
        btn.setObjectName("PrimaryButton")
        btn.clicked.connect(self._do_register)
        form.addRow("Користувач", self.reg_user)
        form.addRow("Імʼя", self.reg_display)
        form.addRow("Пароль", self.reg_pass)
        form.addRow("Повтор пароля", self.reg_pass2)
        form.addRow(btn)
        return w

    def _show_error(self, text: str) -> None:
        self.error.setText(text)
        self.error.setVisible(bool(text))

    def _do_login(self) -> None:
        try:
            user = self.container.auth.login(
                self.login_user.text().strip(),
                self.login_pass.text(),
            )
            self._show_error("")
            self.authenticated.emit(user)
        except Exception as exc:  # noqa: BLE001
            self._show_error(user_message(exc))

    def _do_register(self) -> None:
        if self.reg_pass.text() != self.reg_pass2.text():
            self._show_error("Паролі не збігаються.")
            return
        try:
            user = self.container.auth.register(
                self.reg_user.text().strip(),
                self.reg_pass.text(),
                display_name=self.reg_display.text().strip() or None,
                auto_login=True,
            )
            self._show_error("")
            self.authenticated.emit(user)
        except Exception as exc:  # noqa: BLE001
            self._show_error(user_message(exc))

    def reset_for_logout(self) -> None:
        self.login_pass.clear()
        self.reg_pass.clear()
        self.reg_pass2.clear()
        last = self.container.auth.last_username()
        if last:
            self.login_user.setText(last)
        self.tabs.setCurrentIndex(0)
        self._show_error("")
