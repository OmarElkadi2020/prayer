from __future__ import annotations
import datetime as dt
from datetime import timedelta
from zoneinfo import ZoneInfo

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QTableWidget, QTableWidgetItem, QHeaderView
from PySide6.QtCore import QTimer, Qt

from src.prayer.prayer_times import today_times
from src.prayer.config import TZ

CITY = "Deggendorf"
COUNTRY = "Germany"
METHOD = 3
SCHOOL = 0



class AdhanWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Prayer Times – مواقيت الصلاة")
        self.setFixedSize(300, 400) # Adjust size as needed

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignCenter)

        # Header
        self.title_lbl = QLabel("")
        self.title_lbl.setStyleSheet("font-size: 16pt; font-weight: bold;")
        self.title_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_lbl)

        # Prayer Times Table
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Prayer", "Time"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setRowCount(7) # Assuming 7 prayers
        layout.addWidget(self.table)

        # Countdown
        self.next_lbl = QLabel("")
        self.next_lbl.setStyleSheet("font-size: 14pt;")
        self.next_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.next_lbl)

        # Set up timers
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_times)
        # This will be set dynamically in refresh_times

        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000) # Update every second

        self.refresh_times()
        self.update_clock()

    def refresh_times(self):
        self.today = dt.datetime.now(TZ).date()
        self.times = today_times(
            CITY, COUNTRY, METHOD, SCHOOL
        )

        # Populate the table
        self.table.setRowCount(0) # Clear existing rows
        for row, (prayer, at) in enumerate(self.times.items()):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(prayer))
            self.table.setItem(row, 1, QTableWidgetItem(at.strftime("%H:%M")))

        self.title_lbl.setText(f"{CITY} – {self.today.isoformat()}")

        self.compute_next()

        # Schedule next refresh
        now = dt.datetime.now(TZ)
        tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=10)
        delay_ms = int((tomorrow - now).total_seconds() * 1000)
        self.refresh_timer.stop() # Stop any previous timer
        self.refresh_timer.start(delay_ms)

    def compute_next(self):
        now = dt.datetime.now(TZ)
        future = {p: t for p, t in self.times.items() if t > now}
        if not future:
            # All prayers for today are over; next is Fajr of tomorrow
            next_prayer = "Fajr"
            tmrw = now + timedelta(days=1)
            next_time = today_times(
                CITY, COUNTRY, METHOD, SCHOOL
            )[next_prayer]
        else:
            next_prayer, next_time = min(future.items(), key=lambda kv: kv[1])
        self.next_prayer = next_prayer
        self.next_time = next_time

    def update_clock(self):
        now = dt.datetime.now(TZ)
        remaining = self.next_time - now
        if remaining.total_seconds() <= 0:
            self.compute_next()
            remaining = self.next_time - now

        hh, mm = divmod(int(remaining.total_seconds()), 3600)
        mm, ss = divmod(mm, 60)
        self.next_lbl.setText(f"Next: {self.next_prayer} in {hh:02d}:{mm:02d}:{ss:02d}")


def main():
    app = QApplication([])
    window = AdhanWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
