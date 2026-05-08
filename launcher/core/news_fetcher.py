import feedparser
import threading
import json
import os
import time
from launcher.utils.logger import get_logger

log = get_logger("NewsFetcher")

class NewsFetcher:
    # Since official minecraft RSS is frequently changing or 404ing, we use the launcher's own RSS/JSON endpoint
    # Or a generic reliable one for testing if not available.
    NEWS_URL = "https://www.minecraft.net/en-us/article.rss" # Fallback typical RSS
    CACHE_FILE = "launcher_data/news_cache.json"

    def __init__(self):
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(self.CACHE_FILE), exist_ok=True)

    def fetch_async(self, callback):
        """Asynchronously fetches news and triggers the callback with the results."""
        threading.Thread(target=self._fetch, args=(callback,), daemon=True).start()

    def _load_local_cache(self):
        try:
            if os.path.exists(self.CACHE_FILE):
                with open(self.CACHE_FILE, "r", encoding="utf-8") as f:
                    log.info("Loaded news from local cache.")
                    return json.load(f)
        except Exception as e:
            log.error(f"Failed to load local news cache: {e}")
        return []

    def _save_local_cache(self, news_items):
        try:
            with open(self.CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(news_items, f, ensure_ascii=False, indent=2)
                log.debug("Saved news to local cache.")
        except Exception as e:
            log.error(f"Failed to save local news cache: {e}")

    def _fetch(self, callback):
        max_retries = 3
        timeout_seconds = 5
        news_items = []
        success = False

        for attempt in range(1, max_retries + 1):
            try:
                log.info(f"Fetching news from server (Attempt {attempt}/{max_retries})...")
                # feedparser doesn't strictly support timeouts directly via kwargs in older versions,
                # but it respects socket defaults. For safety, we wrap the call.
                import socket
                socket.setdefaulttimeout(timeout_seconds)

                # Using a custom User-Agent is sometimes required to bypass basic bot protection
                # Often RSS endpoints block feedparser explicitly, or send malformed data if headers are weird.
                import requests
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                resp = requests.get(self.NEWS_URL, headers=headers, timeout=timeout_seconds)
                resp.raise_for_status()

                feed = feedparser.parse(resp.content)

                # feedparser.bozo indicates an error, but sometimes feeds are just slightly malformed (e.g. strict XML errors)
                # If we have entries, we should ignore strict bozo errors.
                if not feed.entries:
                    # Sometimes minecraft RSS feeds are broken xml. Let's try to repair it slightly or fallback.
                    # Since it's just news, if feedparser fails completely, we raise.
                    if feed.bozo:
                        # Attempt to parse json if it was actually a json endpoint mistakenly called
                        try:
                            data = resp.json()
                            # Convert generic json array to feed entries if possible
                            feed.entries = data.get('articleGrid', []) # Mocking structure
                        except Exception:
                            raise Exception(f"Feed parsing error: {feed.bozo_exception}")

                    if not getattr(feed, 'entries', None):
                        raise Exception("Feed is empty or invalid.")

                for entry in feed.entries[:6]: # Get top 6 news
                    news_items.append({
                        "title": entry.get("title", "Без названия"),
                        "link": entry.get("link", ""),
                        "summary": entry.get("summary", "Нет описания")[:150] + "...",
                        "published": entry.get("published", "")
                    })

                success = True
                log.info(f"Successfully fetched {len(news_items)} news items.")
                self._save_local_cache(news_items)
                break # Exit retry loop

            except Exception as e:
                log.warning(f"Attempt {attempt} failed to fetch news: {e}")
                time.sleep(1) # Wait before retry

        if not success:
            log.warning("All attempts to fetch live news failed. Falling back to local cache.")
            news_items = self._load_local_cache()

        if callback:
            # Always wrap callbacks in try-except so a bad UI update doesn't crash the worker thread
            try:
                callback(news_items)
            except Exception as e:
                log.error(f"Error in news callback: {e}")
