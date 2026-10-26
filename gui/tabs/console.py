import asyncio
from nicegui import ui


BROADCAST_PRESETS = [
    "Welcome to the server!",
    "Play fair, respect other players!",
    "Visit our website for more info.",
    "Follow the server rules!",
]

QUICK_COMMANDS = [
    ("Next Map", "admin.runNextLevel"),
    ("Restart Map", "admin.restartMap"),
    ("List Players", "admin.listPlayers"),
    ("List Bans", "admin.listBannedAddresses"),
    ("Clear Bans", "admin.clearBanList"),
]


def render(rcon):
    ui.label("Server Control").classes("text-lg font-semibold mt-4")

    output = ui.log(max_lines=200).classes(
        "w-full h-32 bg-black text-green-400 font-mono text-xs p-2"
    )

    def push(text: str):
        output.push(text)

    # --- Quick Actions ---
    ui.label("Quick Actions").classes("text-md font-semibold mt-3")

    async def do_next_level():
        try:
            await rcon.run_next_level()
            push("[action] next level -> sent")
            ui.notify("Next map triggered", type="positive")
        except Exception as e:
            push(f"[error] {e}")
            ui.notify(f"Error: {e}", type="negative")

    async def do_restart_map():
        try:
            await rcon.restart_map()
            push("[action] restart map -> sent")
            ui.notify("Map restarted", type="positive")
        except Exception as e:
            push(f"[error] {e}")
            ui.notify(f"Error: {e}", type="negative")

    async def do_save_maplist():
        try:
            ok = await rcon.save_maplist_to_file()
            if ok:
                push("[action] maplist saved")
                ui.notify("Maplist saved", type="positive")
            else:
                push("[error] failed to save maplist")
        except Exception as e:
            push(f"[error] {e}")

    async def do_clear_bans():
        try:
            from core import ban_notes
            ban_notes.clear_bans()
            await rcon.unban_all()
            push("[action] bans cleared")
            ui.notify("Bans cleared", type="warning")
        except Exception as e:
            push(f"[error] {e}")

    with ui.row().classes("w-full items-center gap-2 flex-wrap"):
        ui.button("Next Map", on_click=do_next_level).props("outline")
        ui.button("Restart Map", on_click=do_restart_map).props("outline")
        ui.button("Save Maplist", on_click=do_save_maplist).props("outline")
        ui.button("Clear Bans", on_click=do_clear_bans).props("outline")

    ui.separator()

    # --- Broadcast ---
    ui.label("Broadcast to Chat").classes("text-md font-semibold mt-3")
    ui.label("(Messages sent to the server should be in ASCII/Latin)")\
        .classes("text-xs text-gray-500")

    with ui.row().classes("w-full items-center gap-2 mt-2"):
        msg = ui.select(options=BROADCAST_PRESETS, value=BROADCAST_PRESETS[0],
                        label="Message").classes("flex-grow")

        async def broadcast():
            text = (msg.value or "").strip()
            if not text:
                ui.notify("Pick a message", type="warning")
                return
            await rcon.say(text)
            push(f'> admin.say "{text}" all')
            push("[broadcast] sent")
            ui.notify("Sent to chat", type="positive")

        ui.button("Send to All", on_click=broadcast)

    with ui.row().classes("w-full items-center gap-2"):
        custom = ui.input(placeholder="Custom message (ASCII only)...") \
            .classes("flex-grow")

        async def send_custom():
            text = (custom.value or "").strip()
            if not text:
                ui.notify("Enter a message", type="warning")
                return
            if not text.isascii():
                ui.notify("Warning: Non-ASCII characters may display incorrectly", type="warning")
            await rcon.say(text)
            push(f'> admin.say "{text}" all')
            push("[broadcast] sent")
            custom.value = ""
            ui.notify("Sent to chat", type="positive")

        ui.button("Send Custom", on_click=send_custom)