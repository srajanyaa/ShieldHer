# shieldHer Windows Run Guide (Agent-Friendly)

This document is a deterministic setup and run guide for Windows.
It is written so a human or automation agent can execute it step by step.

## 1) Project Overview

- UI: `app.py` (Python + Tkinter)
- Core logic: `analyzer.c` (compiled C executable)
- Data: `data/` folder
- Runtime integration:
  - Python writes input file
  - C analyzer reads input and writes output/history/SOS
  - Python displays analysis

## 2) Required Software (Windows)

Install these first:

1. Python 3.10+ (3.11/3.12 also fine)
2. GCC for Windows (MinGW-w64)

### Verify installations (PowerShell)

```powershell
python --version
gcc --version
```

Expected: both commands print versions and do not fail.

If `gcc` is not found, install MinGW-w64 and add its `bin` folder to `PATH`.

## 3) Folder Assumptions

Assume project root is:

```text
C:\path\to\shieldher
```

The following files should exist:

- `app.py`
- `analyzer.c`
- `data\contacts.txt`
- `data\safe_places.txt`

## 4) Quick Start (One Click)

Double-click `run_windows.bat` in the project root. It will:

1. Detect Python (via `python` or the `py` launcher)
2. Build `analyzer.exe` from `analyzer.c` with `gcc`
3. Verify tkinter is available
4. Syntax-check `app.py`
5. Launch the app

## 5) Manual Build C Analyzer on Windows

From project root:

```powershell
gcc -Wall -Wextra -std=c99 -o analyzer.exe analyzer.c
```

Expected result:

- `analyzer.exe` is created in project root.

## 6) Python Sanity Check

```powershell
python -m py_compile app.py
```

Expected result:

- Command exits silently (no error output).

## 7) Run the App

Either double-click `run_windows.bat` or run manually:

```powershell
python app.py
```

Expected runtime flow:

1. Auth window opens (Login / Sign Up)
2. Sign up or log in
3. Safety UI opens
4. Fill questions and run analysis
5. Results + advice are shown

## 8) First-Time Signup Flow

On Sign Up tab, provide:

- Username
- Password
- Full Name
- Phone
- 3 trusted contacts (name + phone)

Expected after signup:

- Account stored in `data\users.json`
- User directory created at `data\users\<username>\`
- Per-user files used at runtime:
  - `input.txt`
  - `output.txt`
  - `history.csv`
  - `contacts.txt`
  - `safe_places.txt`
  - `sos_draft.txt`

## 9) Timer Behavior (Current)

- UI slider: 10 seconds to 10 minutes
- Input file includes:
  - `TIMER_SECONDS` (primary)
  - `TIMER_MINUTES` (fallback)
- C scoring uses `TIMER_SECONDS` if present, otherwise falls back to `TIMER_MINUTES`.

## 10) Non-Interactive Analyzer Smoke Tests (Optional)

Use this to verify C logic without launching GUI.

### Test A: 30 seconds timer input

```powershell
@"
Q_ISOLATED=0
Q_POOR_LIGHTING=0
Q_LATE_NIGHT=0
Q_FOLLOWED=0
Q_LOW_BATTERY=0
Q_CROWDED=0
CONFIDENCE=3
TIMER_SECONDS=30
TIMER_MINUTES=1
TIMER_EXPIRED=0
NOTES=windows smoke test
"@ | Set-Content data\input.txt

.\analyzer.exe -i data\input.txt -o data\output.txt -h data\history.csv -c data\contacts.txt -s data\sos_draft.txt
Get-Content data\output.txt
```

Expected key in output:

- `RISK_SCORE=15` (timer contribution for 10-59 sec)

## 11) Common Issues and Fixes

### Issue: `Analyzer not found` in app

Cause:

- `analyzer.exe` missing in project root.

Fix:

```powershell
gcc -Wall -Wextra -std=c99 -o analyzer.exe analyzer.c
```

### Issue: `gcc` command not found

Cause:

- MinGW-w64 not installed or not in `PATH`.

Fix:

- Install MinGW-w64
- Add `<mingw-install>\bin` to `PATH`
- Open a new terminal and run `gcc --version`

### Issue: Tkinter error / UI does not launch

Cause:

- Python installation missing Tk support (uncommon on official Windows installer).

Fix:

- Reinstall official Python from python.org and keep Tcl/Tk option enabled.

## 12) Agent Execution Checklist

Use this exact sequence:

1. Confirm tools: `python --version`, `gcc --version`
2. Build C: `gcc -Wall -Wextra -std=c99 -o analyzer.exe analyzer.c`
3. Validate Python: `python -m py_compile app.py`
4. Optional smoke test using `data\input.txt` + `.\analyzer.exe ...`
5. Launch app: `python app.py`
6. Confirm auth -> safety screen -> analysis output path works

Or simply run `run_windows.bat` from the project root and skip steps 2-5.

## 13) Notes

- No external Python packages are required.
- This project uses local file-based storage (no DB).
- Passwords are hashed with SHA-256 + salt for basic internship-level local auth.
