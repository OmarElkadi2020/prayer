import win32serviceutil
import win32service
import win32event
import servicemanager
import sys
import os
import time
import logging

# Add the parent directory to the Python path to allow importing prayer
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from prayer.__main__ import main as prayer_main
from prayer.config import LOG

class PrayerPlayerService(win32serviceutil.ServiceFramework):
    _svc_name_ = "PrayerPlayer"
    _svc_display_name_ = "Prayer Player Scheduler"
    _svc_description_ = "Schedules and plays Adhan, integrates with calendar."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.is_running = True

    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        LOG.info("PrayerPlayer service started.")

        # Redirect stdout/stderr to a log file for debugging
        # This is a basic redirection; for robust logging, use Python's logging module
        # with a FileHandler configured.
        # sys.stdout = open("C:\prayer_player_service_stdout.log", "a")
        # sys.stderr = open("C:\prayer_player_service_stderr.log", "a")

        # Run the main application logic in a separate thread or process if it's blocking
        # For now, assuming prayer_main can be called directly or will manage its own loop
        try:
            # You might need to pass specific arguments to prayer_main
            # For a service, you typically don't want it to exit, so prayer_main
            # should ideally run in a loop or be adapted for service context.
            # If prayer_main is blocking, consider running it in a separate thread.
            # For simplicity, we'll assume it sets up APScheduler and runs in a loop.
            # If prayer_main exits, the service will stop.
            prayer_main([]) # Pass an empty list for argv, as args are handled by service config
            while self.is_running:
                win32event.WaitForSingleObject(self.hWaitStop, 5000) # Check stop event every 5 seconds
        except Exception as e:
            LOG.error(f"Error in PrayerPlayer service: {e}")
            servicemanager.LogErrorMsg(str(e))
        finally:
            LOG.info("PrayerPlayer service stopped.")
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STOPPED,
                (self._svc_name_, '')
            )

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.is_running = False
        LOG.info("PrayerPlayer service stop requested.")

if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(PrayerPlayerService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(PrayerPlayerService)
