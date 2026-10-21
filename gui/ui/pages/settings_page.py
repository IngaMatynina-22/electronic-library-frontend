from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from gui import __version__
from gui.ui.utils.errors import user_message


class SettingsPage(QWidget):
    theme_changed = Signal(str)
    toast = Signal(str, str)

    def __init__(self, container, settings, theme_manager, parent=None) -> None:
        super().__init__(parent)
        self.container = container
        self.settings = settings
        self.theme_manager = theme_manager

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        title = QLabel("Налаштування")
        title.setObjectName("PageTitle")
        root.addWidget(title)

        appearance = QGroupBox("Зовнішній вигляд застосунку")
        form = QFormLayout(appearance)
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Світла", "light")
        self.theme_combo.addItem("Темна", "dark")
        idx = self.theme_combo.findData(settings.get_theme())
        if idx >= 0:
            self.theme_combo.setCurrentIndex(idx)
        self.theme_combo.currentIndexChanged.connect(self._theme)
        form.addRow("Тема інтерфейсу", self.theme_combo)
        hint = QLabel("Змінює кольори вікон, навігації та бібліотеки.")
        hint.setObjectName("HintLabel")
        hint.setWordWrap(True)
        form.addRow("", hint)
        root.addWidget(appearance)

        library = QGroupBox("Бібліотека")
        lform = QFormLayout(library)
        self.view_combo = QComboBox()
        self.view_combo.addItem("Сітка обкладинок", "grid")
        self.view_combo.addItem("Компактний список", "list")
        vidx = self.view_combo.findData(settings.get_library_view())
        if vidx >= 0:
            self.view_combo.setCurrentIndex(vidx)
        self.view_combo.currentIndexChanged.connect(
            lambda: settings.set_library_view(self.view_combo.currentData())
        )
        lform.addRow("Подання за замовчуванням", self.view_combo)
        root.addWidget(library)

        reading = QGroupBox("Читання (лише вміст книги)")
        rform = QFormLayout(reading)
        note = QLabel(
            "Ці параметри застосовуються в режимі читання. "
            "Тема читача не змінює тему всього застосунку."
        )
        note.setObjectName("HintLabel")
        note.setWordWrap(True)
        rform.addRow(note)
        self.font_size = QSpinBox()
        self.font_size.setRange(12, 32)
        self.reader_theme = QComboBox()
        for data, label in (("light", "Світла"), ("dark", "Темна"), ("paper", "Папір")):
            self.reader_theme.addItem(label, data)
        try:
            prefs = container.reader_prefs.get(None)
            if prefs.font_size:
                self.font_size.setValue(prefs.font_size)
            else:
                self.font_size.setValue(16)
            if prefs.theme:
                i = self.reader_theme.findData(prefs.theme)
                if i >= 0:
                    self.reader_theme.setCurrentIndex(i)
        except Exception:  # noqa: BLE001
            self.font_size.setValue(16)
        save_r = QPushButton("Зберегти налаштування читача")
        save_r.setObjectName("PrimaryButton")
        save_r.clicked.connect(self._save_reader)
        rform.addRow("Розмір шрифту EPUB", self.font_size)
        rform.addRow("Тема тексту в читачі", self.reader_theme)
        rform.addRow(save_r)
        root.addWidget(reading)

        account = QGroupBox("Обліковий запис")
        aform = QFormLayout(account)
        self.old_pass = QLineEdit()
        self.old_pass.setEchoMode(QLineEdit.Password)
        self.new_pass = QLineEdit()
        self.new_pass.setEchoMode(QLineEdit.Password)
        change_btn = QPushButton("Змінити пароль")
        change_btn.clicked.connect(self._change_password)
        aform.addRow("Поточний пароль", self.old_pass)
        aform.addRow("Новий пароль", self.new_pass)
        aform.addRow(change_btn)
        root.addWidget(account)

        data = QGroupBox("Дані та резервні копії")
        dform = QVBoxLayout(data)
        self.data_path = QLabel(str(container.config.data_dir))
        self.data_path.setObjectName("MutedLabel")
        self.data_path.setWordWrap(True)
        dform.addWidget(QLabel("Каталог сховища:"))
        dform.addWidget(self.data_path)
        brow = QHBoxLayout()
        backup_btn = QPushButton("Створити резервну копію")
        backup_btn.clicked.connect(self._backup)
        restore_btn = QPushButton("Відновити з копії…")
        restore_btn.clicked.connect(self._restore)
        brow.addWidget(backup_btn)
        brow.addWidget(restore_btn)
        brow.addStretch(1)
        dform.addLayout(brow)
        root.addWidget(data)

        about = QGroupBox("Про застосунок")
        aform2 = QVBoxLayout(about)
        ocr_ok = False
        try:
            ocr_ok = container.ocr.is_available()
        except Exception:  # noqa: BLE001
            ocr_ok = False
        aform2.addWidget(QLabel(f"Версія: {__version__}"))
        aform2.addWidget(QLabel("Формати: PDF, EPUB"))
        aform2.addWidget(
            QLabel("OCR (Tesseract): " + ("доступний" if ocr_ok else "недоступний"))
        )
        root.addWidget(about)
        root.addStretch(1)

    def reload(self) -> None:
        self.data_path.setText(str(self.container.config.data_dir))
        idx = self.theme_combo.findData(self.settings.get_theme())
        if idx >= 0:
            self.theme_combo.blockSignals(True)
            self.theme_combo.setCurrentIndex(idx)
            self.theme_combo.blockSignals(False)

    def _theme(self) -> None:
        name = self.theme_combo.currentData()
        self.settings.set_theme(name)
        self.theme_changed.emit(name)

    def _change_password(self) -> None:
        try:
            self.container.auth.change_password(
                self.old_pass.text(), self.new_pass.text()
            )
            self.old_pass.clear()
            self.new_pass.clear()
            self.toast.emit("Пароль змінено", "success")
        except Exception as exc:  # noqa: BLE001
            self.toast.emit(user_message(exc), "error")

    def _save_reader(self) -> None:
        try:
            self.container.reader_prefs.set(
                font_size=self.font_size.value(),
                theme=self.reader_theme.currentData(),
            )
            self.toast.emit("Налаштування читача збережено", "success")
        except Exception as exc:  # noqa: BLE001
            self.toast.emit(user_message(exc), "error")

    def _backup(self) -> None:
        try:
            result = self.container.backup.create_backup(include_files=True)
            if result.success:
                self.toast.emit(f"Копію створено: {result.path}", "success")
            else:
                self.toast.emit(result.message or "Не вдалося створити копію", "error")
        except Exception as exc:  # noqa: BLE001
            self.toast.emit(user_message(exc), "error")

    def _restore(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Відновити з копії", str(self.container.config.backups_dir), "ZIP (*.zip)"
        )
        if not path:
            return
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Warning)
        box.setWindowTitle("Відновлення")
        box.setText("Поточну бібліотеку буде замінено даними з архіву.")
        box.setInformativeText("Продовжити?")
        box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        if box.exec() != QMessageBox.Yes:
            return
        try:
            result = self.container.backup.restore_backup(path)
            if getattr(result, "success", True):
                self.toast.emit("Відновлення завершено. Перезапустіть застосунок.", "success")
            else:
                self.toast.emit(getattr(result, "message", "Помилка відновлення"), "error")
        except Exception as exc:  # noqa: BLE001
            self.toast.emit(user_message(exc), "error")
