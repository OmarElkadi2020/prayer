#!/usr/bin/env python3
"""
adhan_gui.py – نافذة رسومية لعرض مواقيت الصلاة والعدّ التنازلي
"""

from __future__ import annotations
import datetime as dt
from datetime import timedelta
from zoneinfo import ZoneInfo
import tkinter as tk
from tkinter import ttk

from src import adhan_player

CITY = "Deggendorf"
COUNTRY = "Germany"
METHOD = 3
SCHOOL = 0
TZ = adhan_player.DEFAULT_TZ


class AdhanWindow(ttk.Frame):
    def __init__(self, master: tk.Tk):
        super().__init__(master, padding=20)
        master.title("Prayer Times – مواقيت الصلاة")
        master.resizable(False, False)

        # رأس
        self.title_lbl = ttk.Label(self, text="", font=("Helvetica", 16, "bold"))
        self.title_lbl.grid(column=0, row=0, columnspan=2, pady=(0, 10))

        # جدول المواقيت
        # ── بعد التعديل ─────────────────────────
        self.tree = ttk.Treeview(
            self,
            columns=("prayer", "time"),
            show="headings",
            height=7,
        )
        self.tree.heading("prayer", text="Prayer")
        self.tree.heading("time",   text="Time")

        self.tree.column("prayer", anchor="center", width=90)
        self.tree.column("time",   anchor="center", width=80)
        self.tree.grid(column=0, row=1, columnspan=2, pady=10)

        # عداد
        self.next_lbl = ttk.Label(self, text="", font=("Helvetica", 14))
        self.next_lbl.grid(column=0, row=2, columnspan=2, pady=(0, 10))

        self.grid()
        self.refresh_times()
        self.update_clock()

    # ------------------------------------------------------------------ #
    #               جلب المواقيت وتحديث الجدول / العنوان                 #
    # ------------------------------------------------------------------ #
    def refresh_times(self):
        self.today = dt.datetime.now(ZoneInfo(TZ)).date()
        self.times = adhan_player.fetch_prayer_times(
            CITY, COUNTRY, METHOD, SCHOOL, TZ, self.today
        )

        # ملء الجدول
        self.tree.delete(*self.tree.get_children())
        for prayer, at in self.times.items():
            self.tree.insert("", "end", values=(prayer, at.strftime("%H:%M")))

        self.title_lbl.configure(text=f"{CITY} – {self.today.isoformat()}")

        # حدّد الأذان التالي
        self.compute_next()

        # جدولة تحديث المواقيت بعد منتصف الليل + 10 ثوانٍ
        now = dt.datetime.now(ZoneInfo(TZ))
        tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=10)
        delay = int((tomorrow - now).total_seconds() * 1000)
        self.after(delay, self.refresh_times)

    # ------------------------------------------------------------------ #
    #            تحديد الصلاة التالية ووقت بقائها                        #
    # ------------------------------------------------------------------ #
    def compute_next(self):
        now = dt.datetime.now(ZoneInfo(TZ))
        future = {p: t for p, t in self.times.items() if t > now}
        if not future:
            # انتهت الصلوات لليوم؛ التالية فجر الغد
            next_prayer = "Fajr"
            tmrw = now + timedelta(days=1)
            next_time = adhan_player.fetch_prayer_times(
                CITY, COUNTRY, METHOD, SCHOOL, TZ, tmrw.date()
            )[next_prayer]
        else:
            next_prayer, next_time = min(future.items(), key=lambda kv: kv[1])
        self.next_prayer = next_prayer
        self.next_time = next_time

    # ------------------------------------------------------------------ #
    #                  تحديث العدّ التنازلي كل ثانية                     #
    # ------------------------------------------------------------------ #
    def update_clock(self):
        now = dt.datetime.now(ZoneInfo(TZ))
        remaining = self.next_time - now
        if remaining.total_seconds() <= 0:
            self.compute_next()
            remaining = self.next_time - now

        hh, mm = divmod(int(remaining.total_seconds()), 3600)
        mm, ss = divmod(mm, 60)
        self.next_lbl.configure(
            text=f"Next: {self.next_prayer} in {hh:02d}:{mm:02d}:{ss:02d}"
        )
        self.after(1000, self.update_clock)


def main():
    root = tk.Tk()
    AdhanWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
