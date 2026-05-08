import customtkinter as ctk
import threading
from launcher.ui.components.modern_widgets import ModernCard

class NewsTab(ctk.CTkFrame):
    def __init__(self, master, app_logic):
        super().__init__(master, fg_color="transparent")
        self.app = app_logic

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.news_card = ModernCard(self, "Последние новости", icon_name="news")
        self.news_card.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.scroll_frame = ctk.CTkScrollableFrame(self.news_card.content, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True)

        self.loading_lbl = ctk.CTkLabel(self.scroll_frame, text="[ ] ИНИЦИАЛИЗАЦИЯ СЕТИ...", font=ctk.CTkFont(family="Courier", size=14, weight="bold"), text_color="#FFFFFF")
        self.loading_lbl.pack(pady=20)

        self.news_loaded = False
        self.loading_frames = ["|", "/", "-", "\\"]
        self.frame_idx = 0
        self.is_animating = False

    def _animate_loading(self):
        if not self.is_animating or self.news_loaded:
            return
        self.frame_idx = (self.frame_idx + 1) % len(self.loading_frames)
        self.loading_lbl.configure(text=f"[{self.loading_frames[self.frame_idx]}] ПОЛУЧЕНИЕ ДАННЫХ ИЗ RSS...")
        self.after(100, self._animate_loading)

    def on_show(self):
        if not self.news_loaded and not self.is_animating:
            self.is_animating = True
            self._animate_loading()
            self.fetch_news()

    def fetch_news(self):
        # Fire and forget approach utilizing Watchdog
        import uuid
        task_id = f"news_fetch_{uuid.uuid4().hex[:8]}"

        # We hook into global watchdog
        # The fetcher handles its own internal threading, but we wrap it logically if we need to
        from launcher.core.news_fetcher import NewsFetcher
        nf = NewsFetcher()

        def safe_callback(news_items):
            self._update_ui(news_items)

        nf.fetch_async(safe_callback)

    def _update_ui(self, news_items):
        self.after(0, lambda: self._render_news(news_items))

    def _render_news(self, news_items):
        self.is_animating = False
        self.loading_lbl.destroy()

        if not news_items:
            ctk.CTkLabel(self.scroll_frame, text="НЕТ ДОСТУПА К СЕТИ / ОШИБКА RSS", font=ctk.CTkFont(family="Courier", weight="bold"), text_color="#FF0000").pack(pady=20)
            return

        from launcher.ui.components.modern_widgets import GlassButton

        for item in news_items:
            # Monochrome aesthetic wrapper
            f = ctk.CTkFrame(self.scroll_frame, fg_color="#000000", border_width=1, border_color="#333333", corner_radius=0)
            f.pack(fill="x", pady=5, padx=5)

            title = ctk.CTkLabel(f, text=item['title'].upper(), font=ctk.CTkFont(family="Courier", size=16, weight="bold"), text_color="#FFFFFF", wraplength=500, anchor="w", justify="left")
            title.pack(fill="x", padx=15, pady=(15, 5))

            pub = ctk.CTkLabel(f, text=item.get('published', '').upper(), font=ctk.CTkFont(family="Courier", size=10), text_color="gray", anchor="w")
            pub.pack(fill="x", padx=15)

            summary = ctk.CTkLabel(f, text=item['summary'], font=ctk.CTkFont(family="Courier", size=13), text_color="#d0d0d0", wraplength=600, anchor="w", justify="left")
            summary.pack(fill="x", padx=15, pady=(10, 15))

            if item.get('link'):
                btn = GlassButton(f, text="ЧИТАТЬ", width=120, height=28, command=lambda l=item['link']: self._open_link(l))
                btn.pack(anchor="e", padx=15, pady=(0, 15))

        self.news_loaded = True

    def _open_link(self, url):
        import webbrowser
        try:
            webbrowser.open(url)
        except:
            pass
