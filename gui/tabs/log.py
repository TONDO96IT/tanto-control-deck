from datetime import datetime
from pathlib import Path
from nicegui import ui
from core.events import bus

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "events.log"


def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _write_file(line: str):
    try:
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def render():
    ui.label("Server Events").classes("text-lg font-semibold mt-4")

    # --- Filters & Actions ---
    with ui.row().classes("w-full items-center gap-3 flex-wrap"):
        ui.label("Filters:").classes("text-sm text-gray-400")
        f_admin = ui.checkbox("Admin", value=True)
        f_broadcast = ui.checkbox("Broadcast", value=True)
        f_system = ui.checkbox("System", value=True)

        ui.space()

        async def clear_log():
            try:
                log_el.clear()
                log_el.push(f"[{_ts()}] [SYSTEM] Log cleared manually")
            except Exception:
                pass

        def export_log():
            if not LOG_FILE.exists():
                ui.notify("Log file is empty", type="warning")
                return
            ui.download(LOG_FILE.read_bytes(),
                        filename=f"tanto_log_{datetime.now():%Y%m%d_%H%M}.txt")
            ui.notify("Log exported", type="positive")

        ui.button("Clear", on_click=clear_log).props("flat")
        ui.button("Export", on_click=export_log).props("flat")

    # --- Log Output ---
    log_el = ui.log(max_lines=1000).classes(
        "w-full h-[32rem] bg-black font-mono text-xs p-2"
    )

    # --- CSS for colors ---
    ui.add_head_html("""
        <style>
        .log-admin     { color: #fbbf24; } /* amber */
        .log-broadcast { color: #60a5fa; } /* blue */
        .log-system    { color: #34d399; } /* green */
        .log-error     { color: #f87171; } /* red */
        </style>
    """)

    def _push(text: str, kind: str = "system"):
        line = f"[{_ts()}] {text}"
        _write_file(line)
        try:
            log_el.push(line).classes(f"log-{kind}")
        except Exception:
            pass

    def _passes(kind: str) -> bool:
        try:
            if kind == "admin": return f_admin.value
            if kind == "broadcast": return f_broadcast.value
            return f_system.value
        except Exception:
            return True

    # --- Event Handlers ---
    async def on_admin(payload):
        if not _passes("admin"): return
        act = payload.get("action", "?")
        tgt = payload.get("target", "?")
        _push(f"[ADMIN] {act.upper()} -> {tgt}", "admin")

    async def on_broadcast(payload):
        if not _passes("broadcast"): return
        _push(f"[BROADCAST] {payload.get('message', '')}", "broadcast")

    async def on_connected(_=None):
        if not _passes("system"): return
        _push("[SYSTEM] RCON connected", "system")

    bus.on("admin.action", on_admin)
    bus.on("broadcast.sent", on_broadcast)
    bus.on("rcon.connected", on_connected)

    ui.label(
        f"Kicks, bans, map changes and broadcasts appear here. File: {LOG_FILE}"
    ).classes("text-xs text-gray-500 mt-2")