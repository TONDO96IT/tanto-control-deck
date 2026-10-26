import asyncio
import subprocess
import time
from collections import deque
from pathlib import Path
import psutil
from loguru import logger

from core.config import ProcessConfig
from core.events import bus


class ProcessManager:
    """
    Monitors the game server process (e.g., BF2142_w32ded.exe).
    If it crashes, it attempts to restart it automatically.
    """

    def __init__(self, cfg: ProcessConfig):
        self.cfg = cfg
        self.proc = None
        self._restarts = deque()  # Timestamps of recent restarts
        self._stdout_file = None

    def _is_alive(self) -> bool:
        """Checks if the server process is currently running."""
        exe_name = Path(self.cfg.exe_path).name.lower()
        for p in psutil.process_iter(["name"]):
            try:
                if p.info["name"] and p.info["name"].lower() == exe_name:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False

    def _can_restart(self) -> bool:
        """Checks if the server is within its hourly restart limit."""
        now = time.time()
        # Remove restarts older than 1 hour
        while self._restarts and now - self._restarts[0] > 3600:
            self._restarts.popleft()
        return len(self._restarts) < self.cfg.max_restarts_per_hour

    def _start_process(self) -> bool:
        """Launches the server executable."""
        exe = Path(self.cfg.exe_path)
        work = Path(self.cfg.work_dir) if self.cfg.work_dir else exe.parent

        if not exe.exists():
            logger.error(f"Server executable not found at: {exe}")
            return False

        # Prepare output log file
        log_path = Path(self.cfg.stdout_log)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        self._stdout_file = log_path.open("a", encoding="utf-8", errors="ignore")

        try:
            # Start the process without opening a visible window
            self.proc = subprocess.Popen(
                [str(exe), *self.cfg.args],
                cwd=str(work),
                stdout=self._stdout_file,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
            )
            logger.info(f"Game server started (PID: {self.proc.pid})")
            self._restarts.append(time.time())
            return True
        except Exception as e:
            logger.error(f"Failed to start game server: {e}")
            return False

    async def monitor_loop(self):
        """Main background loop for monitoring and restarting."""
        if not self.cfg.enabled:
            logger.info("Process Manager is disabled in config.")
            return

        logger.info("Process Manager started. Watching for crashes...")

        while True:
            await asyncio.sleep(self.cfg.check_interval_sec)

            if self._is_alive():
                continue

            logger.warning("Game server is down!")
            await bus.emit("process.down")

            if not self._can_restart():
                logger.error(f"Restart limit reached ({self.cfg.max_restarts_per_hour}/hour). Waiting...")
                await bus.emit("process.giveup")
                continue

            logger.info(f"Waiting {self.cfg.restart_delay_sec}s before restarting...")
            await asyncio.sleep(self.cfg.restart_delay_sec)

            if self._is_alive():
                logger.info("Server was started manually, skipping auto-restart.")
                continue

            if self._start_process():
                await bus.emit("process.restarted")

    def get_status(self) -> dict:
        """Returns current status for the UI."""
        now = time.time()
        recent = [t for t in self._restarts if now - t < 3600]
        return {
            "alive": self._is_alive(),
            "restarts_last_hour": len(recent),
            "last_restart": time.strftime("%H:%M:%S", time.localtime(max(self._restarts))) if self._restarts else "—",
        }