import asyncio
import random
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger

from core.config import ServerConfig, MaplistConfig
from core.events import bus

try:
    from rconnet.rconbf2142 import Default
except ImportError:
    Default = None

# --- Mock Data for Testing ---
MOCK_NAMES = ["Player1", "Player2", "Player3", "Admin", "Sniper", "Medic"]
MOCK_TEAMS = ["EU", "PAC"]
MOCK_MAPS = [
    {"id": 0, "name": "minsk", "mode": "gpm_cq", "size": 32},
    {"id": 1, "name": "fall_of_berlin", "mode": "gpm_cq", "size": 64},
]

# --- Settings Schema (Defines valid types for the UI) ---
SETTINGS_SCHEMA = {
    "serverName": ("server_name", "str"),
    "password": ("password", "str"),
    "maxPlayers": ("max_players", "int"),
    "internet": ("internet", "bool"),
    "punkBuster": ("punk_buster", "bool"),
    "welcomeMessage": ("welcome_message", "str"),
    "serverPort": ("server_port", "int"),
    "bandwidthChoke": ("bandwidth_choke", "int"),
    "ticketRatio": ("ticket_ratio", "int"),
    "roundsPerMap": ("rounds_per_map", "int"),
    "timeLimit": ("time_limit", "int"),
    "scoreLimit": ("score_limit", "int"),
    "soldierFriendlyFire": ("soldier_friendly_fire", "int"),
    "vehicleFriendlyFire": ("vehicle_friendly_Fire", "int"),
    "soldierSplashFriendlyFire": ("soldier_splash_friendly_fire", "int"),
    "vehicleSplashFriendlyFire": ("vehicle_splash_friendly_fire", "int"),
    "tkPunishEnabled": ("tk_punish_enabled", "bool"),
    "tkNumPunishToKick": ("tk_num_punish_to_kick", "int"),
    "tkPunishByDefault": ("tk_punish_by_default", "bool"),
    "votingEnabled": ("voting_enabled", "bool"),
    "voteTime": ("vote_time", "int"),
    "minPlayersForVoting": ("min_players_for_voting", "int"),
    "autoBalanceTeam": ("auto_balance_team", "bool"),
    "teamRatioPercent": ("team_ratio_percent", "int"),
    "allowFreeCam": ("allow_free_cam", "bool"),
    "allowExternalViews": ("allow_external_views", "bool"),
    "allowNoseCam": ("allow_nose_cam", "bool"),
    "hitIndicator": ("hit_indicator", "bool"),
    "allowSpectators": ("allow_spectators", "bool"),
    "allowTitanMovement": ("allow_titan_movement", "bool"),
    "numPlayersNeededToStart": ("num_players_needed_to_start", "int"),
    "notEnoughPlayersRestartDelay": ("not_enough_players_restart_delay", "int"),
    "startDelay": ("start_delay", "int"),
    "endDelay": ("end_delay", "int"),
    "spawnTime": ("spawn_time", "int"),
    "manDownTime": ("man_down_time", "int"),
    "endOfRoundDelay": ("end_round_delay", "int"),
    "timeBeforeRestartMap": ("time_before_restart_map", "int"),
    "voipEnabled": ("voip_enabled", "bool"),
    "voipQuality": ("voip_quality", "int"),
    "voipServerRemote": ("voip_server_remote", "bool"),
    "voipServerRemoteIP": ("voip_server_remote_IP", "str"),
    "voipServerPort": ("voip_server_port", "int"),
    "voipBFClientPort": ("voip_BF_client_port", "int"),
    "voipBFServerPort": ("voip_BF_server_Port", "int"),
    "useGlobalRank": ("use_global_rank", "bool"),
    "useGlobalUnlocks": ("use_global_unlocks", "bool"),
    "minUnlockLevel": ("min_unlock_level", "int"),
    "maxUnlockLevel": ("max_unlock_level", "int"),
    "maxRank": ("max_rank", "int"),
    "botSkill": ("bot_skill", "str"),
    "autoRecord": ("auto_record", "bool"),
    "demoIndexURL": ("demo_index_URL", "str"),
    "demoDownloadURL": ("demo_download_URL", "str"),
    "autoDemoHook": ("auto_demo_hook", "str"),
    "demoQuality": ("demo_Quality", "int"),
    "gameSpyPort": ("game_spy_port", "int"),
    "allowNATNegotiation": ("allow_NAT_Negotiation", "bool"),
    "interfaceIP": ("interface_IP", "str"),
    "sponsorText": ("sponsor_text", "str"),
    "sponsorLogoURL": ("sponsor_logo_url", "str"),
    "communityLogoURL": ("community_logo_url", "str"),
    "customMapURL": ("custom_map_url", "str"),
    "radioSpamInterval": ("radio_spam_interval", "int"),
    "radioMaxSpamFlagCount": ("radio_max_spam_flag_count", "int"),
    "radioBlockedDurationTime": ("radio_blocked_duration_time", "int"),
    "adminScript": ("admin_script", "str"),
}

SETTINGS_GROUPS = [
    ("Basic", [
        "serverName", "password", "maxPlayers", "internet", "punkBuster",
        "welcomeMessage", "serverPort", "bandwidthChoke",
    ]),
    ("Gameplay", [
        "ticketRatio", "roundsPerMap", "timeLimit", "scoreLimit",
        "soldierFriendlyFire", "vehicleFriendlyFire",
        "soldierSplashFriendlyFire", "vehicleSplashFriendlyFire",
        "tkPunishEnabled", "tkNumPunishToKick", "tkPunishByDefault",
        "votingEnabled", "voteTime", "minPlayersForVoting",
        "autoBalanceTeam", "teamRatioPercent", "allowFreeCam",
        "allowExternalViews", "allowNoseCam", "hitIndicator",
        "allowSpectators", "allowTitanMovement",
    ]),
    ("Timing", [
        "numPlayersNeededToStart", "notEnoughPlayersRestartDelay",
        "startDelay", "endDelay", "spawnTime", "manDownTime",
        "endOfRoundDelay", "timeBeforeRestartMap",
    ]),
    ("VoIP", [
        "voipEnabled", "voipQuality", "voipServerRemote",
        "voipServerRemoteIP", "voipServerPort", "voipBFClientPort",
        "voipBFServerPort",
    ]),
    ("Rank & Unlocks", [
        "useGlobalRank", "useGlobalUnlocks", "minUnlockLevel",
        "maxUnlockLevel", "maxRank", "botSkill",
    ]),
    ("Demo & Misc", [
        "autoRecord", "demoIndexURL", "demoDownloadURL", "autoDemoHook",
        "demoQuality", "gameSpyPort", "allowNATNegotiation", "interfaceIP",
        "sponsorText", "sponsorLogoURL", "communityLogoURL", "customMapURL",
        "radioSpamInterval", "radioMaxSpamFlagCount",
        "radioBlockedDurationTime", "adminScript",
    ]),
]


class RconManager:
    def __init__(self, cfg: ServerConfig, maplist_cfg: MaplistConfig = None):
        self.cfg = cfg
        self.maplist_cfg = maplist_cfg or MaplistConfig()
        
        self.rcon = None
        self.connected = False
        
        self._mock_maplist = list(MOCK_MAPS)
        self._mock_settings = {k: self._mock_default(t) for k, (_, t) in SETTINGS_SCHEMA.items()}
        
        self._last_maplist = []
        self._last_settings = {}

    def _mock_default(self, kind: str):
        if kind == "bool": return False
        if kind == "int": return 0
        return ""

    def _mock_players(self) -> list[dict]:
        count = random.randint(2, 6)
        names = random.sample(MOCK_NAMES, count)
        return [
            {
                "id": i + 1,
                "name": name,
                "score": random.randint(0, 2000),
                "ping": random.randint(15, 150),
                "team": random.choice(MOCK_TEAMS),
                "ip": f"192.168.1.{random.randint(2, 254)}",
                "port": "",
            } for i, name in enumerate(names)
        ]

    # -------------------------------------------------------------------------
    # CONNECTION MANAGEMENT
    # -------------------------------------------------------------------------

    async def connect(self) -> bool:
        """Establishes a connection to the RCON server."""
        if self.cfg.mock:
            self.connected = True
            logger.info("[MOCK] RCON connected")
            await bus.emit("rcon.connected")
            return True

        if Default is None:
            logger.error("rconnet library is not installed.")
            return False

        try:
            loop = asyncio.get_event_loop()
            self.rcon = await loop.run_in_executor(
                None, lambda: Default(self.cfg.host, self.cfg.rcon_password)
            )
            
            started = await loop.run_in_executor(None, lambda: self.rcon.start())
            if not started:
                logger.error("RCON start() returned False. Check password or server status.")
                self.connected = False
                return False

            self.connected = True
            logger.info(f"RCON connected to {self.cfg.host}:{self.cfg.rcon_port}")
            await bus.emit("rcon.connected")
            return True
        except Exception as e:
            logger.error(f"RCON connection failed: {e}")
            self.connected = False
            return False

    async def _exec(self, func, *args):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func, *args)

    async def _exec_timeout(self, func, timeout=5.0):
        """Executes a function with a strict timeout to prevent UI freezes."""
        loop = asyncio.get_event_loop()
        try:
            return await asyncio.wait_for(
                loop.run_in_executor(None, func),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            logger.warning(f"RCON command timed out after {timeout}s")
            return None
        except Exception as e:
            logger.debug(f"RCON exec error: {e}")
            return None

    # -------------------------------------------------------------------------
    # PLAYER MANAGEMENT
    # -------------------------------------------------------------------------

    async def get_players(self) -> list[dict]:
        if self.cfg.mock:
            return self._mock_players()
        if not self.connected:
            return []

        try:
            raw = await self._exec_timeout(lambda: self.rcon.players, timeout=5.0)
            if not raw:
                return []

            players = []
            items = raw.items() if isinstance(raw, dict) else enumerate(raw)

            for pid, p in items:
                nick = getattr(p, "nick", "") or ""
                player_id = pid
                obj_id = getattr(p, "id", None)
                if obj_id is not None and obj_id != 0:
                    player_id = obj_id

                players.append({
                    "id": player_id,
                    "name": nick.strip() or "?",
                    "ip": (getattr(p, "address", "") or "").strip(),
                    "port": (getattr(p, "port", "") or "").strip(),
                    "key": getattr(p, "key", "") or "",
                    "score": 0,
                    "ping": 0,
                    "team": "",
                })
            return players
        except Exception as e:
            logger.warning(f"Failed to get players: {e}")
            return []

    async def kick(self, player_id: int, name: str = ""):
        if self.cfg.mock:
            logger.info(f"[MOCK] Kicked player {player_id} ({name})")
            await bus.emit("admin.action", {"action": "kick", "target": name or player_id})
            return

        try:
            def do_kick():
                raw = self.rcon.players
                if not raw: return False
                for pid, p in raw.items():
                    if pid == player_id or getattr(p, "id", None) == player_id:
                        p.kick()
                        return True
                return False

            ok = await self._exec_timeout(do_kick, timeout=5.0)
            if ok:
                logger.info(f"Kicked player {player_id}")
                await bus.emit("admin.action", {"action": "kick", "target": name or player_id})
            else:
                logger.debug(f"Kick failed: player {player_id} not found.")
        except Exception as e:
            logger.error(f"Kick error: {e}")

    async def ban(self, player_id: int, timeout: int = 0, name: str = "", reason: str = "Manual", admin: str = "Admin"):
        if self.cfg.mock:
            logger.info(f"[MOCK] Banned player {player_id} ({name})")
            await bus.emit("admin.action", {"action": "ban", "target": name or player_id})
            return

        try:
            def do_ban():
                raw = self.rcon.players
                if not raw: return None
                for pid, p in raw.items():
                    if pid == player_id or getattr(p, "id", None) == player_id:
                        ip = (getattr(p, "address", "") or "").strip()
                        p.ban()
                        return ip
                return None

            ip = await self._exec_timeout(do_ban, timeout=5.0)
            if not ip:
                logger.debug(f"Ban failed: player {player_id} not found.")
                return

            try:
                from core import ban_notes
                ban_notes.add_ban(ip=ip, player=name, reason=reason, admin=admin, timeout_min=timeout)
            except Exception as e:
                logger.warning(f"Could not save ban to local file: {e}")

            logger.info(f"Banned player {player_id} (IP: {ip})")
            await bus.emit("admin.action", {"action": "ban", "target": name or player_id})
        except Exception as e:
            logger.error(f"Ban error: {e}")

    # -------------------------------------------------------------------------
    # MAPLIST MANAGEMENT
    # -------------------------------------------------------------------------

    async def get_maplist(self) -> list[dict]:
        if self.cfg.mock:
            return self._mock_maplist
        if not self.connected:
            return []

        try:
            raw = await self._exec_timeout(lambda: self.rcon.maplist.list, timeout=5.0)
            if not raw:
                return getattr(self, "_last_maplist", [])

            result = []
            items = raw.items() if isinstance(raw, dict) else enumerate(raw)
            
            for idx, m in items:
                name = getattr(m, "name", None)
                mode = getattr(m, "gpm", None)
                size = getattr(m, "size", None)
                if name and mode:
                    result.append({
                        "id": idx,
                        "name": str(name),
                        "mode": str(mode),
                        "size": int(size) if size is not None else 64,
                    })
            
            if result:
                self._last_maplist = result
            return result
        except Exception as e:
            logger.warning(f"Failed to get maplist: {e}")
            return getattr(self, "_last_maplist", [])

    async def _wake_maplist(self):
        try:
            await self._exec_timeout(lambda: self.rcon.maplist.list, timeout=3.0)
        except Exception:
            pass
        await asyncio.sleep(0.3)

    async def change_map_now(self, map_id: int):
        if self.cfg.mock:
            await bus.emit("admin.action", {"action": "change_now", "target": map_id})
            return

        try:
            await self._wake_maplist()

            def do_change():
                raw = self.rcon.maplist.list
                if not raw: return False
                m = raw.get(map_id)
                if m is None: return False
                m.set_next()
                return True

            ok = await self._exec_timeout(do_change, timeout=10.0)
            if ok:
                await asyncio.sleep(0.2)
                await self._exec_timeout(lambda: self.rcon.run_next_level(), timeout=10.0)
                await bus.emit("admin.action", {"action": "change_now", "target": map_id})
            else:
                logger.error(f"Change map failed: ID {map_id} not found.")
        except Exception as e:
            logger.error(f"Change map error: {e}")

    async def remove_map(self, map_id: int):
        if self.cfg.mock:
            self._mock_maplist = [m for m in self._mock_maplist if m["id"] != map_id]
            for i, m in enumerate(self._mock_maplist): m["id"] = i
            return

        try:
            await self._wake_maplist()
            await self._exec_timeout(lambda: self.rcon.maplist.remove(map_id), timeout=10.0)
            await bus.emit("admin.action", {"action": "remove_map", "target": map_id})
        except Exception as e:
            logger.error(f"Remove map error: {e}")

    async def clear_maplist(self):
        if self.cfg.mock:
            self._mock_maplist = []
            return
        try:
            await self._exec_timeout(lambda: self.rcon.maplist.clear(), timeout=10.0)
        except Exception as e:
            logger.error(f"Clear maplist error: {e}")

    async def append_map(self, name: str, mode: str = "gpm_cq", size: int = 64):
        if self.cfg.mock:
            new_id = len(self._mock_maplist)
            self._mock_maplist.append({"id": new_id, "name": name, "mode": mode, "size": size})
            return
        try:
            await self._exec_timeout(lambda: self.rcon.maplist.append(name, mode, size), timeout=10.0)
        except Exception as e:
            logger.error(f"Append map error: {e}")

    async def save_maplist_to_file(self) -> bool:
        maps = await self.get_maplist()
        if not maps: return False
        
        path = Path(self.maplist_cfg.path)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            lines = ["mapList.clear"]
            for m in maps:
                lines.append(f"mapList.append {m['name']} {m['mode']} {m['size']}")
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            await bus.emit("maplist.saved", {"path": str(path), "count": len(maps)})
            return True
        except Exception as e:
            logger.error(f"Save maplist to file failed: {e}")
            return False

    # -------------------------------------------------------------------------
    # SERVER SETTINGS MANAGEMENT
    # -------------------------------------------------------------------------

    async def get_settings(self, only_keys: list[str] = None) -> dict:
        if self.cfg.mock:
            keys = only_keys or self._mock_settings.keys()
            return {k: self._mock_settings.get(k) for k in keys}
        
        if not self.connected:
            return {}

        keys_to_read = only_keys or list(SETTINGS_SCHEMA.keys())
        result = {}

        for key in keys_to_read:
            if key not in SETTINGS_SCHEMA: continue
            attr, kind = SETTINGS_SCHEMA[key]
            
            try:
                method = getattr(self.rcon.settings, attr, None)
                if method is None: continue

                val = None
                for _ in range(2):
                    val = await self._exec_timeout(method, timeout=3.0)
                    if val not in (None, "", "0: Map"): break
                    await asyncio.sleep(0.05)

                if val is None or val == "":
                    result[key] = self._last_settings.get(key)
                elif kind == "int":
                    result[key] = int(val)
                elif kind == "bool":
                    result[key] = str(val).strip().lower() in ("1", "true", "on", "yes")
                else:
                    result[key] = str(val)

                await asyncio.sleep(0.05)
            except Exception as e:
                logger.debug(f"Read setting '{key}' failed: {e}")
                result[key] = None

        for k, v in result.items():
            if v is not None: self._last_settings[k] = v
            
        return result

    async def set_setting(self, key: str, value) -> bool:
        if self.cfg.mock:
            self._mock_settings[key] = value
            await bus.emit("admin.action", {"action": "setting", "target": key})
            return True

        if not self.connected or key not in SETTINGS_SCHEMA:
            return False

        attr, kind = SETTINGS_SCHEMA[key]
        if kind == "str":
            logger.warning(f"Cannot write string setting '{key}' via RCON.")
            return False

        try:
            method = getattr(self.rcon.settings, attr, None)
            if method is None: return False

            send_val = int(value) if kind == "int" else (1 if bool(value) else 0)
            
            loop = asyncio.get_event_loop()
            await asyncio.wait_for(
                loop.run_in_executor(None, lambda: method(send_val)),
                timeout=5.0,
            )
            await bus.emit("admin.action", {"action": "setting", "target": key})
            return True
        except asyncio.TimeoutError:
            logger.error(f"Timeout applying setting '{key}'.")
            return False
        except Exception as e:
            logger.error(f"Failed to apply setting '{key}': {e}")
            return False

    # -------------------------------------------------------------------------
    # MISC & LOOPS
    # -------------------------------------------------------------------------

    async def say(self, message: str, target: str = "all"):
        if self.cfg.mock:
            logger.info(f"[MOCK] Broadcast: {message}")
            return
        try:
            await self._exec_timeout(lambda: self.rcon.say(message), timeout=5.0)
        except Exception as e:
            logger.error(f"Broadcast failed: {e}")

    async def monitoring_loop(self, refresh_sec: int):
        while True:
            if not self.connected:
                ok = await self.connect()
                if not ok:
                    await asyncio.sleep(10)
                    continue
            
            players = await self.get_players()
            await bus.emit("players.updated", players)
            await asyncio.sleep(refresh_sec)

    async def broadcast_loop(self, cfg):
        if not cfg.enabled or not cfg.messages:
            return
            
        while not self.connected:
            await asyncio.sleep(2)
            
        idx = 0
        while True:
            await asyncio.sleep(cfg.interval_sec)
            if not self.connected: continue
            
            msg = cfg.messages[idx % len(cfg.messages)]
            await self.say(msg)
            await bus.emit("broadcast.sent", {"message": msg})
            idx += 1