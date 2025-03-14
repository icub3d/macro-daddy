import argparse
import json
import time
import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox
import threading

from pynput import keyboard

from controller import DefaultController
from replay import Replay
from replayer import Replayer
from recorder import Recorder

# Windows scaling fix
import ctypes
ctypes.windll.shcore.SetProcessDpiAwareness(2)

# def record():
#     recorder = Recorder()

#     recorder_thread = threading.Thread(target=recorder.start)
    

#     def on_stop():
#         recorder.stop()
#         events = recorder.events
#         print(json.dumps([event.to_dict() for event in events], indent=4))

#     # Wait for F8 to stop recording
#     stop_event = threading.Event()
#     def wait_for_stop():
#         while not stop_event.is_set():
#             time.sleep(0.1)
#     threading.Thread(target=wait_for_stop).start()

#     # Listen for F8 to stop recording
#     from pynput import keyboard
#     def on_press(key):
#         if key == keyboard.Key.f8:
#             stop_event.set()
#             on_stop()
#         elif key == keyboard.Key.f7:
#             recorder.start()


#     with keyboard.Listener(on_press=on_press) as listener:
#         listener.join()

# def replay(replay_file, repeat):
#     print("Press F5 to start replay and F6 to stop replay.")
#     with open(replay_file, 'r') as file:
#         events = json.load(file)
#         events = [DefaultController.Event.from_dict(event) for event in events]

#     replayer = Replayer(controller=DefaultController(), repeat=repeat, events=events)

#     def on_start():
#         replayer.start()

#     def on_stop():
#         replayer.stop()

#     # Wait for F6 to stop replay
#     stop_event = threading.Event()
#     def wait_for_stop():
#         while not stop_event.is_set():
#             time.sleep(0.1)
#     threading.Thread(target=wait_for_stop).start()

#     # Listen for F5 to start replay and F6 to stop replay
#     from pynput import keyboard
#     def on_press(key):
#         if key == keyboard.Key.f5:
#             on_start()
#         elif key == keyboard.Key.f6:
#             stop_event.set()
#             on_stop()
#             return False

#     with keyboard.Listener(on_press=on_press) as listener:
#         listener.join()

# def main():
#     parser = argparse.ArgumentParser(description="macro daddy - record and replay macros")
#     subparsers = parser.add_subparsers(dest="command")

#     # Record command
#     record_parser = subparsers.add_parser("record", help="record events (F7 to start, F8 to stop)")

#     # Replay command
#     replay_parser = subparsers.add_parser("replay", help="replay events (F5 to start, F6 to stop)")
#     replay_parser.add_argument("replay_file", type=str, help="path to the replay file")
#     replay_parser.add_argument("--repeat", action="store_true", help="repeat the replay, until stopped")

#     args = parser.parse_args()

#     if args.command == "record":
#         record()
#     elif args.command == "replay":
#         replay(args.replay_file, args.repeat)
#     else:
#         parser.print_help()

# if __name__ == "__main__":
#     main()

class MacroDaddyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Macro Daddy")
        self.replay = None
        self.recorder = None
        self.recorder_running = threading.Event()
        self.replayer = None
        self.replayer_running = threading.Event()

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
            return
        self.recorder_running.set()
        self.recorder = Recorder()
        self.recorder.start()
        self._insert_log("recording started", "info")
        self.log.see(tk.END)  # Scroll to the end

    def stop_recording(self):
        if not self.recorder_running.is_set():
            return
        self.recorder_running.clear()
        self.replay = Replay(events=self.recorder.stop())
        self._insert_log("recording stopped", "info")
        self.log.see(tk.END)  # Scroll to the end

    def load_replay(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            try:
                self.replay = Replay.load(file_path)
                self._insert_log(f"loaded replay {file_path}", "info")
                self.log.see(tk.END)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load replay: {e}")

    def save_replay(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            try:
                if self.replay:
                    self.replay.save(file_path)
                    self._insert_log(f"saved replay {file_path}", "info")
                    self.log.see(tk.END)
                else:
                    self._insert_log("no replay to save", "warning")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save replay: {e}")

    def start_replay(self):
        if self.replayer_running.is_set():
            return
        self.replayer_running.set()
        self.replayer = Replayer(events=self.replay.events, repeat=self.repeat_var.get())
        self.replayer.start()
        self._insert_log("starting replay", "info")

    def stop_replay(self):
        if not self.replayer_running.is_set():
            return
        self.replayer_running.clear()
        self.replayer.stop()
        self._insert_log("stopping replay", "info")

    def _insert_log(self, text, tag=None):
        self.log.config(state=tk.NORMAL)
        when = time.strftime("%Y-%m-%d %H:%M:%S")
        self.log.insert(tk.END, f"when={when} message=\"{text}\"\n", tag)
        self.log.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = MacroDaddyApp(root)
    root.mainloop()