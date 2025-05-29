Absolutely! Here is your documentation in **Markdown** format, suitable for a README or wiki page.

---

````markdown
# How to Run the Adhan Script as a Background Service on Ubuntu 22.04

This guide shows you how to convert your Python adhan scheduler into a background service that runs automatically at login using a systemd **user service**. This is ideal for desktop applications that interact with your calendar, audio, or GUI.

---

## 1. Prepare Your Environment

- Place your Python scripts in a folder, e.g. `prayer`
- Create a virtual environment and install dependencies:

```bash
python3 -m venv myenv
source myenv/bin/activate
pip install --upgrade pip
pip install requests intervaltree apscheduler
````

---

## 2. Test the Script Manually

Before creating the service, make sure your script works from the terminal:

```bash
myenv/bin/python3 /src/adhan_player.py --city Deggendorf --country Germany --audio adhan.mp3 --log-level INFO
```

---

## 3. Create a systemd User Service File

1. Create the user systemd directory if needed:

   ```bash
   mkdir -p ~/.config/systemd/user/
   ```

2. Create and edit the service file:

   ```bash
   nano ~/.config/systemd/user/adhan-player.service
   ```

3. Paste and adjust this content:

   ```ini
   [Unit]
   Description=Adhan Player Prayer Scheduler

   [Service]
   Type=simple
   ExecStart=myenv/bin/python3 /src/adhan_player.py --city Deggendorf --country Germany --audio adhan.mp3 --log-level INFO
   Restart=always

   [Install]
   WantedBy=default.target
   ```

---

## 4. Enable and Start the Service

Reload and enable your user service:

```bash
systemctl --user daemon-reload
systemctl --user enable --now adhan-player.service
```

If you want the service to run even when not logged in to the GUI:

```bash
loginctl enable-linger $USER
```

---

## 5. Check Service Status and Logs

Check if it’s running and view logs:

```bash
systemctl --user status adhan-player.service
journalctl --user -u adhan-player.service -f
```

---

## 6. Apply Code Changes

After editing your code, **restart the service** to apply updates:

```bash
systemctl --user restart adhan-player.service
```

If you change the `.service` file:

```bash
systemctl --user daemon-reload
systemctl --user restart adhan-player.service
```

---

## 7. Stop or Disable the Service

To stop:

```bash
systemctl --user stop adhan-player.service
```

To disable from autostart:

```bash
systemctl --user disable adhan-player.service
```

---

## 8. Common Troubleshooting Commands

* View last 50 log lines:

  ```bash
  journalctl --user -u adhan-player.service -n 50 --no-pager
  ```
* List all running user services:

  ```bash
  systemctl --user list-units --type=service
  ```

---

## 9. Environment Notes

No need to set `DISPLAY` or `DBUS_SESSION_BUS_ADDRESS` manually; user services inherit your desktop session automatically.

---

## **Summary of Commands Used**

```bash
# Create virtualenv and install dependencies
python3 -m venv myenv
source myenv/bin/activate
pip install --upgrade pip
pip install requests intervaltree apscheduler

# Create user service file
mkdir -p ~/.config/systemd/user/
nano ~/.config/systemd/user/adhan-player.service

# Reload, enable and start service
systemctl --user daemon-reload
systemctl --user enable --now adhan-player.service

# (Optional) Enable linger for running after logout
loginctl enable-linger $USER

# Check status and logs
systemctl --user status adhan-player.service
journalctl --user -u adhan-player.service -f

# Restart after code changes
systemctl --user restart adhan-player.service
```

---

**Congratulations!**
Your adhan scheduler now runs automatically, restarts after reboots and login, and picks up new changes with a simple restart.

---