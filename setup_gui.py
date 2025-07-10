import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
import requests
import threading

# Add the project root to the Python path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from src.prayer import config
from src.prayer.auth import google_auth

class SetupGUI(ttk.Frame):
    def __init__(self, master: tk.Tk):
        super().__init__(master, padding=20)
        master.title("Prayer Player Setup")
        master.resizable(False, False)

        self.countries = []
        self.cities = []
        self.create_widgets()
        self.load_initial_config()
        self.grid()
        self.load_countries()

    def create_widgets(self):
        # Country Selection
        ttk.Label(self, text="Country:").grid(column=0, row=0, sticky="w", pady=5)
        self.country_var = tk.StringVar()
        self.country_combo = ttk.Combobox(self, textvariable=self.country_var, width=38)
        self.country_combo.grid(column=1, row=0, sticky="ew", pady=5)
        self.country_combo.bind("<<ComboboxSelected>>", self.on_country_select)
        self.country_combo.bind("<KeyRelease>", lambda e: self._update_dropdown(e, 'country'))
        self.country_combo.bind('<Button-1>', lambda e: self.after(10, lambda: self._setup_combobox_search(self.country_combo)))

        # City Selection
        ttk.Label(self, text="City:").grid(column=0, row=1, sticky="w", pady=5)
        self.city_var = tk.StringVar()
        self.city_combo = ttk.Combobox(self, textvariable=self.city_var, state="disabled", width=38)
        self.city_combo.grid(column=1, row=1, sticky="ew", pady=5)
        self.city_combo.bind("<KeyRelease>", lambda e: self._update_dropdown(e, 'city'))
        self.city_combo.bind('<Button-1>', lambda e: self.after(10, lambda: self._setup_combobox_search(self.city_combo)))

        # Save Button
        self.save_button = ttk.Button(self, text="Save Configuration", command=self.save_configuration)
        self.save_button.grid(column=0, row=2, columnspan=2, pady=10)

        # Google Calendar Authentication
        ttk.Label(self, text="Google Calendar Setup:").grid(column=0, row=3, sticky="w", pady=5)
        self.auth_button = ttk.Button(self, text="Authenticate Google Calendar", command=self.authenticate_google_calendar)
        self.auth_button.grid(column=1, row=3, sticky="ew", pady=5)

        # Status Label
        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(self, textvariable=self.status_var, foreground="blue")
        self.status_label.grid(column=0, row=4, columnspan=2, pady=10)

        # Run Mode Selection
        ttk.Label(self, text="Run Mode:").grid(column=0, row=5, sticky="w", pady=5)
        self.run_mode_var = tk.StringVar(value="background")
        self.background_radio = ttk.Radiobutton(self, text="Run in background (recommended)", variable=self.run_mode_var, value="background")
        self.background_radio.grid(column=1, row=5, sticky="w", pady=2)
        self.foreground_radio = ttk.Radiobutton(self, text="Run in foreground (for testing)", variable=self.run_mode_var, value="foreground")
        self.foreground_radio.grid(column=1, row=6, sticky="w", pady=2)

        # Finish Button
        self.finish_button = ttk.Button(self, text="Finish Setup", command=self.finish_setup)
        self.finish_button.grid(column=0, row=8, columnspan=2, pady=10)

    def _fetch_data(self, url, params=None):
        try:
            response = requests.post(url, json=params) if params else requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            self.update_status(f"API Error: {e}", "red")
            messagebox.showerror("API Error", f"Failed to fetch data: {e}")
            return None

    def load_countries(self):
        self.update_status("Loading countries...", "blue")
        threading.Thread(target=self._load_countries_thread, daemon=True).start()

    def _load_countries_thread(self):
        data = self._fetch_data("https://countriesnow.space/api/v0.1/countries")
        if data and not data.get("error"):
            self.countries = sorted([country["country"] for country in data["data"]])
            self.country_combo["values"] = self.countries
            self.update_status("Countries loaded. Please select a country.", "green")
            self.country_combo.config(state="normal")
            # If a country was loaded from config, trigger city loading
            if self.country_var.get() in self.countries:
                self.on_country_select(None)
        else:
            self.update_status("Failed to load countries.", "red")

    def on_country_select(self, event):
        selected_country = self.country_var.get()
        self.city_combo.set("")
        self.city_combo.config(state="disabled")
        self.update_status(f"Loading cities for {selected_country}...", "blue")
        threading.Thread(target=self._load_cities_thread, args=(selected_country,), daemon=True).start()

    def _load_cities_thread(self, country):
        data = self._fetch_data("https://countriesnow.space/api/v0.1/countries/cities", {"country": country})
        if data and not data.get("error"):
            self.cities = sorted(data["data"])
            self.city_combo["values"] = self.cities
            self.city_combo.config(state="normal")
            self.update_status(f"Cities for {country} loaded.", "green")
            # Set city from config if available
            current_config = config.load_config()
            if current_config.get('country') == country and current_config.get('city') in self.cities:
                self.city_var.set(current_config.get('city'))
        else:
            self.update_status(f"Failed to load cities for {country}.", "red")

    def load_initial_config(self):
        current_config = config.load_config()
        self.city_var.set(current_config.get('city', ''))
        self.country_var.set(current_config.get('country', ''))
        self.run_mode_var.set(current_config.get('run_mode', 'background'))
        self.update_status("Configuration loaded.")

    def save_configuration(self):
        city = self.city_var.get().strip()
        country = self.country_var.get().strip()
        run_mode = self.run_mode_var.get()

        if not city or not country:
            messagebox.showwarning("Input Error", "Country and City must be selected.")
            return

        try:
            config.save_config(city, country, run_mode)
            self.update_status("Configuration saved successfully!", "green")
        except Exception as e:
            self.update_status(f"Error saving config: {e}", "red")
            messagebox.showerror("Save Error", f"Failed to save configuration: {e}")

    def authenticate_google_calendar(self):
        self.update_status("Attempting Google Calendar authentication...", "blue")
        try:
            google_auth.get_google_credentials(reauthenticate=True)
            self.update_status("Google Calendar authentication successful!", "green")
        except Exception as e:
            self.update_status(f"Google Calendar authentication failed: {e}", "red")
            messagebox.showerror("Authentication Error", f"Failed to authenticate Google Calendar: {e}")

    def finish_setup(self):
        self.save_configuration()
        if "successfully" in self.status_var.get():
            messagebox.showinfo("Setup Complete", "Configuration saved. You can now close this window.")
            self.master.destroy()
        else:
            messagebox.showwarning("Setup Incomplete", "Please save the configuration before finishing.")

    def _update_dropdown(self, event, combo_type):
        combo = event.widget
        var = combo.cget("textvariable")
        text = self.getvar(var)

        if combo_type == 'country':
            source_list = self.countries
        else:  # city
            source_list = self.cities

        if not text:
            filtered_list = source_list
        else:
            filtered_list = [item for item in source_list if text.lower() in item.lower()]

        # Preserve the entered text and cursor position
        current_text = text
        combo['values'] = filtered_list
        combo.set(current_text)
        combo.icursor(tk.END)

    def _setup_combobox_search(self, combo):
        """
        Binds keypress events on the combobox's dropdown list to redirect them
        to the main entry field. This is a workaround for a known issue in
        Tkinter on Linux where the dropdown list steals focus.
        """
        # This uses internal Tkinter details and might be fragile.
        try:
            popdown_window_name = self.tk.eval(f'ttk::combobox::PopdownWindow {combo}')
            if popdown_window_name:
                listbox = f'{popdown_window_name}.f.l'
                handler = lambda e, c=combo: self._on_listbox_keypress(e, c)
                self.tk.call('bind', listbox, '<KeyPress>', handler)
        except tk.TclError:
            # This can happen if the popdown window isn't visible yet.
            # The <Button-1> binding will retry.
            pass

    def _on_listbox_keypress(self, event, combo):
        """
        Handles a keypress on the dropdown list by redirecting it to the
        combobox entry widget.
        """
        if event.char:
            combo.focus()
            combo.event_generate(f'<KeyPress-{event.keysym}>')
            return 'break' # Stop the listbox from processing the event

    def update_status(self, message: str, color: str = "blue"):
        self.status_var.set(message)
        self.status_label.config(foreground=color)

def main():
    root = tk.Tk()
    SetupGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()