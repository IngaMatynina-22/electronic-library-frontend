from __future__ import annotations

from calendar import monthrange
from datetime import date

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from gui.ui.dialogs.goal_dialog import GoalDialog
from gui.ui.utils.errors import user_message
from gui.ui.utils.formatters import format_duration

try:
    from PySide6.QtCharts import (
        QBarCategoryAxis,
        QBarSeries,
        QBarSet,
        QChart,
        QChartView,
        QPieSeries,
        QValueAxis,
    )
    from PySide6.QtGui import QPainter

    HAS_CHARTS = True
except Exception:  # noqa: BLE001
    HAS_CHARTS = False


class AnalyticsPage(QWidget):
    toast = Signal(str, str)

    def __init__(self, container, parent=None) -> None:
        super().__init__(parent)
        self.container = container
        self._mode = "stats"
        self._year = date.today().year
        self._month = date.today().month

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        self.title = QLabel("Аналітика")
        self.title.setObjectName("PageTitle")
        root.addWidget(self.title)

        self.stats_box = QWidget()
        stats_l = QVBoxLayout(self.stats_box)
        stats_l.setContentsMargins(0, 0, 0, 0)
        self.stats_labels: dict[str, QLabel] = {}
        summary = QHBoxLayout()
        for key, caption in [
            ("total", "Усього"),
            ("completed", "Прочитано"),
            ("reading", "Читаю"),
            ("planned", "У планах"),
            ("time", "Час"),
        ]:
            cell = QVBoxLayout()
            cap = QLabel(caption)
            cap.setObjectName("MutedLabel")
            val = QLabel("—")
            val.setStyleSheet("font-size: 18px; font-weight: 600;")
            self.stats_labels[key] = val
            cell.addWidget(cap)
            cell.addWidget(val)
            summary.addLayout(cell)
        stats_l.addLayout(summary)

        charts_row = QHBoxLayout()
        self.status_chart_host = QVBoxLayout()
        self.genre_chart_host = QVBoxLayout()
        charts_row.addLayout(self.status_chart_host, 1)
        charts_row.addLayout(self.genre_chart_host, 1)
        stats_l.addLayout(charts_row, 1)
        self.genre_list = QListWidget()
        self.genre_list.setMaximumHeight(120)
        stats_l.addWidget(QLabel("Жанри (список)"))
        stats_l.addWidget(self.genre_list)
        root.addWidget(self.stats_box)

        self.cal_box = QWidget()
        cal_l = QVBoxLayout(self.cal_box)
        cal_l.setContentsMargins(0, 0, 0, 0)
        nav = QHBoxLayout()
        prev = QPushButton("◀")
        nxt = QPushButton("▶")
        prev.clicked.connect(self._prev_month)
        nxt.clicked.connect(self._next_month)
        self.month_lbl = QLabel("")
        nav.addWidget(prev)
        nav.addWidget(self.month_lbl, 1, Qt.AlignCenter)
        nav.addWidget(nxt)
        cal_l.addLayout(nav)
        self.activity_chart_host = QVBoxLayout()
        cal_l.addLayout(self.activity_chart_host, 1)
        self.cal_grid = QGridLayout()
        cal_l.addLayout(self.cal_grid)
        self.day_detail = QLabel("Оберіть день")
        self.day_detail.setObjectName("MutedLabel")
        cal_l.addWidget(self.day_detail)
        root.addWidget(self.cal_box)

        self.goals_box = QWidget()
        goals_l = QVBoxLayout(self.goals_box)
        goals_l.setContentsMargins(0, 0, 0, 0)
        g_row = QHBoxLayout()
        add_g = QPushButton("Створити / оновити ціль")
        add_g.setObjectName("PrimaryButton")
        add_g.clicked.connect(self._edit_goal)
        del_g = QPushButton("Видалити ціль")
        del_g.clicked.connect(self._delete_goal)
        g_row.addWidget(add_g)
        g_row.addWidget(del_g)
        g_row.addStretch(1)
        goals_l.addLayout(g_row)
        self.goals_list = QListWidget()
        goals_l.addWidget(self.goals_list, 1)
        self.goal_bar = QProgressBar()
        goals_l.addWidget(self.goal_bar)
        root.addWidget(self.goals_box)

        self._chart_views: list = []

    def show_mode(self, mode: str) -> None:
        self._mode = mode
        titles = {
            "stats": "Статистика читання",
            "calendar": "Календар активності",
            "goals": "Цілі читання",
        }
        self.title.setText(titles.get(mode, "Аналітика"))
        self.stats_box.setVisible(mode == "stats")
        self.cal_box.setVisible(mode == "calendar")
        self.goals_box.setVisible(mode == "goals")
        self.reload()

    def _clear_layout(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def reload(self) -> None:
        try:
            if self._mode == "stats":
                s = self.container.statistics.get_library_stats()
                r = self.container.statistics.get_reading_stats()
                self.stats_labels["total"].setText(str(s.total_books))
                self.stats_labels["completed"].setText(str(s.completed_books))
                self.stats_labels["reading"].setText(str(s.reading_books))
                self.stats_labels["planned"].setText(str(s.planned_books))
                self.stats_labels["time"].setText(format_duration(r.total_reading_seconds))
                self.genre_list.clear()
                genres = s.books_by_genre or self.container.statistics.get_genre_stats()
                for name, count in sorted(genres.items(), key=lambda kv: -kv[1]):
                    self.genre_list.addItem(f"{name}: {count}")
                self._render_status_chart(s)
                self._render_genre_chart(genres)
            elif self._mode == "calendar":
                self._render_calendar()
                self._render_activity_chart()
            else:
                self.goals_list.clear()
                goals = self.container.statistics.list_goals()
                current = None
                for g in goals:
                    self.goals_list.addItem(
                        f"{g.year}: {g.completed_books}/{g.target_books} "
                        f"({g.progress_percent:.0f}%)"
                    )
                    if g.year == date.today().year:
                        current = g
                if current:
                    self.goal_bar.setRange(0, max(1, current.target_books))
                    self.goal_bar.setValue(current.completed_books)
                    self.goal_bar.setFormat(
                        f"{current.completed_books}/{current.target_books} книг у {current.year}"
                    )
                else:
                    self.goal_bar.setRange(0, 1)
                    self.goal_bar.setValue(0)
                    self.goal_bar.setFormat("Немає цілі на поточний рік")
        except Exception as exc:  # noqa: BLE001
            self.toast.emit(user_message(exc), "error")

    def _render_status_chart(self, s) -> None:
        self._clear_layout(self.status_chart_host)
        if not HAS_CHARTS:
            self.status_chart_host.addWidget(QLabel("QtCharts недоступний"))
            return
        series = QPieSeries()
        for label, value in [
            ("Прочитано", s.completed_books),
            ("Читаю", s.reading_books),
            ("У планах", s.planned_books),
            ("Пауза", getattr(s, "paused_books", 0)),
            ("Відкладено", getattr(s, "abandoned_books", 0)),
        ]:
            if value:
                series.append(f"{label} ({value})", value)
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("За статусом")
        chart.legend().setAlignment(Qt.AlignBottom)
        view = QChartView(chart)
        view.setRenderHint(QPainter.Antialiasing)
        view.setMinimumHeight(220)
        self.status_chart_host.addWidget(view)

    def _render_genre_chart(self, genres: dict) -> None:
        self._clear_layout(self.genre_chart_host)
        if not HAS_CHARTS:
            return
        items = sorted(genres.items(), key=lambda kv: -kv[1])[:8]
        if not items:
            self.genre_chart_host.addWidget(QLabel("Немає даних за жанрами"))
            return
        bar_set = QBarSet("Книги")
        cats = []
        for name, count in items:
            cats.append(name[:12])
            bar_set.append(count)
        series = QBarSeries()
        series.append(bar_set)
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("За жанрами")
        axis_x = QBarCategoryAxis()
        axis_x.append(cats)
        axis_y = QValueAxis()
        axis_y.setRange(0, max(1, max(c for _, c in items)))
        chart.addAxis(axis_x, Qt.AlignBottom)
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_x)
        series.attachAxis(axis_y)
        chart.legend().setVisible(False)
        view = QChartView(chart)
        view.setRenderHint(QPainter.Antialiasing)
        view.setMinimumHeight(220)
        self.genre_chart_host.addWidget(view)

    def _render_activity_chart(self) -> None:
        self._clear_layout(self.activity_chart_host)
        activity = self.container.statistics.get_activity_calendar(self._year)
        _, days = monthrange(self._year, self._month)
        if not HAS_CHARTS:
            return
        bar_set = QBarSet("Хв")
        cats = []
        max_v = 1
        for day in range(1, days + 1):
            key = f"{self._year:04d}-{self._month:02d}-{day:02d}"
            seconds = activity.get(key, 0)
            mins = int(seconds // 60)
            bar_set.append(mins)
            if day == 1 or day % 5 == 0 or day == days:
                cats.append(str(day))
            else:
                cats.append("")
            max_v = max(max_v, mins)
        series = QBarSeries()
        series.append(bar_set)
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle(f"Активність {self._month:02d}.{self._year} (хвилини)")
        axis_x = QBarCategoryAxis()
        axis_x.append(cats)
        axis_y = QValueAxis()
        axis_y.setRange(0, max_v)
        chart.addAxis(axis_x, Qt.AlignBottom)
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_x)
        series.attachAxis(axis_y)
        chart.legend().setVisible(False)
        view = QChartView(chart)
        view.setRenderHint(QPainter.Antialiasing)
        view.setMinimumHeight(200)
        self.activity_chart_host.addWidget(view)

    def _render_calendar(self) -> None:
        while self.cal_grid.count():
            item = self.cal_grid.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self.month_lbl.setText(f"{self._month:02d}.{self._year}")
        activity = self.container.statistics.get_activity_calendar(self._year)
        for i, name in enumerate(["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"]):
            self.cal_grid.addWidget(QLabel(name), 0, i)
        first_weekday, days = monthrange(self._year, self._month)
        row = 1
        col = first_weekday
        for day in range(1, days + 1):
            key = f"{self._year:04d}-{self._month:02d}-{day:02d}"
            seconds = activity.get(key, 0)
            btn = QPushButton(str(day))
            btn.setMinimumSize(36, 32)
            btn.setProperty("activeDay", bool(seconds))
            if seconds:
                btn.setObjectName("ActiveDayButton")
                btn.setToolTip(format_duration(seconds))
            btn.clicked.connect(lambda checked=False, k=key, s=seconds: self._day_clicked(k, s))
            self.cal_grid.addWidget(btn, row, col)
            col += 1
            if col > 6:
                col = 0
                row += 1

    def _day_clicked(self, key: str, seconds: int) -> None:
        if seconds:
            self.day_detail.setText(f"{key}: {format_duration(seconds)} читання")
        else:
            self.day_detail.setText(f"{key}: активності немає")

    def _prev_month(self) -> None:
        if self._month == 1:
            self._month = 12
            self._year -= 1
        else:
            self._month -= 1
        self._render_calendar()
        self._render_activity_chart()

    def _next_month(self) -> None:
        if self._month == 12:
            self._month = 1
            self._year += 1
        else:
            self._month += 1
        self._render_calendar()
        self._render_activity_chart()

    def _edit_goal(self) -> None:
        dlg = GoalDialog(parent=self)
        if not dlg.exec():
            return
        try:
            self.container.statistics.set_goal(dlg.year.value(), dlg.target.value())
            self.toast.emit("Ціль збережено", "success")
            self.reload()
        except Exception as exc:  # noqa: BLE001
            self.toast.emit(user_message(exc), "error")

    def _delete_goal(self) -> None:
        item = self.goals_list.currentItem()
        if not item:
            return
        year = int(item.text().split(":")[0])
        if QMessageBox.question(self, "Видалити", f"Видалити ціль за {year}?") != QMessageBox.Yes:
            return
        try:
            self.container.statistics.delete_goal(year)
            self.toast.emit("Ціль видалено", "success")
            self.reload()
        except Exception as exc:  # noqa: BLE001
            self.toast.emit(user_message(exc), "error")
