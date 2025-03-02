# Copy-Paste Guide for Setting Up the Project

Follow these steps to set up your Blender Multi-Channel Export Pipeline project:

## 1. Create and run the setup script

1. Create a file named `setup_project.sh` and paste the shell script into it
2. Make it executable: `chmod +x setup_project.sh`
3. Run it: `./setup_project.sh`

## 2. Copy the code into each file

Use the list below to copy the appropriate code into each file:

### Main addon files

| File | Description |
|------|-------------|
| `addon/__init__.py` | Main addon registration code |
| `addon/operators/setup.py` | Pipeline setup operator |
| `addon/operators/render.py` | Rendering operators and scene switcher |
| `addon/panels/export_panel.py` | UI panel for the addon |

### Server files

| File | Description |
|------|-------------|
| `server/process_queue.py` | Server-side batch processing script |

### Other files

| File | Description |
|------|-------------|
| `build.py` | Script to build distributable ZIP |
| `tests/test_load_addon.py` | Basic test for loading the addon |
| `.github/workflows/test.yml` | GitHub Actions workflow |
| `README.md` | Project documentation |
| `LICENSE` | License file |
| `.gitignore` | Git ignore file |
| `Setup Instructions.md` | Instructions for setting up the repo |

## 3. Initialize Git repository

```bash
cd blender-multi-channel-export
git init
git add .
git commit -m "Initial project setup"
```

## 4. Link to Blender for development

### On macOS:

```bash
ln -s "$(pwd)/addon" ~/Library/Application\ Support/Blender/3.6/scripts/addons/multi_channel_export
```

### On Windows:

```bash
mklink /D "%APPDATA%\Blender Foundation\Blender\3.6\scripts\addons\multi_channel_export" "%CD%\addon"
```

### On Linux:

```bash
ln -s "$(pwd)/addon" ~/.config/blender/3.6/scripts/addons/multi_channel_export
```

## 5. Test in Blender

1. Open Blender
2. Go to Edit → Preferences → Add-ons
3. Search for "Multi-Channel Export"
4. Enable the addon

The error should now be fixed and the addon should work properly!