import asyncio
from nicegui import ui, app
from loguru import logger

from core.config import load_config
from core.rcon_manager import RconManager
from core.process_manager import ProcessManager
from core.events import bus

# Import tabs
from gui.tabs import players, maplist, banlist, console, settings, log as log_tab

# Load configuration
cfg = load_config()

# Initialize core managers
rcon = RconManager(cfg.server, cfg.maplist)
pm = ProcessManager(cfg.process)


@ui.page("/")
def index():
    """Main UI page."""
    ui.dark_mode().enable()
    ui.page_title(f"{cfg.server.name} - Control Deck")

    # --- Header ---
    with ui.header().classes("items-center justify-between bg-slate-900 p-3"):
        ui.label(f"{cfg.server.name}").classes("text-xl font-bold")
        
        with ui.row().classes("items-center gap-4"):
            # Process Manager Status
            proc_status = ui.label().classes("text-xs")
            # RCON Status
            rcon_status = ui.label().classes("text-sm")

    def refresh_header():
        # Update RCON status
        if rcon.connected:
            rcon_status.text = "RCON: Online"
            rcon_status.classes(replace="text-green-400 text-sm")
        else:
            rcon_status.text = "RCON: Offline"
            rcon_status.classes(replace="text-red-400 text-sm")

        # Update Process Manager status
        if not cfg.process.enabled:
            proc_status.text = "PROC: disabled"
            proc_status.classes(replace="text-gray-500 text-xs")
        else:
            st = pm.get_status()
            if st["alive"]:
                proc_status.text = f"PROC: alive | restarts/h: {st['restarts_last_hour']}"
                proc_status.classes(replace="text-green-400 text-xs")
            else:
                proc_status.text = f"PROC: down | restarts/h: {st['restarts_last_hour']}"
                proc_status.classes(replace="text-red-400 text-xs")

    refresh_header()
    ui.timer(2.0, refresh_header)

    # --- Tabs ---
    with ui.tabs().classes("w-full") as tabs:
        tab_players = ui.tab("Players")
        tab_maplist = ui.tab("Maplist")
        tab_banlist = ui.tab("Banlist")
        tab_settings = ui.tab("Settings")
        tab_console = ui.tab("Console")
        tab_log = ui.tab("Log")

    with ui.tab_panels(tabs, value=tab_players).classes("w-full"):
        with ui.tab_panel(tab_players):
            players.render(rcon)
        with ui.tab_panel(tab_maplist):
            maplist.render(rcon)
        with ui.tab_panel(tab_banlist):
            banlist.render(rcon)
        with ui.tab_panel(tab_settings):
            settings.render(rcon)
        with ui.tab_panel(tab_console):
            console.render(rcon)
        with ui.tab_panel(tab_log):
            log_tab.render()


@app.on_startup
async def startup():
    """Runs when the app starts. Initializes logging and background tasks."""
    logger.add(cfg.logging.file, level=cfg.logging.level, rotation="10 MB", retention="5 days")
    logger.info(f"Control Deck starting for {cfg.server.name} (mock={cfg.server.mock})")
    
    # Start background tasks
    asyncio.create_task(rcon.monitoring_loop(cfg.monitoring.player_refresh_sec))
    asyncio.create_task(rcon.broadcast_loop(cfg.broadcast))
    asyncio.create_task(pm.monitor_loop())


# Run the app
ui.run(host="0.0.0.0", port=8080, title="Control Deck", reload=False, show=True)