from pathlib import Path
import yaml
from pydantic import BaseModel


class ServerConfig(BaseModel):
    host: str
    rcon_port: int
    rcon_password: str
    name: str = "BF2142 Server"
    mock: bool = False


class MonitoringConfig(BaseModel):
    player_refresh_sec: int = 3
    connection_retry_sec: int = 10


class ProcessConfig(BaseModel):
    enabled: bool = False
    exe_path: str = ""
    work_dir: str = ""
    args: list[str] = []
    check_interval_sec: int = 10
    restart_delay_sec: int = 15
    max_restarts_per_hour: int = 5
    stdout_log: str = "logs/bf2142_stdout.log"


class MaplistConfig(BaseModel):
    path: str = "mods/bf2142/settings/maplist.con"
    auto_save: bool = False


class BroadcastConfig(BaseModel):
    enabled: bool = False
    interval_sec: int = 300
    messages: list[str] = []


class LoggingConfig(BaseModel):
    level: str = "INFO"
    file: str = "logs/tanto.log"


class AppConfig(BaseModel):
    server: ServerConfig
    monitoring: MonitoringConfig
    process: ProcessConfig = ProcessConfig()
    maplist: MaplistConfig = MaplistConfig()
    broadcast: BroadcastConfig = BroadcastConfig()
    logging: LoggingConfig


def load_config(path: str = "config.yaml") -> AppConfig:
    """
    Loads and parses the YAML configuration file.
    Raises a clear error if the file is missing (instead of a cryptic crash).
    """
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(
            f"Config file not found at '{path}'. "
            f"Please copy 'config.example.yaml' to 'config.yaml' and fill it in."
        )
        
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    return AppConfig(**raw)