import unittest
import time
import os
from datetime import datetime

from src.prayer_times import today_times, _fetch_raw

# Skip this test by default when network access is not enabled
RUN_NET_TESTS = os.environ.get("RUN_NET_TESTS") == "1"

class TestPrayerTimesIntegration(unittest.TestCase):

    def setUp(self):
        # Clear caches before each test to ensure isolation
        _fetch_raw.cache_clear()
        from src import prayer_times
        prayer_times._disk_cache.clear()

    @unittest.skipUnless(RUN_NET_TESTS, "Network access required for this test")
    def test_today_times_with_real_api_call(self):
        """
        Tests the today_times function with a real API call to ensure it
        handles a live response correctly.
        """
        # Using a real, well-known location
        city = "Mecca"
        country = "Saudi Arabia"

        # 1. First call - should hit the API
        start_time = time.time()
        times = today_times(city, country)
        duration1 = time.time() - start_time
        print(f"First call (real API) took: {duration1:.4f}s")


        # --- Assertions for the first call ---
        self.assertIsInstance(times, dict)
        # There should be 5 prayers
        self.assertEqual(len(times), 5)

        expected_prayers = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]
        for prayer in expected_prayers:
            self.assertIn(prayer, times)
            self.assertIsInstance(times[prayer], datetime)
            self.assertIsNotNone(times[prayer].tzinfo)

        # 2. Second call - should be cached and much faster
        start_time = time.time()
        cached_times = today_times(city, country)
        duration2 = time.time() - start_time
        print(f"Second call (cached) took: {duration2:.4f}s")

        # --- Assertions for the second call ---
        self.assertEqual(times, cached_times)
        # The cached call should be significantly faster than the API call
        self.assertLess(duration2, duration1)
        # It should be very fast, e.g., under 0.01s
        self.assertLess(duration2, 0.01)

if __name__ == '__main__':
    unittest.main()
