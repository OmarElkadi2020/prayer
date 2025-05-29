"""
اختبارات وحدة بسيطة لـ adhan_player.py
$ pip install pytest pytest-mock
$ pytest -q
"""

import types
from datetime import datetime, timezone, timedelta

import pytest

from . import adhan_player

def _fake_response(payload: dict, status: int = 200):
    "إنشاء غلاف استجابة يشبه requests.Response بما يكفي للاختبار."
    return types.SimpleNamespace(
        status_code=status,
        json=lambda: payload,
    )

# ------------------------------------------------------------------ #
#                    اختبار fetch_prayer_times()                     #
# ------------------------------------------------------------------ #
def test_fetch_prayer_times_success(mocker):
    expected = {
        "Fajr": "05:00",
        "Sunrise": "06:30",
        "Dhuhr": "13:15",
        "Asr": "17:00",
        "Maghrib": "20:45",
        "Isha": "22:30",
    }
    payload = {"data": {"timings": expected}}

    mocker.patch("requests.get", return_value=_fake_response(payload))
    timings = adhan_player.fetch_prayer_times("Deggendorf", "Germany")

    # المفاتيح الستة متاحة
    assert set(timings.keys()) == set(expected.keys())
    # والقيم كلها datetime
    assert all(hasattr(t, "hour") for t in timings.values())


def test_fetch_prayer_times_api_failure(mocker):
    mocker.patch("requests.get", return_value=_fake_response({}, 500))
    with pytest.raises(RuntimeError):
        adhan_player.fetch_prayer_times("BadCity", "Nowhere")


# ------------------------------------------------------------------ #
#               اختبار جدولة المهام schedule_prayer_jobs            #
# ------------------------------------------------------------------ #
def test_schedule_prayer_jobs():
    scheduler = adhan_player._make_scheduler()

    # أوقات تجريبية: فجْر بعد دقيقة، والباقي آخر اليوم
    now = datetime.now(timezone.utc)
    hhmm_next_min = (now + timedelta(minutes=1)).strftime("%H:%M")

    test_times = {
        "Fajr": hhmm_next_min,
        "Dhuhr": "23:59",
        "Asr": "23:59",
        "Maghrib": "23:59",
        "Isha": "23:59",
    }

    adhan_player.schedule_prayer_jobs(
        scheduler,
        test_times,
        action=lambda *_: None,   # لا نحتاج صوتًا فعليًّا
    )

    jobs = scheduler.get_jobs()
    # نتوقّع 5 مهام (Sunrise غير موجود من الأصل)
    assert len(jobs) == 5
