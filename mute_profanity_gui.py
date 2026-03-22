#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess
import threading
import os
import sys
import time

class ProfanityMuterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Profanity Muter - GUI Edition")
        self.root.geometry("980x760")
        self.root.resizable(True, True)

        # Variables
        self.batch_var = tk.BooleanVar(value=False)
        self.validate_var = tk.BooleanVar(value=False)
        self.safe_var = tk.BooleanVar(value=False)
        self.dark_var = tk.BooleanVar(value=True)
        self.verbose_var = tk.BooleanVar(value=False)
        self.enhance_var = tk.BooleanVar(value=False)
        self.merge_var = tk.BooleanVar(value=True)
        self.beam_var = tk.IntVar(value=5)

        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.custom_words_var = tk.StringVar()
        self.model_var = tk.StringVar(value="large-v3")

        # Cancellation support
        self.cancel_flag = tk.BooleanVar(value=False)
        self.processing = False
        self.current_process = None

        # Style
        self.style = ttk.Style()
        self.apply_theme()

        # Main frame
        self.main_frame = ttk.Frame(root, style="TFrame")
        self.main_frame.pack(fill="both", expand=True)

        # Dark mode toggle
        ttk.Checkbutton(self.main_frame, text="Dark Mode", variable=self.dark_var,
                        command=self.toggle_dark_mode).grid(row=0, column=2, sticky="e", padx=10)

        # Mode
        ttk.Label(self.main_frame, text="Processing Mode:", font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky="w", pady=5)
        ttk.Checkbutton(self.main_frame, text="Batch mode (process entire folder)", variable=self.batch_var,
                        command=self.update_labels).grid(row=1, column=1, sticky="w", padx=10)

        # Input
        self.input_label = ttk.Label(self.main_frame, text="Input Video File:", font=("Segoe UI", 10))
        self.input_label.grid(row=2, column=0, sticky="w", pady=8)
        ttk.Entry(self.main_frame, textvariable=self.input_path, width=70).grid(row=2, column=1, pady=8, padx=5)
        ttk.Button(self.main_frame, text="Browse...", command=self.browse_input).grid(row=2, column=2, pady=8)

        # Output
        self.output_label = ttk.Label(self.main_frame, text="Output Video File:", font=("Segoe UI", 10))
        self.output_label.grid(row=3, column=0, sticky="w", pady=8)
        ttk.Entry(self.main_frame, textvariable=self.output_path, width=70).grid(row=3, column=1, pady=8, padx=5)
        ttk.Button(self.main_frame, text="Browse...", command=self.browse_output).grid(row=3, column=2, pady=8)

        # Options
        ttk.Label(self.main_frame, text="Options:", font=("Segoe UI", 10, "bold")).grid(row=4, column=0, sticky="w", pady=(15,5))
        ttk.Checkbutton(self.main_frame, text="Validate (compare Whisper vs subtitles)", variable=self.validate_var).grid(row=5, column=1, sticky="w", padx=10)
        ttk.Checkbutton(self.main_frame, text="Safe mode (mute missed subtitle profanities)", variable=self.safe_var).grid(row=6, column=1, sticky="w", padx=10)
        ttk.Checkbutton(self.main_frame, text="Dialogue Enhancement (helps Whisper catch more profanity)", 
                        variable=self.enhance_var).grid(row=7, column=1, sticky="w", padx=10)
        ttk.Checkbutton(self.main_frame, text="Merge with built-in profanity list", 
                        variable=self.merge_var).grid(row=8, column=1, sticky="w", padx=10)
        ttk.Checkbutton(self.main_frame, text="Verbose logging", variable=self.verbose_var).grid(row=9, column=1, sticky="w", padx=10)

        # Custom Words
        ttk.Label(self.main_frame, text="Custom Words File (optional):", font=("Segoe UI", 10)).grid(row=10, column=0, sticky="w", pady=8)
        ttk.Entry(self.main_frame, textvariable=self.custom_words_var, width=70).grid(row=10, column=1, pady=8, padx=5)
        ttk.Button(self.main_frame, text="Browse...", command=self.browse_custom).grid(row=10, column=2, pady=8)

        # Beam Size
        ttk.Label(self.main_frame, text="Beam Size (higher = more accurate, slower):", 
                  font=("Segoe UI", 10)).grid(row=11, column=0, sticky="w", pady=8)
        beam_frame = ttk.Frame(self.main_frame)
        beam_frame.grid(row=11, column=1, sticky="w", padx=5)
        for val in [1, 3, 5, 7, 10, 15]:
            ttk.Radiobutton(beam_frame, text=str(val), variable=self.beam_var, value=val).pack(side="left", padx=8)

        # Model selector
        ttk.Label(self.main_frame, text="Whisper Model:", font=("Segoe UI", 10)).grid(row=12, column=0, sticky="w", pady=8)
        models = ["tiny", "base", "small", "medium", "large-v2", "large-v3", "distil-large-v3", "large-v3-turbo"]
        self.model_combo = ttk.Combobox(self.main_frame, values=models, textvariable=self.model_var, state="readonly", width=25)
        self.model_combo.grid(row=12, column=1, sticky="w", padx=5, pady=8)

        # Action buttons
        btn_frame = ttk.Frame(self.main_frame, style="TFrame")
        btn_frame.grid(row=13, column=0, columnspan=3, pady=25, sticky="ew")
        btn_frame.columnconfigure(0, weight=1)

        button_container = ttk.Frame(btn_frame)
        button_container.grid(row=0, column=0)

        self.start_btn = ttk.Button(button_container, text="Start Processing", command=self.start_processing, style="Accent.TButton")
        self.start_btn.pack(side="left", padx=25)

        self.cancel_btn = ttk.Button(button_container, text="Cancel", command=self.cancel_processing, state="disabled")
        self.cancel_btn.pack(side="left", padx=25)

        ttk.Button(button_container, text="Clear Log", command=self.clear_log).pack(side="left", padx=25)

        # Live Log + Progress (rows shifted)
        ttk.Label(self.main_frame, text="Live Log Output:", font=("Segoe UI", 10, "bold")).grid(row=14, column=0, sticky="w")
        self.log_text = scrolledtext.ScrolledText(self.main_frame, height=18, state="normal", font=("Consolas", 9))
        self.log_text.grid(row=15, column=0, columnspan=3, sticky="nsew", pady=8)

        self.progress = ttk.Progressbar(self.main_frame, mode="indeterminate")
        self.progress.grid(row=16, column=0, columnspan=3, sticky="ew", pady=8)

        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(15, weight=1)

        self.update_labels()
        self.toggle_dark_mode()



    def apply_theme(self):
        self.style.theme_use('clam')
        self.style.configure("Accent.TButton", foreground="#FFFFFF", background="#007ACC")
        self.style.configure("TFrame", background="#1E1E1E")

    def toggle_dark_mode(self):
        if self.dark_var.get():
            bg = "#1E1E1E"; fg = "#FFFFFF"; entry_bg = "#2E2E2E"; log_bg = "#121212"; accent = "#007ACC"
        else:
            bg = "#F0F0F0"; fg = "#000000"; entry_bg = "#FFFFFF"; log_bg = "#FFFFFF"; accent = "#007ACC"

        self.root.configure(bg=bg)
        self.style.configure("TFrame", background=bg)
        self.style.configure("TLabel", background=bg, foreground=fg)
        self.style.configure("TCheckbutton", background=bg, foreground=fg)
        self.style.configure("TButton", background=accent)
        self.style.configure("Accent.TButton", background=accent, foreground="#FFFFFF")
        self.style.configure("TEntry", fieldbackground=entry_bg, foreground=fg)
        self.style.configure("TCombobox", fieldbackground=entry_bg, foreground=fg)
        self.style.configure("TProgressbar", background=accent, troughcolor=bg)
        self.log_text.configure(bg=log_bg, fg=fg, insertbackground=fg)

    def update_labels(self):
        if self.batch_var.get():
            self.input_label.config(text="Input Folder:")
            self.output_label.config(text="Output Folder:")
        else:
            self.input_label.config(text="Input Video File:")
            self.output_label.config(text="Output Video File:")

    def browse_input(self):
        if self.batch_var.get():
            path = filedialog.askdirectory(title="Select Input Folder")
        else:
            path = filedialog.askopenfilename(title="Select Video", filetypes=[("Video Files", "*.mkv *.mp4 *.avi *.mov *.m4v *.webm")])
        if path:
            self.input_path.set(path)

    def browse_output(self):
        if self.batch_var.get():
            path = filedialog.askdirectory(title="Select Output Folder")
        else:
            path = filedialog.asksaveasfilename(title="Save Output As", defaultextension=".mkv",
                                                filetypes=[("Video Files", "*.mkv *.mp4")])
        if path:
            self.output_path.set(path)

    def browse_custom(self):
        path = filedialog.askopenfilename(title="Select Custom Profanity List",
                                          filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if path:
            self.custom_words_var.set(path)

    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def clear_log(self):
        self.log_text.delete(1.0, tk.END)

    def start_processing(self):
        if self.processing: return


        self.cancel_flag.set(False)
        self.processing = True
        self.start_btn.config(state="disabled")
        self.cancel_btn.config(state="normal")
        self.log("Starting AI profanity muting...")
        self.progress.start()

        threading.Thread(target=self.run_cli, args=(self.input_path.get().strip(), self.output_path.get().strip()), daemon=True).start()

    def cancel_processing(self):
        if not self.processing: return
        self.cancel_flag.set(True)
        self.log("Cancellation requested...")
        if self.current_process and self.current_process.poll() is None:
            try:
                self.current_process.terminate()
                time.sleep(1.5)
                if self.current_process.poll() is None:
                    self.current_process.kill()
            except Exception as e:
                self.log(f"Error terminating process: {e}")

    def run_cli(self, input_p, output_p):
        script_path = os.path.join(os.path.dirname(__file__), "mute_profanity.py")
        if not os.path.exists(script_path):
            self.root.after(0, lambda: self.log("ERROR: mute_profanity.py not found!"))
            self.root.after(0, lambda: messagebox.showerror("Error", "mute_profanity.py is missing!"))
            self._finish_processing()
            return

        cmd = [sys.executable, script_path, input_p, output_p]
        if self.batch_var.get(): cmd.append("--batch")
        if self.validate_var.get(): cmd.append("--validate")
        if self.safe_var.get(): cmd.append("--safe")
        if self.enhance_var.get(): cmd.append("--enhance")
        if not self.verbose_var.get(): cmd.append("--quiet")
        if not self.merge_var.get(): cmd.append("--no-merge")

        cmd.extend(["--model", self.model_var.get()])
        cmd.extend(["--beam", str(self.beam_var.get())])

        if self.custom_words_var.get().strip():
            cmd.extend(["--custom-words", self.custom_words_var.get().strip()])

        self.root.after(0, lambda: self.log(f"Command: {' '.join(cmd)}"))

        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                       text=True, bufsize=1, universal_newlines=True)
            self.current_process = process

            for line in process.stdout:
                if self.cancel_flag.get():
                    self.root.after(0, lambda: self.log("Process cancelled by user."))
                    break
                if line.strip():
                    self.root.after(0, lambda l=line.strip(): self.log(l))

            process.wait()

            if self.cancel_flag.get():
                self.root.after(0, lambda: self.log("Processing stopped."))
            elif process.returncode in (0, 3221226505):
                self.root.after(0, lambda: self.log("All done! Videos are profanity-free and VLC-ready."))
                self.root.after(0, lambda: messagebox.showinfo("Success", "Processing completed successfully!"))
            else:
                self.root.after(0, lambda: self.log(f"Process exited with code {process.returncode}"))

        except Exception as e:
            self.root.after(0, lambda: self.log(f"Unexpected error: {e}"))

        finally:
            self._finish_processing()

    def _finish_processing(self):
        self.root.after(0, lambda: self.progress.stop())
        self.root.after(0, lambda: self.start_btn.config(state="normal"))
        self.root.after(0, lambda: self.cancel_btn.config(state="disabled"))
        self.processing = False
        self.current_process = None


if __name__ == "__main__":
    root = tk.Tk()
    app = ProfanityMuterApp(root)
    root.mainloop()
