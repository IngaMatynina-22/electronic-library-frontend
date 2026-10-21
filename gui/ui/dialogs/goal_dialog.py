from __future__ import annotations

from datetime import date

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QSpinBox,
    QVBoxLayout,
)


class GoalDialog(QDialog):
    def __init__(self, year: int | None = None, target: int = 12, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Ціль читання")
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.year = QSpinBox()
        self.year.setRange(2000, 2100)
        self.year.setValue(year or date.today().year)
        self.target = QSpinBox()
        self.target.setRange(1, 1000)
        self.target.setValue(target)
        form.addRow("Рік", self.year)
        form.addRow("Книг на рік", self.target)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("Зберегти")
        buttons.button(QDialogButtonBox.Cancel).setText("Скасувати")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
