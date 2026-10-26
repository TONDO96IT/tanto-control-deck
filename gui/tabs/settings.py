from nicegui import ui
from core.rcon_manager import SETTINGS_GROUPS, SETTINGS_SCHEMA


def render(rcon):
    ui.label("Server Settings").classes("text-lg font-semibold mt-4")
    ui.label("Write access is limited to int/bool. Strings (serverName, URLs) are read-only.") \
        .classes("text-xs text-yellow-600")

    # --- Status Bar ---
    with ui.row().classes("w-full items-center gap-3 mt-2"):
        status_icon = ui.icon("check_circle", color="green").classes("text-lg")
        status_label = ui.label("Ready").classes("text-sm text-gray-400")
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

    inputs = {}
    busy_flag = {"value": False}

    def safe_notify(text, type="info"):
        try:
            ui.notify(text, type=type)
        except Exception:
            pass

    def safe_update(widget):
        try:
            widget.update()
        except Exception:
            pass

    async def refresh_group(group_label, keys):
        """Reads only the fields of a specific group."""
        if busy_flag["value"]: return
        busy_flag["value"] = True
        set_busy(f"Reading: {group_label} ...")
        try:
            data = await rcon.get_settings(only_keys=list(keys))
            for key in keys:
                if key not in inputs: continue
                kind = SETTINGS_SCHEMA[key][1]
                val = data.get(key)
                widget = inputs[key]
                if val is None: continue
                try:
                    if kind == "bool":
                        widget.value = bool(val)
                    elif kind == "int":
                        widget.value = int(val)
                    else:
                        widget.value = str(val)
                except (ValueError, TypeError):
                    continue
                safe_update(widget)
            set_ready(f"{group_label} updated")
            safe_notify(f"{group_label} updated", type="info")
        except Exception as e:
            set_error(f"Error: {e}")
            safe_notify(f"Error: {e}", type="negative")
        finally:
            busy_flag["value"] = False

    async def apply_group(group_label, keys):
        """Applies changes only for a specific group."""
        if busy_flag["value"]: return
        busy_flag["value"] = True
        set_busy(f"Applying: {group_label} ...")
        changed = 0
        skipped = 0
        try:
            for key in keys:
                kind = SETTINGS_SCHEMA[key][1]
                if kind == "str":
                    skipped += 1
                    continue
                
                val = inputs[key].value
                if val is None or val == "": continue
                
                ok = await rcon.set_setting(key, val)
                if ok: changed += 1
                else: skipped += 1
            
            msg = f"{group_label}: applied {changed}"
            if skipped: msg += f", skipped {skipped}"
            set_ready(msg)
            safe_notify(msg, type="positive" if changed else "warning")
        except Exception as e:
            set_error(f"Error: {e}")
            safe_notify(f"Error: {e}", type="negative")
        finally:
            busy_flag["value"] = False

    # --- Build UI ---
    for group_label, keys in SETTINGS_GROUPS:
        with ui.card().classes("w-full mt-3"):
            with ui.row().classes("w-full items-center justify-between"):
                ui.label(group_label).classes("text-md font-bold")
                with ui.row().classes("gap-2"):
                    ui.button("Refresh", color="secondary",
                              on_click=lambda gl=group_label, ks=keys: refresh_group(gl, ks)).props("dense")
                    ui.button("Apply", color="primary",
                              on_click=lambda gl=group_label, ks=keys: apply_group(gl, ks)).props("dense")

            with ui.grid(columns=2).classes("w-full gap-3 mt-2"):
                for key in keys:
                    kind = SETTINGS_SCHEMA[key][1]
                    if kind == "bool":
                        inputs[key] = ui.switch(key).classes("w-full")
                    elif kind == "int":
                        inputs[key] = ui.number(label=key).classes("w-full")
                    else:
                        w = ui.input(label=key).classes("w-full")
                        w.props("readonly") # String fields are read-only
                        inputs[key] = w