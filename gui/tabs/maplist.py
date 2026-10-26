from datetime import datetime
from nicegui import ui
from core.maps import (
    get_modes,
    get_maps_for_mode,
    get_sizes_for_map,
    mode_label,
)


def render(rcon):
    ui.label("Map Rotation").classes("text-lg font-semibold mt-4")

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
        {"name": "id", "label": "#", "field": "id", "align": "left"},
        {"name": "name", "label": "Map", "field": "name", "align": "left"},
        {"name": "mode", "label": "Mode", "field": "mode", "align": "left"},
        {"name": "size", "label": "Size", "field": "size", "align": "left"},
        {"name": "actions", "label": "Actions", "field": "actions", "align": "center"},
    ]

    table = ui.table(columns=columns, rows=[], row_key="id").classes("w-full")

    table.add_slot("body-cell-actions", """
        <q-td :props="props">
            <q-btn dense color="orange" label="CHANGE NOW"
                   @click="$parent.$emit('change_now', props.row)" />
            <q-btn dense color="red" label="REMOVE"
                   @click="$parent.$emit('remove', props.row)" />
        </q-td>
    """)

    busy_flag = {"value": False}

    async def refresh():
        if busy_flag["value"]: return
        busy_flag["value"] = True
        set_busy("Reading maplist...")
        try:
            maps = await rcon.get_maplist()
            table.rows = maps or []
            table.update()
            updated_label.text = f"Updated: {datetime.now().strftime('%H:%M:%S')}"
            set_ready(f"Loaded: {len(table.rows)} maps")
        except Exception as e:
            set_error(f"Error: {e}")
        finally:
            busy_flag["value"] = False

    # --- CHANGE NOW ---
    change_target = {"id": None, "name": ""}
    change_dialog = ui.dialog()
    
    with change_dialog, ui.card().classes("w-96"):
        ui.label("Change Map NOW?").classes("text-lg font-bold text-orange-400")
        change_target_label = ui.label("").classes("text-sm text-gray-400")
        ui.label("Current round will be interrupted.").classes("text-xs text-gray-500")
        with ui.row().classes("w-full justify-end mt-2"):
            ui.button("Cancel", on_click=lambda: change_dialog.close()).props("flat")
            ui.button("Yes, change", color="orange", on_click=lambda: do_change_now())

    async def open_change_dialog(row):
        change_target["id"] = row["id"]
        change_target["name"] = row["name"]
        change_target_label.text = f"{row['name']} ({row['mode']}, {row['size']})"
        change_dialog.open()

    async def do_change_now():
        if change_target["id"] is None or busy_flag["value"]: return
        busy_flag["value"] = True
        change_dialog.close()
        set_busy(f"Changing map: {change_target['name']} ...")
        try:
            await rcon.change_map_now(change_target["id"])
            set_ready(f"Map changed: {change_target['name']}")
            ui.notify(f"Map changed: {change_target['name']}", type="positive")
        except Exception as e:
            set_error(f"Error: {e}")
        finally:
            busy_flag["value"] = False

    # --- REMOVE ---
    async def on_remove(e):
        if busy_flag["value"]: return
        busy_flag["value"] = True
        set_busy(f"Removing: {e.args['name']} ...")
        try:
            await rcon.remove_map(e.args["id"])
            await refresh()
            refresh_map_options()
            set_ready(f"Removed: {e.args['name']}")
            ui.notify(f"Removed: {e.args['name']}", type="warning")
        except Exception as ex:
            set_error(f"Error: {ex}")
        finally:
            busy_flag["value"] = False

    table.on("change_now", lambda e: open_change_dialog(e.args))
    table.on("remove", on_remove)

    # --- Action Buttons ---
    with ui.row().classes("w-full items-center gap-2 mt-2 flex-wrap"):
        ui.button("Refresh", on_click=refresh)
        ui.button("Clear Maplist", color="negative", on_click=lambda: clear_and_refresh())
        ui.button("Save to File", color="primary", on_click=lambda: save_to_file())

    async def toggle_autosave(e):
        rcon.maplist_cfg.auto_save = bool(e.value)
        ui.notify(f"Autosave {'enabled' if e.value else 'disabled'}", type="info")

    ui.checkbox("Autosave maplist", value=bool(rcon.maplist_cfg.auto_save), on_change=toggle_autosave)
    ui.label(f"Path: {rcon.maplist_cfg.path}").classes("text-xs text-gray-500")

    async def clear_and_refresh():
        if busy_flag["value"]: return
        busy_flag["value"] = True
        set_busy("Clearing maplist...")
        try:
            await rcon.clear_maplist()
            await refresh()
            refresh_map_options()
            set_ready("Maplist cleared")
            ui.notify("Maplist cleared", type="warning")
        except Exception as e:
            set_error(f"Error: {e}")
        finally:
            busy_flag["value"] = False

    async def save_to_file():
        if busy_flag["value"]: return
        busy_flag["value"] = True
        set_busy("Saving to file...")
        try:
            ok = await rcon.save_maplist_to_file()
            if ok:
                set_ready(f"Saved: {rcon.maplist_cfg.path}")
                ui.notify("Saved successfully", type="positive")
            else:
                set_error("Failed to save (empty list?)")
        except Exception as e:
            set_error(f"Error: {e}")
        finally:
            busy_flag["value"] = False

    # --- Add Map Form ---
    ui.separator()
    ui.label("Add Map").classes("text-md font-semibold")

    mode_options = {m: mode_label(m) for m in get_modes()}

    with ui.row().classes("w-full items-center gap-2"):
        mode_in = ui.select(options=mode_options, value="gpm_cq", label="Mode").classes("w-48")
        map_in = ui.select(options=get_maps_for_mode("gpm_cq"), value="Verdun", label="Map").classes("w-64")
        size_in = ui.select(options=get_sizes_for_map("gpm_cq", "Verdun"), value=64, label="Size").classes("w-28")

        def is_duplicate(map_name, mode, size):
            for m in (table.rows or []):
                if (m.get("name") == map_name and m.get("mode") == mode and int(m.get("size", 0)) == int(size)):
                    return True
            return False

        def refresh_map_options():
            mode = mode_in.value
            if not mode: return
            all_maps = get_maps_for_mode(mode)
            available = []
            for name in all_maps:
                sizes = get_sizes_for_map(mode, name)
                if any(not is_duplicate(name, mode, sz) for sz in sizes):
                    available.append(name)

            current = map_in.value
            map_in.options = available
            if available and current not in available:
                map_in.value = available[0]
            elif not available:
                map_in.value = None
            map_in.update()
            on_map_change()

        def on_mode_change():
            refresh_map_options()

        def on_map_change():
            if map_in.value and mode_in.value:
                sizes = get_sizes_for_map(mode_in.value, map_in.value)
                free_sizes = [s for s in sizes if not is_duplicate(map_in.value, mode_in.value, s)]
                size_in.options = free_sizes if free_sizes else sizes
                size_in.value = free_sizes[-1] if free_sizes else sizes[-1]
            else:
                size_in.options = []
                size_in.value = None
            size_in.update()

        mode_in.on_value_change(lambda _: on_mode_change())
        map_in.on_value_change(lambda _: on_map_change())

        async def add_map():
            if busy_flag["value"]: return
            if not map_in.value or not size_in.value:
                ui.notify("Pick a map and size", type="warning")
                return
            if is_duplicate(map_in.value, mode_in.value, size_in.value):
                ui.notify("Already in rotation", type="negative")
                return
            
            busy_flag["value"] = True
            set_busy(f"Adding: {map_in.value} ...")
            try:
                await rcon.append_map(map_in.value, mode_in.value, size_in.value)
                await refresh()
                refresh_map_options()
                set_ready(f"Added: {map_in.value} ({size_in.value})")
                ui.notify(f"Added: {map_in.value}", type="positive")
            except Exception as e:
                set_error(f"Error: {e}")
            finally:
                busy_flag["value"] = False

        ui.button("Add", on_click=add_map)

    # Initial load
    ui.timer(0.5, refresh, once=True)