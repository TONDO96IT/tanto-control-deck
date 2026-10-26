from datetime import datetime
from nicegui import ui
from core import ban_notes

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
    ui.label("Ban List (ban_notes.txt)").classes("text-lg font-semibold mt-4")
    ui.label("Bans are stored locally in a text file. Timeouts are informational only.") \
        .classes("text-xs text-gray-500")

    # --- Status Bar ---
    with ui.row().classes("w-full items-center gap-3 mt-2"):
        status_icon = ui.icon("check_circle", color="green").classes("text-lg")
        status_label = ui.label("Ready").classes("text-sm text-gray-400")
        updated_label = ui.label("Updated: —").classes("text-xs text-gray-500")
        ui.space()
        spinner = ui.spinner(size="md", color="primary")
        spinner.set_visibility(False)

    def set_busy(text="Sending..."):
        status_icon.name = "hourglass_top"
        status_icon.props("color=orange")
        status_label.text = text
        status_label.classes(replace="text-sm text-orange-400")
        spinner.set_visibility(True)

    def set_ready(text="Ready"):
        status_icon.name = "check_circle"
        status_icon.props("color=green")
        status_label.text = text
        status_label.classes(replace="text-sm text-gray-400")
        spinner.set_visibility(False)

    def set_error(text):
        status_icon.name = "error"
        status_icon.props("color=red")
        status_label.text = text
        status_label.classes(replace="text-sm text-red-400")
        spinner.set_visibility(False)

    # --- Table ---
    columns = [
        {"name": "id", "label": "ID", "field": "id", "align": "left", "style": "width: 50px"},
        {"name": "ip", "label": "IP", "field": "ip", "align": "left", "style": "width: 140px"},
        {"name": "player", "label": "Name", "field": "player", "align": "left", "style": "width: 140px"},
        {"name": "reason", "label": "Reason", "field": "reason", "align": "left", "style": "width: 120px"},
        {"name": "admin", "label": "Admin", "field": "admin", "align": "left", "style": "width: 100px"},
        {"name": "created_at", "label": "Created", "field": "created_at", "align": "left", "style": "width: 140px"},
        {"name": "expires_at", "label": "Expires", "field": "expires_at", "align": "left", "style": "width: 140px"},
        {"name": "actions", "label": "", "field": "actions", "align": "center", "style": "width: 130px"},
    ]

    table = ui.table(columns=columns, rows=[], row_key="id").classes("w-full")

    table.add_slot("body-cell-actions", """
        <q-td :props="props" class="text-center">
            <q-btn dense color="red" label="UNBAN"
                   @click="$parent.$emit('unban', props.row)" />
        </q-td>
    """)

    table.add_slot("body-cell-expires_at", """
        <q-td :props="props" :class="props.row.expired ? 'text-gray-500' : ''">
            {{ props.value }}
        </q-td>
    """)

    all_bans = []
    busy_flag = {"value": False}

    def refresh():
        nonlocal all_bans
        if busy_flag["value"]: return
        busy_flag["value"] = True
        set_busy("Reading ban list...")
        try:
            all_bans = ban_notes.get_bans()
            apply_filter()
            updated_label.text = f"Updated: {datetime.now().strftime('%H:%M:%S')}"
            set_ready(f"Loaded: {len(all_bans)} bans")
        except Exception as e:
            set_error(f"Error: {e}")
        finally:
            busy_flag["value"] = False

    def apply_filter():
        q = (search.value or "").lower().strip()
        if not q:
            table.rows = all_bans
        else:
            table.rows = [
                b for b in all_bans
                if q in (b.get("ip", "") or "").lower()
                or q in (b.get("player", "") or "").lower()
                or q in (b.get("reason", "") or "").lower()
            ]
        table.update()

    async def on_unban(e):
        if busy_flag["value"]: return
        ip = e.args["ip"]
        busy_flag["value"] = True
        set_busy(f"Unbanning: {ip} ...")
        try:
            ban_notes.remove_ban(ip)
            try:
                await rcon.remove_ban(ip)
            except Exception:
                pass
            refresh()
            ui.notify(f"Unbanned: {ip}", type="positive")
        except Exception as ex:
            set_error(f"Error: {ex}")
        finally:
            busy_flag["value"] = False

    table.on("unban", on_unban)

    # --- Search & Actions ---
    with ui.row().classes("w-full items-center gap-2 mt-2 flex-wrap"):
        search = ui.input(placeholder="Search by IP / Name / Reason",
                          on_change=lambda _: apply_filter()).classes("w-72")
        ui.button("Refresh", on_click=refresh)
        ui.button("Clear Ban List", color="negative", on_click=lambda: open_clear_dialog())

    # --- Clear Dialog ---
    clear_dialog = ui.dialog()
    with clear_dialog, ui.card().classes("w-96"):
        ui.label("⚠️ Clear ENTIRE ban list?").classes("text-lg font-bold text-red-400")
        ui.label("All bans will be removed from the local file and server.") \
            .classes("text-sm text-gray-400")
        with ui.row().classes("w-full justify-end mt-2"):
            ui.button("Cancel", on_click=lambda: clear_dialog.close()).props("flat")
            ui.button("YES, DELETE ALL", color="red", on_click=lambda: do_clear_all())

    def open_clear_dialog():
        clear_dialog.open()

    async def do_clear_all():
        if busy_flag["value"]: return
        busy_flag["value"] = True
        set_busy("Clearing ban list...")
        try:
            ban_notes.clear_bans()
            try:
                await rcon.unban_all()
            except Exception:
                pass
            refresh()
            clear_dialog.close()
            ui.notify("Ban list cleared", type="warning")
        except Exception as ex:
            set_error(f"Error: {ex}")
        finally:
            busy_flag["value"] = False

    # --- Add Ban Form ---
    ui.separator()
    ui.label("Add Ban").classes("text-md font-semibold")

    with ui.row().classes("w-full items-center gap-2 flex-wrap"):
        ip_in = ui.input(placeholder="192.168.1.100").classes("w-56")
        player_in = ui.input(placeholder="Name (opt.)").classes("w-48")
        reason_in = ui.select(options=BAN_REASONS, value="Manual", label="Reason").classes("w-44")
        duration_in = ui.select(options=BAN_DURATIONS, value=0, label="Duration").classes("w-36")

        async def add_ban():
            if busy_flag["value"]: return
            ip = (ip_in.value or "").strip()
            if not ip:
                ui.notify("Enter an IP", type="warning")
                return
            
            parts = ip.split(".")
            if len(parts) != 4 or not all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
                ui.notify("Invalid IP address", type="negative")
                return

            busy_flag["value"] = True
            timeout_min = int(duration_in.value or 0)
            set_busy(f"Banning: {ip} ...")
            try:
                ban_notes.add_ban(
                    ip=ip,
                    player=(player_in.value or "").strip(),
                    reason=reason_in.value or "Manual",
                    timeout_min=timeout_min,
                )
                try:
                    await rcon.add_ban(ip)
                except Exception as e:
                    ui.notify(f"Server warning: {e}", type="warning")
                
                refresh()
                ui.notify(f"Banned: {ip}", type="negative")
                ip_in.value = ""
                player_in.value = ""
                reason_in.value = "Manual"
                duration_in.value = 0
            except Exception as ex:
                set_error(f"Error: {ex}")
            finally:
                busy_flag["value"] = False

        ui.button("Ban", color="negative", on_click=add_ban)

    # --- Search by Nick ---
    ui.separator()
    ui.label("Find by Nickname").classes("text-md font-semibold")
    with ui.row().classes("w-full items-center gap-2"):
        nick_search = ui.input(placeholder="Player name").classes("w-72")
        nick_result = ui.label("").classes("text-xs text-gray-400")

        def do_search():
            nick = (nick_search.value or "").strip()
            if not nick:
                nick_result.text = ""
                return
            found = ban_notes.find_by_nick(nick)
            if found:
                lines = [f"{b['player']} -> {b['ip']} ({b['reason']})" for b in found]
                nick_result.text = "\n".join(lines)
            else:
                nick_result.text = "Not found"

        ui.button("Search", on_click=do_search)

    # Initial load
    ui.timer(0.5, refresh, once=True)