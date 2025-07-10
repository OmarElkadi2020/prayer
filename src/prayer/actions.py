# ---------------------------------------------------------------------------
# actions.py – shell helpers, focus‑mode, audio playback
# ---------------------------------------------------------------------------

from __future__ import annotations
import subprocess, sys, os
from datetime import datetime, timedelta
from typing import Set

from apscheduler.schedulers.blocking import BlockingScheduler

from .config import TZ, LOG, NET_OFF_CMD, NET_ON_CMD, FOCUS_DELAY, FOCUS_LENGTH

KEEP_PIDS: Set[int] = {os.getpid(), os.getppid()}


# -- utility --------------------------------------------------------------

def _safe_close():
    try:
        out = subprocess.check_output(["wmctrl", "-l", "-p"], text=True, timeout=2)
    except FileNotFoundError:
        LOG.warning("wmctrl missing – cannot close windows")
        return
    keep = {ln.split()[0] for ln in out.splitlines() if int(ln.split()[2]) in KEEP_PIDS or ln.endswith("تهيئة الخشوع")}
    for ln in out.splitlines():
        wid = ln.split()[0]
        if wid not in keep:
            subprocess.call(["wmctrl", "-ic", wid])


# -- focus mode -----------------------------------------------------------

import os
def focus_mode():
    LOG.info("🕌 Focus‑mode ON")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    focus_script = os.path.join(script_dir, "focus_steps.py")  # أو المسار المناسب
    env = os.environ.copy()
    # ✦ أضف <DISPLAY و/أو Wayland إذا كانت مفقودة
    if "WAYLAND_DISPLAY" in env:                # تعمل على Wayland
        env.setdefault("QT_QPA_PLATFORM", "wayland")
    else:                                       # غالبًا X11
        env.setdefault("DISPLAY", ":0")
        env.setdefault("QT_QPA_PLATFORM", "xcb")

    env["PYTHONPATH"] = script_dir + (":" + env.get("PYTHONPATH", ""))
    subprocess.Popen(
        [sys.executable, focus_script],
        cwd=script_dir,
        env=env
    )
    subprocess.call(NET_OFF_CMD, shell=True)
    # _safe_close()
    resume = datetime.now(TZ) + FOCUS_LENGTH
    tmp_scheduler = BlockingScheduler(timezone=TZ)
    tmp_scheduler.add_job(lambda: (subprocess.call(NET_ON_CMD, shell=True), LOG.info("🌐 Net back")), "date", run_date=resume)
    tmp_scheduler.start(paused=False)

# -- audio playback ---
def play(cmd: str):
    LOG.info("📢 Play %s", cmd)
    subprocess.Popen(cmd, shell=True)