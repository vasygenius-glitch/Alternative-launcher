import customtkinter as ctk

class GlassButton(ctk.CTkButton):
    """A button that mimics a modern sleek look."""
    def __init__(self, master, **kwargs):
        # Allow overriding defaults cleanly
        defaults = {
            "corner_radius": 8,
            "border_width": 1,
            "border_color": "#3a3a3a",
            "fg_color": "#2b2b2b",
            "hover_color": "#3d3d3d",
            "font": ctk.CTkFont(weight="bold")
        }
        defaults.update(kwargs)
        super().__init__(master, **defaults)

class ModernCard(ctk.CTkFrame):
    """A highly stylized card for content."""
    def __init__(self, master, title, icon_name="info", **kwargs):
        from launcher.utils.paths import get_resource_path
        from PIL import Image
        super().__init__(master, fg_color=("#ffffff", "#1e1e1e"), corner_radius=15, border_width=1, border_color=("#d0d0d0", "#333333"), **kwargs)

        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", padx=15, pady=(15, 5))

        try:
            icon_path = get_resource_path(f"launcher/assets/icons/{icon_name}.png")
            img = Image.open(icon_path)
            self.ctk_icon = ctk.CTkImage(light_image=img, dark_image=img, size=(24, 24))
            self.icon_lbl = ctk.CTkLabel(self.header, text="", image=self.ctk_icon)
        except Exception:
            self.icon_lbl = ctk.CTkLabel(self.header, text="●", font=ctk.CTkFont(size=18), text_color="#28a745")

        self.icon_lbl.pack(side="left", padx=(0, 10))

        self.title_lbl = ctk.CTkLabel(self.header, text=title, font=ctk.CTkFont(size=18, weight="bold"))
        self.title_lbl.pack(side="left")

        self.separator = ctk.CTkFrame(self, height=2, fg_color=("#e0e0e0", "#2a2a2a"))
        self.separator.pack(fill="x", padx=15, pady=5)

        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.pack(fill="both", expand=True, padx=15, pady=(5, 15))

class ToastNotification(ctk.CTkFrame):
    """A modern toast notification widget."""
    def __init__(self, master, message, type="info", duration=3000):
        color_map = {
            "info": "#17a2b8",
            "success": "#28a745",
            "error": "#dc3545"
        }
        border_color = color_map.get(type, "#17a2b8")

        super().__init__(master, fg_color=("#e0e0e0", "#2b2b2b"), border_width=2, border_color=border_color, corner_radius=10)

        self.lbl = ctk.CTkLabel(self, text=message, font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl.pack(padx=20, pady=15)

        self.place(relx=0.5, rely=0.05, anchor="n")
        self.after(duration, self.fade_out)

    def fade_out(self):
        self.destroy()
