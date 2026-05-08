import customtkinter as ctk
import threading
from launcher.ui.components.modern_widgets import ModernCard

class NewsTab(ctk.CTkFrame):
    def __init__(self, master, app_logic):
        super().__init__(master, fg_color="transparent")
        self.app = app_logic

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.news_card = ModernCard(self, "Последние новости", icon="📰")
        self.news_card.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.scroll_frame = ctk.CTkScrollableFrame(self.news_card.content, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True)

        self.loading_lbl = ctk.CTkLabel(self.scroll_frame, text="Загрузка новостей...", font=ctk.CTkFont(size=14, slant="italic"))
        self.loading_lbl.pack(pady=20)

        self.news_loaded = False

    def on_show(self):
        if not self.news_loaded:
            self.fetch_news()

    def fetch_news(self):
        from launcher.core.news_fetcher import NewsFetcher
        # If we have an integrated fetcher in app, use it. Otherwise instance one.
        nf = NewsFetcher()
        nf.fetch_async(self._update_ui)

    def _update_ui(self, news_items):
        # Must run on main thread
        self.after(0, lambda: self._render_news(news_items))

    def _render_news(self, news_items):
        self.loading_lbl.destroy()

        if not news_items:
            ctk.CTkLabel(self.scroll_frame, text="Новости не найдены или нет подключения к интернету.").pack(pady=20)
            return

        for item in news_items:
            f = ctk.CTkFrame(self.scroll_frame, fg_color=("#f0f0f0", "#252525"), corner_radius=8)
            f.pack(fill="x", pady=5, padx=5)

            title = ctk.CTkLabel(f, text=item['title'], font=ctk.CTkFont(size=16, weight="bold"), wraplength=500, anchor="w", justify="left")
            title.pack(fill="x", padx=15, pady=(15, 5))

            pub = ctk.CTkLabel(f, text=item.get('published', ''), font=ctk.CTkFont(size=10), text_color="gray", anchor="w")
            pub.pack(fill="x", padx=15)

            summary = ctk.CTkLabel(f, text=item['summary'], font=ctk.CTkFont(size=13), wraplength=600, anchor="w", justify="left")
            summary.pack(fill="x", padx=15, pady=(10, 15))

            # Clickable link simulation
            if item.get('link'):
                btn = ctk.CTkButton(f, text="Читать далее", width=120, height=28, command=lambda l=item['link']: self._open_link(l))
                btn.pack(anchor="e", padx=15, pady=(0, 15))

        self.news_loaded = True

    def _open_link(self, url):
        import webbrowser
        try:
            webbrowser.open(url)
        except:
            pass
