import tkinter as tk
from PIL import Image, ImageTk, ImageDraw

class AppTheme:
    # Grayscale-inspired palette
    BG_MAIN = "#F0F0F0"       # Main background
    BG_HEADER = "#A9A9A9"     # Header background
    SLIDER_TROUGH = "#C0C0C0" # Slider trough color
    SLIDER_HANDLE = "#999999" # Custom color for the handle (drawn in code if needed)

    # Fonts
    FONT_TITLE = ("Arial", 20, "bold")
    FONT_BODY = ("Arial", 14)
    FONT_TOOLTIP = ("Arial", 10)

class MidiArpeggiatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MIDI Arpeggiator")
        self.root.geometry("800x600")
        self.root.configure(bg=AppTheme.BG_MAIN)

        # === Header Bar ===
        header_frame = tk.Frame(root, bg=AppTheme.BG_HEADER, height=60)
        header_frame.pack(fill="x")

        title_label = tk.Label(header_frame, text="MIDI Arpeggiator",
                               font=AppTheme.FONT_TITLE,
                               fg="black", bg=AppTheme.BG_HEADER)
        title_label.pack(pady=10)

        # === Reset Button (Top Right) ===
        self.reset_icon = self.create_reset_icon()
        reset_button = tk.Button(root, image=self.reset_icon,
                                 command=self.reset_values, bd=0,
                                 bg=AppTheme.BG_MAIN,
                                 activebackground=AppTheme.BG_MAIN)
        reset_button.place(x=750, y=10)

        # === Frame for Sliders ===
        slider_frame = tk.Frame(root, bg=AppTheme.BG_MAIN)
        slider_frame.pack(pady=30)

        # Rate (BPM) Slider
        rate_label = tk.Label(slider_frame, text="Rate (BPM)",
                              font=AppTheme.FONT_BODY,
                              bg=AppTheme.BG_MAIN)
        rate_label.grid(row=0, column=0, padx=20, pady=10, sticky="w")

        self.rate_slider = tk.Scale(
            slider_frame,
            from_=20, to=300,  # BPM range
            resolution=0.1,
            orient="horizontal",
            length=400,
            troughcolor=AppTheme.SLIDER_TROUGH,
            bd=2,
            sliderrelief=tk.RAISED,
            highlightthickness=0,
        )
        self.rate_slider.grid(row=0, column=1, padx=20, pady=10)

        # Note Length Slider
        length_label = tk.Label(slider_frame, text="Note Length",
                                font=AppTheme.FONT_BODY,
                                bg=AppTheme.BG_MAIN)
        length_label.grid(row=1, column=0, padx=20, pady=10, sticky="w")

        self.length_slider = tk.Scale(
            slider_frame,
            from_=0.1, to=1.0,  # Note length range
            resolution=0.1,
            orient="horizontal",
            length=400,
            troughcolor=AppTheme.SLIDER_TROUGH,
            bd=2,
            sliderrelief=tk.RAISED,
            highlightthickness=0,
        )
        self.length_slider.grid(row=1, column=1, padx=20, pady=10)

        # Tooltip
        reset_button.bind("<Enter>", self.show_tooltip)
        reset_button.bind("<Leave>", self.hide_tooltip)
        self.tooltip_label = tk.Label(root,
                                      text="Reset",
                                      font=AppTheme.FONT_TOOLTIP,
                                      bg="white", fg="black",
                                      relief="solid", bd=1)
        self.tooltip_label.place_forget()

    def create_reset_icon(self):
        """Create a looping arrow reset icon in grayscale."""
        size = (30, 30)
        img = Image.new("RGBA", size, (0, 0, 0, 0))  # Transparent
        draw = ImageDraw.Draw(img)
        # Draw a looping arrow (approximation)
        # Using a dark gray fill to match the new theme
        draw.arc((5, 5, 25, 25), start=0, end=270, fill="#333333", width=3)
        draw.polygon([(23, 9), (27, 14), (21, 14)], fill="#333333")
        return ImageTk.PhotoImage(img)

    def reset_values(self):
        """Resets sliders to their default values."""
        self.rate_slider.set(1.0)
        self.length_slider.set(1.0)

    def show_tooltip(self, event):
        """Shows the reset tooltip near the button."""
        self.tooltip_label.place(x=730, y=40)

    def hide_tooltip(self, event):
        """Hides the reset tooltip."""
        self.tooltip_label.place_forget()


if __name__ == "__main__":
    root = tk.Tk()
    app = MidiArpeggiatorApp(root)
    root.mainloop()
