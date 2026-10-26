from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger

# Bans are stored in a simple text file. Easy to read, edit, and backup.
DATA_DIR = Path("data")
DATA_FILE = DATA_DIR / "ban_notes.txt"


def _ensure_file():
    """Creates the data directory and file if they don't exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        DATA_FILE.write_text("", encoding="utf-8")


def _read_lines() -> list[str]:
    _ensure_file()
    try:
        return DATA_FILE.read_text(encoding="utf-8").splitlines()
    except Exception as e:
        logger.error(f"Failed to read ban file: {e}")
        return []


def _write_lines(lines: list[str]):
    _ensure_file()
    try:
        content = "\n".join(lines) + "\n" if lines else ""
        DATA_FILE.write_text(content, encoding="utf-8")
    except Exception as e:
        logger.error(f"Failed to write ban file: {e}")


def add_ban(ip: str, player: str = "", reason: str = "Manual", admin: str = "Admin", timeout_min: int = 0):
    """Adds a new ban record to the text file."""
    created = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    if timeout_min and timeout_min > 0:
        expires = (datetime.now() + timedelta(minutes=timeout_min)).strftime("%Y-%m-%d %H:%M")
    else:
        expires = "never"

    lines = _read_lines()
    # Remove any existing record for this IP to avoid duplicates
    lines = [l for l in lines if not l.startswith(ip + " |")]

    new_line = f"{ip} | {player or '-'} | {reason or 'Manual'} | {admin or 'Admin'} | {created} | {expires}"
    lines.append(new_line)
    
    _write_lines(lines)
    logger.info(f"BAN ADDED: {ip} ({player}) - {reason}")


def get_bans() -> list[dict]:
    """Parses the text file into a list of dictionaries for the UI."""
    result = []
    for i, line in enumerate(_read_lines()):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        
        parts = [p.strip() for p in line.split("|")]
        while len(parts) < 6:
            parts.append("")
            
        result.append({
            "id": i + 1,
            "ip": parts[0],
            "player": parts[1],
            "reason": parts[2],
            "admin": parts[3],
            "created_at": parts[4],
            "expires_at": parts[5] or "never",
            "expired": _is_expired(parts[5]),
        })
    return result


def remove_ban(ip: str):
    """Removes a ban record by IP."""
    lines = _read_lines()
    lines = [l for l in lines if not l.startswith(ip + " |")]
    _write_lines(lines)
    logger.info(f"BAN REMOVED: {ip}")


def clear_bans():
    """Clears the entire ban list."""
    _write_lines([])
    logger.info("ALL BANS CLEARED")


def find_by_nick(nick: str) -> list[dict]:
    """Search ban records by player nickname."""
    nick_lower = (nick or "").lower()
    return [b for b in get_bans() if nick_lower in (b.get("player", "") or "").lower()]


def _is_expired(expires: str) -> bool:
    """Checks if a ban has expired."""
    if not expires or expires == "never":
        return False
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(expires, fmt)
            return dt < datetime.now()
        except ValueError:
            continue
    return False