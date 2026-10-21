from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
    QLabel,
)

from gui.ui.utils.formatters import STATUS_LABELS


class BulkEditDialog(QDialog):
    def __init__(self, count: int, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Масове редагування")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Буде змінено книг: {count}"))

        form = QFormLayout()
        self.use_status = QCheckBox("Змінити статус")
        self.status = QComboBox()
        for k, v in STATUS_LABELS.items():
            self.status.addItem(v, k)
        self.use_rating = QCheckBox("Змінити рейтинг")
        self.rating = QSpinBox()
        self.rating.setRange(0, 5)
        self.use_favorite = QCheckBox("Позначити як вибране")
        self.favorite = QComboBox()
        self.favorite.addItem("Так", True)
        self.favorite.addItem("Ні", False)
        self.use_authors = QCheckBox("Автори (замінити)")
        self.authors = QLineEdit()
        self.use_genres = QCheckBox("Жанри (замінити)")
        self.genres = QLineEdit()

        form.addRow(self.use_status, self.status)
        form.addRow(self.use_rating, self.rating)
        form.addRow(self.use_favorite, self.favorite)
        form.addRow(self.use_authors, self.authors)
        form.addRow(self.use_genres, self.genres)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Застосувати")
        buttons.button(QDialogButtonBox.Cancel).setText("Скасувати")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def kwargs(self) -> dict:
        out: dict = {}
        if self.use_status.isChecked():
            out["status"] = self.status.currentData()
        if self.use_rating.isChecked():
            out["rating"] = self.rating.value() or None
        if self.use_favorite.isChecked():
            out["is_favorite"] = self.favorite.currentData()
        if self.use_authors.isChecked():
            names = [a.strip() for a in self.authors.text().split(",") if a.strip()]
            out["author_names"] = names
        if self.use_genres.isChecked():
            names = [g.strip() for g in self.genres.text().split(",") if g.strip()]
            out["genre_names"] = names
        return out
