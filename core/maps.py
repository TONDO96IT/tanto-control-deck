# Static dictionary of all BF2142 maps, modes, and sizes.
# Source: BF2142 dedicated server files.

AVAILABLE_MAPS = {
    "gpm_cq": {
        "Verdun": [16, 32, 64],
        "Tunis_Harbor": [16, 32, 64],
        "Suez_Canal": [16, 32, 64],
        "Strike_at_Karkand": [16, 32, 64],
        "Sidi_Power_Plant": [16, 32, 64],
        "Shuhia_Taiba": [16, 32, 64],
        "Operation_Shingle": [16, 32, 64],
        "Minsk": [16, 32, 64],
        "Fall_of_Berlin": [16, 32, 64],
        "Cerbere_Landing": [16, 32, 64],
        "Camp_Gibraltar": [16, 32, 64],
        "Belgrade": [16, 32, 64],
    },
    "gpm_ti": {
        "Verdun": [16, 48, 64],
        "Tunis_Harbor": [16, 32, 64],
        "Suez_Canal": [16, 48, 64],
        "Sidi_Power_Plant": [16, 48, 64],
        "Shuhia_Taiba": [16, 48, 64],
        "Port_Bavaria": [48],
        "Molokai": [48, 64],
        "Minsk": [16, 48, 64],
        "Highway_Tampa": [48],
        "Fall_of_Berlin": [16, 48, 64],
        "Cerbere_Landing": [16, 48, 64],
        "Camp_Gibraltar": [16, 32, 64],
        "Bridge_at_Remagen": [48],
        "Belgrade": [16, 48, 64],
    },
    "gpm_sl": {
        "Yellow_Knife": [16, 32, 64],
        "Port_Bavaria": [16, 32, 64],
        "Operation_Shingle": [16, 32, 64],
        "Operation_Blue_Pearl": [16, 32, 64],
        "Liberation_of_Leipzig": [16, 32, 64],
        "Highway_Tampa": [16, 32, 64],
        "Bridge_at_Remagen": [16, 32, 64],
    },
    "gpm_nv": {
        "Verdun": [16, 32, 64],
        "Tunis_Harbor": [16, 32, 64],
        "Suez_Canal": [16, 32, 64],
        "Strike_at_Karkand": [16, 32, 64],
        "Sidi_Power_Plant": [16, 32, 64],
        "Shuhia_Taiba": [16, 32, 64],
        "Operation_Shingle": [16, 32, 64],
        "Minsk": [16, 32, 64],
        "Fall_of_Berlin": [16, 32, 64],
        "Cerbere_Landing": [16, 32],
        "Camp_Gibraltar": [16, 32],
        "Belgrade": [16, 32],
    },
    "gpm_coop": {
        "Verdun": [16, 32, 64],
        "Tunis_Harbor": [16, 32, 64],
        "Suez_Canal": [16, 32, 64],
        "Sidi_Power_Plant": [16, 32, 64],
        "Shuhia_Taiba": [16, 32, 64],
        "Minsk": [16, 32, 64],
        "Fall_of_Berlin": [16, 32, 64],
        "Cerbere_Landing": [16, 32, 64],
        "Camp_Gibraltar": [16, 32, 64],
        "Belgrade": [16, 32, 64],
    },
    "gpm_ca": {
        "Wake_Island_2142": [64],
    },
}

MODE_LABELS = {
    "gpm_cq": "Conquest",
    "gpm_ti": "Titan",
    "gpm_sl": "Northern Strike",
    "gpm_nv": "No Vehicles",
    "gpm_coop": "Coop",
    "gpm_ca": "Wake Island",
}

MODE_ORDER = ["gpm_cq", "gpm_ti", "gpm_sl", "gpm_nv", "gpm_coop", "gpm_ca"]


def get_modes() -> list[str]:
    """Returns the list of available game modes."""
    return [m for m in MODE_ORDER if m in AVAILABLE_MAPS]


def get_maps_for_mode(mode: str) -> list[str]:
    """Returns all map names for a specific game mode."""
    return list(AVAILABLE_MAPS.get(mode, {}).keys())


def get_sizes_for_map(mode: str, map_name: str) -> list[int]:
    """Returns the available sizes for a specific map and mode."""
    return AVAILABLE_MAPS.get(mode, {}).get(map_name, [])


def mode_label(mode: str) -> str:
    """Returns the human-readable name of a mode."""
    return MODE_LABELS.get(mode, mode)