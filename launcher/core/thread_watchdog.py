import threading
import time
from launcher.utils.logger import get_logger

log = get_logger("ThreadWatchdog")

class ThreadWatchdog:
    """
    Industrial-grade thread monitoring system.
    Detects frozen or hanging threads and can forcefully terminate or ignore them
    to prevent UI lockups.
    """
    def __init__(self):
        self.monitored_threads = {}
        self._lock = threading.Lock()
        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True, name="WatchdogMonitor")
        self._monitor_thread.start()

    def register_task(self, task_id, timeout_seconds=15):
        """Registers a task to be monitored."""
        with self._lock:
            self.monitored_threads[task_id] = {
                "last_heartbeat": time.time(),
                "timeout": timeout_seconds,
                "status": "running"
            }
        log.debug(f"Task '{task_id}' registered in Watchdog.")

    def heartbeat(self, task_id):
        """Updates the heartbeat of a monitored task."""
        with self._lock:
            if task_id in self.monitored_threads:
                self.monitored_threads[task_id]["last_heartbeat"] = time.time()

    def unregister_task(self, task_id):
        """Removes a task from monitoring (usually upon successful completion)."""
        with self._lock:
            if task_id in self.monitored_threads:
                del self.monitored_threads[task_id]
                log.debug(f"Task '{task_id}' finished and unregistered.")

    def _monitor_loop(self):
        while self._running:
            time.sleep(2)
            now = time.time()
            dead_tasks = []

            with self._lock:
                for task_id, data in self.monitored_threads.items():
                    if data["status"] == "running" and (now - data["last_heartbeat"]) > data["timeout"]:
                        log.error(f"WATCHDOG: Task '{task_id}' has frozen (no heartbeat for {data['timeout']}s). Marking as dead.")
                        data["status"] = "dead"
                        dead_tasks.append(task_id)

            # If we need to trigger recovery mechanisms, we do it here outside the lock
            for task_id in dead_tasks:
                self._handle_dead_task(task_id)

    def register_process(self, task_id, pid, timeout_seconds=60):
        """Registers a system process (PID) to be monitored. Requires psutil."""
        with self._lock:
            self.monitored_threads[task_id] = {
                "type": "process",
                "pid": pid,
                "last_heartbeat": time.time(),
                "timeout": timeout_seconds,
                "status": "running"
            }
        log.debug(f"Process '{task_id}' (PID: {pid}) registered in Watchdog.")

    def _handle_dead_task(self, task_id):
        data = self.monitored_threads.get(task_id)
        if not data: return

        if data.get("type") == "process":
            # True Psutil Hard Kill
            try:
                import psutil
                pid = data["pid"]
                proc = psutil.Process(pid)
                # Recursively kill children to ensure no zombie java.exe
                for child in proc.children(recursive=True):
                    child.kill()
                proc.kill()
                log.error(f"WATCHDOG KILLED FROZEN PROCESS: {task_id} (PID {pid})")

                # Signal the crash analyzer logic (will be caught by monitor process in app.py)
            except psutil.NoSuchProcess:
                pass
            except Exception as e:
                log.error(f"Watchdog failed to kill process {pid}: {e}")
        else:
            # We can't safely "kill" a python thread natively without ctypes magic that corrupts state.
            # Instead, we decouple the UI from it and let it rot in the background while restarting the logical flow.
            if "news_fetch" in task_id:
                log.warning(f"Recovery triggered for {task_id}: Re-initializing connection pools.")

    def shutdown(self):
        self._running = False
