TANTO Control Deck (TCD)

A modern, stable, web-based RCON panel for Battlefield 2142 servers.
Built with Python, NiceGUI, and rconnet. Designed to replace outdated tools like 2142CC.

## What is this?
TANTO Control Deck is a web-based control panel for your Battlefield 2142 dedicated server.
Instead of typing RCON commands in a black console, you open a browser and click buttons:
kick players, ban cheaters, change maps, read logs, and tweak server settings.

## Features
- **Live Players**: Kick and Ban with a reason (saved to a local file).

- **Maplist**: Instant map change (CHANGE NOW), remove maps, and save list.

- **Settings**: Read and write server variables (int/bool) via RCON.

- **Console**: Direct RCON commands and broadcast messages.

- **Log**: Live event feed (kicks, bans, messages).

- **Process Manager (TPM)**: Auto-restarts your server if it crashes (optional).

## IMPORTANT WARNINGS
- Console Timeout: If you leave the panel open for a long time without activity, RCON connections may go stale. Restart the panel (or refresh F5) if commands hang.

- Unstable Settings: Do not set `sv.maxUnlockLevel` higher than 5 on vanilla servers. It will crash the server.

- Security: This panel does not have built-in authentication. Do not expose it to the open internet without a reverse proxy (Nginx) and a password.

- Settings Limitations: Not all server settings can be changed in real-time via RCON.

- Int & Bool settings (like `sv.ticketRatio`, `sv.maxPlayers`) usually apply instantly.

- String settings (like `sv.serverName`, `sv.welcomeMessage`) are read-only in this panel. To change them, you must edit serversettings.con on the server and restart the server.

- Some settings (like `sv.serverPort`) may require a full server restart to take effect. If the UI says "skipped", it means the RCON protocol rejected the change.

## Installation
## Requirements
Windows (or Linux) with Python 3.12+.

A running BF2142 dedicated server.

RCON enabled in your serversettings.con (`sv.rconPassword` "your_password").

## Steps
Install **Python 3.12+**.

Clone the repo: git clone https://github.com/TONDO96IT/tanto-control-deck.git

Install dependencies:
pip install -r requirements.txt

Copy `config.example.yaml` to `config.yaml` and fill in your server details.

Mock Mode: If you just want to test the UI without connecting to a real server, set mock: true in your config.yaml. This will load fake players and maps so you can see how the panel works.

Run: `python main.py`

Open http://localhost:8080

## How to fill config.yaml
After copying config.example.yaml to config.yaml, you must set these values:

host: IP address of your game server (e.g., 127.0.0.1 if local, or 109.x.x.x if VPS).

rcon_port: Usually 4711.

rcon_password: The password from your serversettings.con.

mock: Set to false for a real server, true for UI testing.

If you leave CHANGE_ME, the panel will start but will show RCON: Offline.

## TPM (Process Manager)
If you want TCD to auto-restart your game server, check the tpm/ folder.
Copy tantopm.py to your server PC, configure the paths inside, and run it in the background.
It uses psutil to watch the process and subprocess to restart it.

## License
This project is licensed under the MIT License - see the LICENSE file for details.
