# MapLoom - Quick Start Guide

**Project Location:** `/home/akoel/Projects/boat/general/Code/MapLoom`

---

## ⚡ 30-Second Quick Start

```bash
# Navigate to project
cd /home/akoel/Projects/boat/general/Code/MapLoom

# Activate virtual environment
source activate_venv.sh

# Install dependencies (one time only)
pip install -r requirements.txt

# Run the application
python src/main.py
```

That's it! 🚀

---

## 📖 First-Time Setup (5 minutes)

### 1. Open Terminal

```bash
cd /home/akoel/Projects/boat/general/Code/MapLoom
```

### 2. Activate Virtual Environment

```bash
source activate_venv.sh
```

**Expected output:**
```
================================================
Activating MapLoom Virtual Environment
================================================

✅ Virtual environment activated
Location: /home/akoel/Projects/boat/general/Code/MapLoom/venv
Python:   Python 3.x.x
Pip:      pip x.x.x from ...

Available commands:
  python src/main.py          - Run application
  pytest tests/                - Run tests
  python src/main.py --help   - Show help
  deactivate                   - Deactivate venv
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Expected output:**
```
Collecting PyQt5==5.15.7
...
Successfully installed PyQt5-5.15.7 PyQtWebEngine-5.15.7 Pillow-12.3.0 PyYAML-6.0.1 pytest-7.4.3 ...
```

### 4. Verify Installation

```bash
python -c "import PyQt5; import PIL; print('✅ All dependencies installed')"
```

**Expected output:**
```
✅ All dependencies installed
```

### 5. You're Ready!

The virtual environment and all dependencies are now ready. You only need to do this once per development machine.

---

## 🎯 Running the Application

### Basic Run

```bash
python src/main.py
```

This opens the MapLoom window with placeholder panels.

### Run with Debug Logging

```bash
python src/main.py --debug
```

This shows detailed logging to console and writes to `maploom.log`:

```bash
tail -f maploom.log  # Watch logs in real-time
```

### Run with Specific MBTiles File

```bash
python src/main.py --file /path/to/your/map.mbtiles
```

**Example:**
```bash
python src/main.py --file ~/Downloads/map.mbtiles
```

### Show Help

```bash
python src/main.py --help
```

---

## 🧪 Running Tests

### Run All Tests

```bash
pytest tests/
```

### Run Specific Test File

```bash
pytest tests/test_mbtiles_reader.py -v
```

### Run with Coverage

```bash
pytest tests/ --cov=src/
```

---

## 📁 Project Structure

```
MapLoom/
├── src/                    # Application source code
│   ├── main.py            # Entry point (run this!)
│   ├── core/              # Business logic (MBTiles, zoom generation)
│   ├── map/               # Map tile handling
│   └── gui/               # PyQt5 user interface
├── doc/                   # Documentation
├── tests/                 # Unit tests
├── config/                # Configuration
├── mbtiles/               # Sample MBTiles files
├── images/                # Application icons/assets
├── venv/                  # Python virtual environment (auto-created)
├── requirements.txt       # Python dependencies
├── activate_venv.sh       # Virtual environment activation script
└── README.md              # Full project documentation
```

---

## 📚 Documentation

- **[README.md](README.md)** - Project overview and architecture
- **[SETUP_SUMMARY.md](SETUP_SUMMARY.md)** - What was created and why
- **[doc/DOCUMENTATION_INDEX.md](doc/DOCUMENTATION_INDEX.md)** - Navigation guide to all docs

---

## 🔍 What Each File Does

| File | Purpose |
|------|---------|
| `src/main.py` | Application entry point, handles CLI arguments |
| `src/gui/main_window.py` | Main window with left/right panels |
| `requirements.txt` | Lists all Python dependencies |
| `activate_venv.sh` | Activates the virtual environment |
| `.gitignore` | Tells git what to ignore |
| `venv/` | Python virtual environment (auto-created) |

---

## 💡 Common Tasks

### I want to work on the code

1. Activate the virtual environment: `source activate_venv.sh`
2. Check out a task from `doc/TODO_LIST.md` (to be created)
3. Edit files in `src/`
4. Write tests in `tests/`
5. Run tests: `pytest tests/`

### I want to understand the architecture

1. Read [README.md](README.md) - 5 minutes
2. Read [SETUP_SUMMARY.md](SETUP_SUMMARY.md) - 5 minutes
3. Read `doc/ARCHITECTURE.md` (to be created) - 15 minutes

### I want to start fresh

1. Deactivate venv: `deactivate`
2. Delete venv: `rm -rf venv/`
3. Recreate venv: `python3 -m venv venv`
4. Activate: `source activate_venv.sh`
5. Install: `pip install -r requirements.txt`

### I want to add a new dependency

1. Install it: `pip install package-name`
2. Note the version: `pip show package-name`
3. Add to `requirements.txt`: `package-name==x.x.x` (with exact version!)

### I want to check my environment

```bash
# Which Python?
which python

# Which pip?
which pip

# What version?
python --version

# What packages installed?
pip list

# Any conflicts?
pip check
```

---

## ⚠️ Troubleshooting

### "ModuleNotFoundError: No module named 'PyQt5'"

**Solution:** Virtual environment not activated or dependencies not installed.

```bash
source activate_venv.sh
pip install -r requirements.txt
```

### "Permission denied" on activate_venv.sh

**Solution:** Make script executable.

```bash
chmod +x activate_venv.sh
```

### Application opens but shows placeholders

**Expected!** The application is still in development. You'll see:
- "Characteristics Panel (Left side) - To be implemented"
- "Map Panel (Right side) - To be implemented"

This is normal for the current Phase 1 structure.

### No logs appearing

**Solution:** Debug logging not enabled.

```bash
python src/main.py --debug
```

Logs go to:
- Console (terminal output)
- File: `maploom.log` in project root

### PyQt5 GUI issues on Linux

**Solution:** May need some system libraries.

```bash
# Ubuntu/Debian
sudo apt-get install python3-pyqt5 python3-pyqt5.qtwebengine

# Or just use our venv:
pip install -r requirements.txt
```

---

## ✅ Success Indicators

After following this guide, you should have:

- ✅ Virtual environment activated
- ✅ All dependencies installed
- ✅ Application runs: `python src/main.py`
- ✅ No import errors
- ✅ Can see a window with placeholder content
- ✅ Debug logging works: `python src/main.py --debug`

If all of these work, you're ready to start development! 🎉

---

## 🚀 Next Steps

1. **Understand the project:** Read [README.md](README.md)
2. **See what's ready:** Review [SETUP_SUMMARY.md](SETUP_SUMMARY.md)
3. **Plan development:** Read `doc/PROJECT_SPECIFICATION.md` (to be created)
4. **Get development tasks:** Check `doc/TODO_LIST.md` (to be created)
5. **Start coding:** Implement Phase 1 tasks

---

## 📞 Need Help?

1. **Environment issues?** → Check "Troubleshooting" section above
2. **Understand the code?** → Read [README.md](README.md)
3. **Don't know what to do?** → Read `doc/DOCUMENTATION_INDEX.md`
4. **Complex problem?** → Check `doc/HARD_PROBLEMS_AND_SOLUTIONS.md` (when it exists)

---

**Last Updated:** 2026-10-11  
**Project:** MapLoom - MBTiles Viewer and Zoom Level Generator  
**Status:** ✅ Ready for Development
