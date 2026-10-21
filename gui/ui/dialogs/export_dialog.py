from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)


class ExportDialog(QDialog):
    def __init__(self, books: list | None = None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Експорт матеріалів")
        self.setMinimumWidth(420)
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.format_combo = QComboBox()
        self.format_combo.addItem("Markdown", "markdown")
        self.format_combo.addItem("JSON", "json")

        self.book_combo = QComboBox()
        self.book_combo.addItem("Усі книги", None)
        for b in books or []:
            self.book_combo.addItem(b.title, b.id)

        self.tag_edit = QLineEdit()
        self.tag_edit.setPlaceholderText("Опційно: фільтр за тегом")

        path_row = QHBoxLayout()
        self.path_edit = QLineEdit()
        browse = QPushButton("Огляд…")
        browse.clicked.connect(self._browse)
        path_row.addWidget(self.path_edit, 1)
        path_row.addWidget(browse)

        form.addRow("Формат", self.format_combo)
        form.addRow("Книга", self.book_combo)
        form.addRow("Тег", self.tag_edit)
        form.addRow("Файл", path_row)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Експортувати")
        buttons.button(QDialogButtonBox.Cancel).setText("Скасувати")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse(self) -> None:
        fmt = self.format_combo.currentData()
        ext = "md" if fmt == "markdown" else "json"
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Зберегти експорт",
            str(Path.home() / f"library_export.{ext}"),
            f"*.{ext}",
        )
        if path:
            self.path_edit.setText(path)

    def values(self) -> dict:
        return {
            "destination": self.path_edit.text().strip(),
            "format": self.format_combo.currentData(),
            "book_id": self.book_combo.currentData(),
            "tag": self.tag_edit.text().strip() or None,
        }
