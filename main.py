import time
import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox
from event import EventType
from event_recorder import EventRecorder, Event
from pynput import keyboard
import json
import threading
import ctypes

from event_replayer import EventReplayer

ctypes.windll.shcore.SetProcessDpiAwareness(2)

class MacroRecorderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Macro Daddy")
        self.recorder = None
        self.recorder_running = threading.Event()
        self.events = []
        self.replay_thread = None
        self.replay_running = threading.Event()

        # Create a label for keybinds
        self.keybinds_label = tk.Label(root, text="Keybinds:\n F7 - Start Recording\nF8 - Stop Recording\nF5 - Start Replay\rF6 - Stop Replay")
        self.keybinds_label.pack(pady=10)

        # Create a menu
        self.menu = tk.Menu(root)
        root.config(menu=self.menu)
        file_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load Replay", command=self.load_replay)
        file_menu.add_command(label="Save Replay", command=self.save_replay)
        file_menu.add_separator()
        file_menu.add_command(label="Start Replay", command=self.start_replay)
        file_menu.add_command(label="Stop Replay", command=self.stop_replay)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=root.quit)

        # Create a scrolled text widget for the log
        self.log = scrolledtext.ScrolledText(root, width=80, height=20, state=tk.DISABLED)
        self.log.pack(padx=10, pady=10)

        # Create tags for colored text
        self.log.tag_configure("info", foreground="blue")
        self.log.tag_configure("warning", foreground="orange")
        self.log.tag_configure("error", foreground="red")

        # Create a checkbox for repeat mode
        self.repeat_var = tk.BooleanVar()
        self.repeat_checkbox = tk.Checkbutton(root, text="Repeat", variable=self.repeat_var)
        self.repeat_checkbox.pack()

        # Start listening for global key events
        self.global_listener = keyboard.GlobalHotKeys({
            '<f7>': self.start_recording,
            '<f8>': self.stop_recording,
            '<f5>': self.start_replay,
            '<f6>': self.stop_replay
        })
        self.global_listener.start()

    def start_recording(self):
        if self.recorder_running.is_set():
            self._insert_log("recorder already running", "warning")
            return

        self.recorder_running.set()
        self.recorder = EventRecorder(ignore_keys=[keyboard.Key.f8, keyboard.Key.f7, keyboard.Key.f5, keyboard.Key.f6]) 
        self.recorder.start()
        self._insert_log("recording started", "info")

    def stop_recording(self):
        if not self.recorder_running.is_set():
            self._insert_log("recorder not running", "warning")
            return

        self.events = self.recorder.stop()
        self.recorder_running.clear()
        self.recorder = None
        self._insert_log("recording stopped", "info")
        self.log.see(tk.END)  # Scroll to the end

    def load_replay(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            try:
                with open(file_path, 'r') as file:
                    events = json.load(file)
                    self.events = [Event.from_dict(event) for event in events]
                    self._insert_log(f"loaded replay {file_path}", "info")
                    self.log.see(tk.END)
            except Exception as e:
                self._insert_log(f"failed to load replay: {e}", "error")

    def save_replay(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            try:
                with open(file_path, 'w') as file:
                    json.dump([event.to_dict() for event in self.events], file, indent=4)
                    self._insert_log(f"saved replay {file_path}", "info")
            except Exception as e:
                self._insert_log(f"failed to save replay: {e}", "error")

    def start_replay(self):
        self._insert_log("starting replay ", "info")
        self.replay_running.set()
        self.replay_thread = threading.Thread(target=self._replay_loop)
        self.replay_thread.start()

    def _replay_loop(self):
        while self.replay_running.is_set():
            self.replay = EventReplayer(self.events)
            self.replay.replay()
            if not self.repeat_var.get():
                break
        self._insert_log("replay finished", "info")

    def stop_replay(self):
        self.replay_running.clear()
        self.replay.stop()
        if self.replay_thread:
            self.replay_thread.join()
        self._insert_log("replay stopped", "info")

    def _insert_log(self, text, tag=None):
        self.log.config(state=tk.NORMAL)
        when = time.strftime("%Y-%m-%d %H:%M:%S")
        self.log.insert(tk.END, f"when={when} message=\"{text}\"\n", tag)
        self.log.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = MacroRecorderApp(root)
    root.mainloop()