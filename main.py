"""Vision Bot - Android app (Kivy UI). Credentials are entered in the app, never stored in the repo."""
import json
import os

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

import bot_core

FIELDS = [
    ("gemini_key", "Gemini API key", False),
    ("gemini_model", "Gemini model", False),
    ("ig_user", "Bot Instagram username", False),
    ("ig_pass", "Bot Instagram password", True),
    ("creator_name", "Your name", False),
    ("creator_handle", "Your IG handle (@...)", False),
]
DEFAULTS = {"gemini_model": "gemini-2.0-flash", "creator_name": "Sahil", "creator_handle": "@sahilchakvesr"}


class VisionApp(App):
    def build(self):
        self.title = "Vision Bot"
        self.runner = None
        self.inputs = {}
        self.settings_path = os.path.join(self.user_data_dir, "settings.json")

        root = BoxLayout(orientation="vertical", padding=10, spacing=6)
        saved = self._load_settings()

        for key, hint, secret in FIELDS:
            ti = TextInput(
                text=saved.get(key, DEFAULTS.get(key, "")),
                hint_text=hint,
                multiline=False,
                password=secret,
                size_hint_y=None,
                height=44,
            )
            self.inputs[key] = ti
            root.add_widget(ti)

        self.status = Label(text="Stopped", size_hint_y=None, height=30)
        self.toggle = Button(text="START BOT", size_hint_y=None, height=50)
        self.toggle.bind(on_press=self.on_toggle)
        root.add_widget(self.status)
        root.add_widget(self.toggle)

        self.log_label = Label(text="", size_hint_y=None, halign="left", valign="top")
        self.log_label.bind(width=lambda s, w: setattr(s, "text_size", (w, None)))
        self.log_label.bind(texture_size=lambda s, t: setattr(s, "height", t[1]))
        scroll = ScrollView()
        scroll.add_widget(self.log_label)
        root.add_widget(scroll)
        return root

    def _load_settings(self):
        try:
            with open(self.settings_path) as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_settings(self):
        os.makedirs(self.user_data_dir, exist_ok=True)
        data = {k: v.text.strip() for k, v in self.inputs.items()}
        with open(self.settings_path, "w") as f:
            json.dump(data, f)
        return data

    def log(self, msg):
        Clock.schedule_once(lambda dt: self._append_log(msg))

    def _append_log(self, msg):
        lines = (self.log_label.text + "\n" + msg).strip().split("\n")
        self.log_label.text = "\n".join(lines[-80:])

    def on_toggle(self, *_):
        if self.runner and self.runner.is_running():
            self.runner.stop()
            self.toggle.text = "START BOT"
            self.status.text = "Stopping..."
            return

        settings = self._save_settings()
        missing = [k for k in ("gemini_key", "ig_user", "ig_pass") if not settings.get(k)]
        if missing:
            self.log(f"Missing: {', '.join(missing)}")
            return

        self.runner = bot_core.BotRunner(settings, self.log)
        self.runner.start()
        self.toggle.text = "STOP BOT"
        self.status.text = "Running"


if __name__ == "__main__":
    VisionApp().run()
