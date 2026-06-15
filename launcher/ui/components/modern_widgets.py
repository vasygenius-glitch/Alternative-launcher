import customtkinter as ctk

class GlassButton(ctk.CTkButton):
    """Aggressive monochrome button with sharp edges."""
    def __init__(self, master, **kwargs):
        # Strict industrial aesthetic
        defaults = {
            "corner_radius": 0,
            "border_width": 2,
            "border_color": "#FFFFFF",
            "fg_color": "#000000",
            "hover_color": "#1a1a1a",
            "text_color": "#FFFFFF",
            "font": ctk.CTkFont(family="Courier", weight="bold")
        }
        # Only Play Button or Critical Action can use red
        if kwargs.get("fg_color") == "#FF0000":
            defaults["border_color"] = "#FF0000"
            defaults["hover_color"] = "#cc0000"

        defaults.update(kwargs)
        super().__init__(master, **defaults)

class ModernCard(ctk.CTkFrame):
    """Monochrome flat container with sharp borders."""
    def __init__(self, master, title, icon_name="info", **kwargs):
        from launcher.utils.paths import get_resource_path
        from PIL import Image
        # Force sharp corners and stark contrast
        super().__init__(master, fg_color="#000000", corner_radius=0, border_width=2, border_color="#FFFFFF", **kwargs)

        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", padx=15, pady=(15, 5))

        try:
            icon_path = get_resource_path(f"launcher/assets/icons/{icon_name}.png")
            img = Image.open(icon_path)
            self.ctk_icon = ctk.CTkImage(light_image=img, dark_image=img, size=(24, 24))
            self.icon_lbl = ctk.CTkLabel(self.header, text="", image=self.ctk_icon)
        except Exception:
            self.icon_lbl = ctk.CTkLabel(self.header, text=">", font=ctk.CTkFont(family="Courier", size=18, weight="bold"), text_color="#FFFFFF")

        self.icon_lbl.pack(side="left", padx=(0, 10))

        self.title_lbl = ctk.CTkLabel(self.header, text=title.upper(), font=ctk.CTkFont(family="Courier", size=18, weight="bold"), text_color="#FFFFFF")
        self.title_lbl.pack(side="left")

        self.separator = ctk.CTkFrame(self, height=2, fg_color="#FFFFFF", corner_radius=0)
        self.separator.pack(fill="x", padx=15, pady=5)

        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.pack(fill="both", expand=True, padx=15, pady=(5, 15))

class ToastNotification(ctk.CTkFrame):
    """Terminal-style strict notification."""
    def __init__(self, master, message, type="info", duration=3000):
        color_map = {
            "info": "#FFFFFF",
            "success": "#FFFFFF", # In pure monochrome, success is also white
            "error": "#FF0000"    # Only errors are neon red
        }
        border_color = color_map.get(type, "#FFFFFF")
        text_color = color_map.get(type, "#FFFFFF")

        super().__init__(master, fg_color="#000000", border_width=2, border_color=border_color, corner_radius=0)

        self.lbl = ctk.CTkLabel(self, text=message.upper(), text_color=text_color, font=ctk.CTkFont(family="Courier", size=14, weight="bold"))
        self.lbl.pack(padx=20, pady=15)

        self.place(relx=0.5, rely=0.05, anchor="n")
        self.after(duration, self.fade_out)

    def fade_out(self):
        self.destroy()
