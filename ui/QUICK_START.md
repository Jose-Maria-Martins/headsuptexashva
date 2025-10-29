# UI Quick Start

## ✅ Bot vs Bot Mode is Working!

The issue with `simulate_match()` has been fixed. The UI now properly runs bot matches and displays results.

## How to Run:

1. Navigate to the `ui/` folder
2. Double-click `run.bat`
3. Wait for Flask to start
4. Open browser to: **http://localhost:5000**
5. Click "Bot vs Bot"
6. Configure your match and click "Start Match"

## What You'll See:

- Match runs immediately (runs full match in backend)
- Progressive display shows final results quickly
- Final stacks and win counts displayed
- Winner announcement

## Current Behavior:

- **Full match runs at once** (not hand-by-hand due to C++ engine design)
- **Progressive display** simulates showing progress
- **Final results** are accurate and complete

## Try These Matchups:

- **V0 vs V0**: Should be 50/50 (~1000 vs ~1000 stacks)
- **V1 vs V0**: V1 should dominate (~80%+ win rate)
- **V2 vs V0**: V2 should crush V0 (~95%+ win rate)
- **V2 vs V1**: V2 should win (~80%+ win rate)

## Troubleshooting:

**Error: "Engine not available"**
- Run `python build_simple.py` from the root directory
- Or use: `venv\Scripts\python.exe build_simple.py`

**Port already in use:**
- Change port in `app.py` line 172: `app.run(debug=True, host='0.0.0.0', port=5001)`

## Next Steps:

- [ ] Add card visualization
- [ ] Implement human vs bot gameplay
- [ ] Add statistics dashboard
- [ ] Add match replay

## For Your Paper:

This UI demonstrates your research visually and can be used for presentations/demos!



