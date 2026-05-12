# Desktop-Groups — Claude Guidance

## Project Overview

A personal Python automation project built for learning. It watches for games launching on Windows, then automatically applies a "profile" — changing the Wallpaper Engine wallpaper, switching the audio output device, and adjusting Govee smart lights.

## Directory Structure

```
Desktop-Groups/
├── configs/           # JSON config files (game_list.json, profiles.json, govee_devices.json, govee_scenes.json)
├── src/
│   ├── game_presets/  # Main watcher script (game_presets.py)
│   └── resources/     # Shared helper modules (govee_lights.py, profiles.py, change_wallpaper.py, desktop_groups.py)
├── venv/              # Python virtual environment (root-level)
└── .env               # API keys (ignored)
```

## What to Ignore
- `Archive/` — old/legacy code
- `.env` — secrets file
- Any folder named `test` or similar testing directories
- `venv/` and `src/game_presets/venv/` — virtual environment files

## Collaboration Style

This is a **beginner learning project**. The primary goal when assisting is to **teach concepts, not write code for the user**. Unless explicitly asked to implement something:

- Explain *what* needs to change and *why*
- Point to the specific file and line(s) involved
- Describe the concept (e.g., relative vs absolute paths, imports, etc.)
- Let the user write the fix themselves

Only handle tedious/mechanical tasks directly (e.g., creating config files, scaffolding boilerplate the user already understands).

## Key Technical Notes

- Python files use `sys.path.insert(0, parent_dir)` to enable cross-folder imports within `src/`
- JSON config files live in `configs/` — any hardcoded or relative paths pointing elsewhere are a common bug after restructuring
- The project uses a root-level `venv/` — packages like `wmi`, `pycaw`, `python-dotenv`, and `requests` must be installed there
- `game_presets.py` runs an infinite loop watching for Windows process creation events via WMI
