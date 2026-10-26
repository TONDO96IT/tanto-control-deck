from datetime import datetime
from nicegui import ui
from core.events import bus

COLUMNS = [
    {"name": "id", "label": "ID", "field": "id", "align": "left"},
    {"name": "name", "label": "Name", "field": "name", "align": "left"},
    {"name": "ip", "label": "IP", "field": "ip", "align": "left"},
    {"name": "port", "label": "Port", "field": "port", "align": "left"},
    {"name": "actions", "label": "Actions", "field": "actions", "align": "center"},
]

ACTIONS_SLOT = """
    <q-td :props="props">
        <q-btn dense color="orange" label="KICK"
               @click="$parent.$emit('kick', props.row)" />
        <q-btn dense color="red" label="BAN"
               @click="$parent.$emit('ban', props.row)" />
    </q-td>
"""

BAN_REASONS = ["Manual", "Aimbot", "Wallhack", "Teamkill",
               "Spawnkill", "Racism", "AFK", "Cheating"]

BAN_DURATIONS = {
    0: "Permanent",
    60: "1 hour",
    1440: "1 day",
    10080: "1 week",
    43200: "30 days",
}


def render(rcon):
    ui.label("Players on Server").classes("text-lg font-semibold mt-4")
    ui.label("Data is fetched manually via the Refresh button.") \
        .classes("text-xs text-gray-500")

    # --- Status Bar ---
    with ui.row().classes("w-full items-center gap-3 mt-3"):
        players_count = ui.label("Players: —").classes("text-md font-bold")
        updated_label = ui.label("Updated: —").classes("text-xs text-gray-400")
        ui.space()

        refresh_btn = ui.button("Refresh", color="primary")
        spinner = ui.spinner(size="lg", color="primary")
        spinner.set_visibility(False)

    table = ui.table(columns=COLUMNS, rows=[], row_key="id").classes("w-full")
    table.add_slot("body-cell-actions", ACTIONS_SLOT)

    # --- Ban Dialog ---
    ban_target = {"id": None, "name": "", "ip": ""}

    ban_dialog = ui.dialog()
    with ban_dialog, ui.card().classes("w-96"):
        ui.label("Ban Player").classes("text-lg font-bold text-red-400")
        ban_target_label = ui.label("").classes("text-sm text-gray-400")
        ban_reason = ui.select(options=BAN_REASONS, value="Manual",
                               label="Reason").classes("w-full")
        ban_duration = ui.select(options=BAN_DURATIONS, value=0,
                                 label="Duration").classes("w-full")
        with ui.row().classes("w-full justify-end mt-2"):
            ui.button("Cancel", on_click=lambda: ban_dialog.close()).props("flat")
            ui.button("Ban", color="red", on_click=lambda: do_ban())

    async def open_ban_dialog(row):
        ban_target["id"] = row["id"]
        ban_target["name"] = row["name"]
        ban_target["ip"] = row.get("ip", "")
        ban_target_label.text = f"{row['name']} ({row.get('ip', '?')})"
        ban_reason.value = "Manual"
        ban_duration.value = 0
        ban_dialog.open()

    async def do_ban():
        if ban_target["id"] is None:
            return
        timeout_min = int(ban_duration.value or 0)
        reason = ban_reason.value or "Manual"
        await rcon.ban(
            ban_target["id"],
            timeout=timeout_min,
            name=ban_target["name"],
            reason=reason,
        )
        ui.notify(f"Banned: {ban_target['name']} ({reason})", type="negative")
        ban_dialog.close()
        await refresh()

    async def on_kick(e):
        await rcon.kick(e.args["id"], e.args.get("name", ""))
        ui.notify(f"Kicked: {e.args['name']}", type="warning")
        await refresh()

    table.on("kick", on_kick)
    table.on("ban", lambda e: open_ban_dialog(e.args))

    # --- Normalization ---
    def _normalize(p):
        return {
            "id": p.get("id"),
            "name": p.get("name", "?"),
            "ip": p.get("ip", "") or "-",
            "port": p.get("port", "") or "-",
        }

    # --- Refresh Logic ---
    async def refresh():
        spinner.set_visibility(True)
        refresh_btn.disable()
        try:
            players = await rcon.get_players()
            rows = [_normalize(p) for p in (players or [])]
            table.rows = rows
            table.update()
            players_count.text = f"Players: {len(rows)}"
            updated_label.text = f"Updated: {datetime.now().strftime('%H:%M:%S')}"
            if rows:
                ui.notify(f"Updated: {len(rows)} players", type="positive")
            else:
                ui.notify("Server is empty", type="info")
        except Exception as e:
            ui.notify(f"Error: {e}", type="negative")
        finally:
            spinner.set_visibility(False)
            refresh_btn.enable()

    refresh_btn.on("click", refresh)

    # Auto-refresh on page load (once)
    ui.timer(0.5, refresh, once=True)