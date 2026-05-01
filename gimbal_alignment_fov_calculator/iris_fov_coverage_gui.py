import math
import tkinter as tk
from pathlib import Path
from tkinter import font
from PIL import Image, ImageTk


def calculate(inputs):
    IPD = inputs["IPD"]
    eyeball_radius = inputs["eyeball_radius"]
    eye_to_camera_distance = inputs["eye_to_camera_distance"]
    eye_center_to_camera_center_offset = inputs["eye_center_to_camera_center_offset"]
    left_camera_to_right_camera_distance = inputs["left_camera_to_right_camera_distance"]
    camera_h_fov = inputs["camera_h_fov"]
    gimbal_angle = inputs["gimbal_angle"]

    left_camera_x = -left_camera_to_right_camera_distance / 2
    left_camera_y = 0
    right_camera_x = left_camera_to_right_camera_distance / 2
    right_camera_y = 0

    left_eye_x1 = -eyeball_radius - IPD / 2 + eye_center_to_camera_center_offset
    left_eye_y1 = eye_to_camera_distance
    left_eye_x2 = eyeball_radius - IPD / 2 + eye_center_to_camera_center_offset
    left_eye_y2 = eye_to_camera_distance

    right_eye_x1 = -eyeball_radius + IPD / 2 + eye_center_to_camera_center_offset
    right_eye_y1 = eye_to_camera_distance
    right_eye_x2 = eyeball_radius + IPD / 2 + eye_center_to_camera_center_offset
    right_eye_y2 = eye_to_camera_distance

    left_angle1 = math.atan2(left_eye_y1 - left_camera_y, left_eye_x1 - left_camera_x)
    left_angle2 = math.atan2(left_eye_y2 - left_camera_y, left_eye_x2 - left_camera_x)
    left_eye_coverage = -math.degrees(left_angle2 - left_angle1)
    left_eye_fov_margin = camera_h_fov - left_eye_coverage
    left_eye_fov_margin_with_gimbal = left_eye_fov_margin/2 + gimbal_angle

    right_angle1 = math.atan2(right_eye_y1 - right_camera_y, right_eye_x1 - right_camera_x)
    right_angle2 = math.atan2(right_eye_y2 - right_camera_y, right_eye_x2 - right_camera_x)
    right_eye_coverage = -math.degrees(right_angle2 - right_angle1)
    right_eye_fov_margin = camera_h_fov - right_eye_coverage
    right_eye_fov_margin_with_gimbal = right_eye_fov_margin/2 + gimbal_angle

    return {
        "left_coverage": left_eye_coverage,
        "left_margin": left_eye_fov_margin,
        "left_margin_gimbal": left_eye_fov_margin_with_gimbal,
        "right_coverage": right_eye_coverage,
        "right_margin": right_eye_fov_margin,
        "right_margin_gimbal": right_eye_fov_margin_with_gimbal,
    }


# ── colour palette ─────────────────────────────────────────────────────────────
BG     = "#1e1e2e"
PANEL  = "#2a2a3e"
ACCENT = "#7c6af7"
TEXT   = "#cdd6f4"
SUBTEXT= "#a6adc8"
GREEN  = "#a6e3a1"
YELLOW = "#f9e2af"
RED    = "#f38ba8"
ENTRY_BG = "#313244"
BORDER = "#45475a"

IMG_W  = 520   # display width for the diagram


class App(tk.Tk):
    # (key, label, unit, default, spec_note)
    FIELDS = [
        ("IPD",                               "IPD",                       "mm", 63,   "normal range: 54–74 mm"),
        ("eyeball_radius",                    "Eyeball Radius",            "mm", 12,   None),
        ("eye_to_camera_distance",            "Eye-to-Camera Distance",    "mm", 350,  "range: 350–550 mm"),
        ("eye_center_to_camera_center_offset","Eye–Camera Center Offset",  "mm", 0,    None),
        ("left_camera_to_right_camera_distance", "Camera Separation (L→R)","mm", 42,  "spec: 42 mm"),
        ("camera_h_fov",                      "Camera Horizontal FOV",     "°",  5.6, "spec: 5.6°"),
        ("gimbal_angle",                      "Gimbal Angle (one side)",   "°",  4,   "spec: 4°"),
    ]

    # (label, key, note)
    OUTPUTS = [
        ("LEFT EYE",            None,                  None),
        ("Eye Coverage",        "left_coverage",       None),
        ("FOV Margin",          "left_margin",         "two sides"),
        ("FOV Margin + Gimbal", "left_margin_gimbal",  "one side"),
        ("RIGHT EYE",           None,                  None),
        ("Eye Coverage",        "right_coverage",      None),
        ("FOV Margin",          "right_margin",        "two sides"),
        ("FOV Margin + Gimbal", "right_margin_gimbal", "one side"),
    ]

    def __init__(self):
        super().__init__()
        self.title("Iris FOV Coverage Calculator")
        self.configure(bg=BG)
        self.resizable(False, False)

        title_font  = font.Font(family="Helvetica", size=15, weight="bold")
        label_font  = font.Font(family="Helvetica", size=11)
        small_font  = font.Font(family="Helvetica", size=9)
        spec_font   = font.Font(family="Helvetica", size=9, slant="italic")
        result_font = font.Font(family="Helvetica", size=12, weight="bold")
        unit_font   = font.Font(family="Helvetica", size=10)

        # ── title ─────────────────────────────────────────────────────────────
        tk.Label(self, text="Iris FOV Coverage Calculator",
                 bg=BG, fg=ACCENT, font=title_font, pady=12
                 ).grid(row=0, column=0, columnspan=2, sticky="ew")

        # ── LEFT: diagram ─────────────────────────────────────────────────────
        img_path = Path(__file__).parent / "iris_camera_fov_coverage.png"
        raw = Image.open(img_path)
        scale = IMG_W / raw.width
        img_h = int(raw.height * scale)
        raw = raw.resize((IMG_W, img_h), Image.LANCZOS)
        self._diagram = ImageTk.PhotoImage(raw)

        img_frame = tk.Frame(self, bg=PANEL,
                             highlightbackground=BORDER, highlightthickness=1)
        img_frame.grid(row=1, column=0, padx=(14, 6), pady=(0, 14), sticky="n")

        tk.Label(img_frame, text="SYSTEM DIAGRAM",
                 bg=PANEL, fg=ACCENT, font=small_font,
                 anchor="w", padx=8, pady=5).pack(fill="x")
        tk.Label(img_frame, image=self._diagram, bg=PANEL,
                 padx=6, pady=6).pack()

        # ── RIGHT: inputs + outputs stacked ───────────────────────────────────
        right = tk.Frame(self, bg=BG)
        right.grid(row=1, column=1, padx=(6, 14), pady=(0, 14), sticky="n")

        # inputs
        in_frame = tk.Frame(right, bg=PANEL,
                            highlightbackground=BORDER, highlightthickness=1,
                            padx=16, pady=12)
        in_frame.pack(fill="x", pady=(0, 8))

        tk.Label(in_frame, text="INPUT PARAMETERS",
                 bg=PANEL, fg=ACCENT, font=small_font
                 ).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 6))

        self.vars = {}
        for i, (key, label, unit, default, spec) in enumerate(self.FIELDS, start=1):
            tk.Label(in_frame, text=label, bg=PANEL, fg=TEXT,
                     font=label_font, anchor="w", width=24
                     ).grid(row=i, column=0, sticky="w", pady=3)

            var = tk.StringVar(value=str(default))
            self.vars[key] = var

            tk.Entry(in_frame, textvariable=var, width=8,
                     bg=ENTRY_BG, fg=TEXT, insertbackground=TEXT,
                     relief="flat", font=label_font,
                     highlightbackground=BORDER, highlightthickness=1
                     ).grid(row=i, column=1, padx=(6, 4), pady=3)

            tk.Label(in_frame, text=unit, bg=PANEL, fg=SUBTEXT,
                     font=unit_font).grid(row=i, column=2, sticky="w")

            if spec:
                tk.Label(in_frame, text=spec, bg=PANEL, fg="#6c7086",
                         font=spec_font).grid(row=i, column=3, sticky="w", padx=(8, 0))

        btn = tk.Button(in_frame, text="Calculate", command=self._run,
                        bg=ACCENT, fg="#0f0e17",
                        activebackground="#6255d4", activeforeground="#0f0e17",
                        font=font.Font(family="Helvetica", size=11, weight="bold"),
                        relief="flat", cursor="hand2", padx=12, pady=5)
        btn.grid(row=len(self.FIELDS) + 1, column=0, columnspan=4,
                 pady=(12, 2), sticky="ew")
        self.bind("<Return>", lambda _: self._run())

        # outputs
        out_frame = tk.Frame(right, bg=PANEL,
                             highlightbackground=BORDER, highlightthickness=1,
                             padx=16, pady=12)
        out_frame.pack(fill="x")

        tk.Label(out_frame, text="OUTPUT RESULTS",
                 bg=PANEL, fg=ACCENT, font=small_font
                 ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 6))

        self.result_vars = {}
        for row, (label, key, note) in enumerate(self.OUTPUTS, start=1):
            if key is None:
                tk.Label(out_frame, text=label, bg=PANEL, fg=YELLOW,
                         font=font.Font(family="Helvetica", size=10, weight="bold"),
                         anchor="w").grid(row=row, column=0, columnspan=4,
                                          sticky="w", pady=(8, 1))
            else:
                tk.Label(out_frame, text=label, bg=PANEL, fg=TEXT,
                         font=label_font, anchor="w", width=22
                         ).grid(row=row, column=0, sticky="w", pady=2)

                var = tk.StringVar(value="—")
                self.result_vars[key] = var
                lbl = tk.Label(out_frame, textvariable=var, bg=PANEL, fg=GREEN,
                               font=result_font, anchor="e", width=9)
                lbl.grid(row=row, column=1, sticky="e", pady=2)
                self.result_vars[key + "_widget"] = lbl

                tk.Label(out_frame, text="°", bg=PANEL, fg=SUBTEXT,
                         font=unit_font).grid(row=row, column=2, sticky="w")

                if note:
                    tk.Label(out_frame, text=note, bg=PANEL, fg="#6c7086",
                             font=spec_font).grid(row=row, column=3, sticky="w", padx=(8, 0))

        # status bar
        self.status = tk.StringVar(value="Enter parameters and press Calculate.")
        tk.Label(self, textvariable=self.status, bg=BG, fg=SUBTEXT,
                 font=small_font, pady=5
                 ).grid(row=2, column=0, columnspan=2, sticky="ew")

        self._run()

    def _run(self):
        try:
            inputs = {key: float(self.vars[key].get()) for key, *_ in self.FIELDS}
        except ValueError:
            self.status.set("Error: all inputs must be valid numbers.")
            return

        results = calculate(inputs)

        for key, val in results.items():
            self.result_vars[key].set(f"{val:+.3f}")
            widget = self.result_vars.get(key + "_widget")
            if widget and "margin" in key:
                widget.configure(fg=RED if val < 0 else (YELLOW if val < 1 else GREEN))

        self.status.set("Calculated successfully.")


if __name__ == "__main__":
    App().mainloop()
