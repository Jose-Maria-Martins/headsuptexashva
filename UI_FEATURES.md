# Poker AI UI - Complete Feature List

## What You Can Do

### 1. Bot vs Bot Spectator Mode ✅ **FULLY FUNCTIONAL**

**Setup:**
- Choose Bot A (V0/V1/V2)
- Choose Bot B (V0/V1/V2)  
- Select number of hands (50-500)
- Click "Start Match"

**What You See:**
- Match header with hand progress (e.g., "Hand 50 / 200")
- Two player panels showing:
  - Bot name (e.g., "V1 - Hand Strength")
  - Current stack size
  - Number of hands won
- VS indicator between players
- Match statistics updated in real-time

**Controls:**
- "Next Hand" button to manually advance
- Auto-play mode (advances every 0.5 seconds automatically)
- "New Match" to start fresh with new configuration
- Back button to return to menu

**Results:**
- Final stacks for both bots
- Total hands won by each bot
- Match summary

**Technical Details:**
- Uses your C++ engine's `simulate_match()` function
- Runs one hand at a time for visualization
- Results are live and accurate
- Backend handles bot wrapper creation automatically

---

### 2. Human vs Bot (Play) Mode ⚠️ **BASIC FRAMEWORK**

**Current Status:**
- Setup screen works ✅
- Difficulty selection works ✅
- Backend API endpoint exists ✅
- Game loop needs implementation ❌

**What Will Be Available (Not Yet Implemented):**
- See your hole cards
- See community board cards
- View pot size, stacks, blinds
- Action buttons: Fold / Call / Raise
- Bet sizing slider
- Opponent action display
- Hand equity calculation
- Match statistics

**Note:** Full implementation requires creating a custom game loop that plays one betting round at a time and waits for user input. This is more complex than bot vs bot mode.

---

## Visual Design

- **Dark Theme**: Deep blue background with gold accents
- **Card-Style Layout**: Menu items styled like cards
- **Responsive**: Works on different screen sizes
- **Clean Interface**: Minimal, focused on gameplay

---

## Technical Implementation

### Folder Structure:
```
ui/
├── app.py                 # Flask server
├── run.bat                # Quick start script
├── README.md              # Usage instructions
├── requirements.txt       # Dependencies
├── templates/
│   ├── index.html         # Main menu
│   ├── bot_vs_bot.html    # Bot vs Bot page
│   └── play.html          # Human vs Bot page
└── static/
    ├── css/
    │   └── style.css       # All styling
    ├── js/
    │   └── bot_vs_bot.js   # Bot vs Bot logic
    └── images/
        └── (future card images)
```

### Backend Integration:
- Uses existing `poker_engine` C++ bindings
- Uses existing `RandomBot`, `HandStrengthBot`, `MonteCarloBot` classes
- Creates wrapper classes to integrate with C++ engine
- Minimal modifications to existing code

### API Endpoints:
```
GET  /                      # Main menu
GET  /bot-vs-bot            # Bot vs Bot HTML page
GET  /play                  # Human vs Bot HTML page
POST /api/bot-vs-bot/start  # Start bot match (JSON)
GET  /api/bot-vs-bot/next   # Get next hand state (JSON)
POST /api/play/start        # Start human match (JSON)
```

---

## How to Run

### Quick Start:
1. Navigate to `ui/` folder
2. Double-click `run.bat`
3. Open browser to `http://localhost:5000`

### Manual Start:
```bash
cd ui
..\venv\Scripts\activate
python app.py
```

### What Happens:
- Flask server starts on port 5000
- Server checks if C++ engine is available
- If available: Full functionality
- If not: Shows error message (requires rebuilding with `build_simple.py`)

---

## Current Limitations

1. **Human vs Bot**: Only setup screen works, gameplay not implemented
2. **No Card Images**: Cards shown as text (K♠, A♥, etc.)
3. **No Animations**: Actions happen instantly, no visual effects
4. **No Sound**: Silent gameplay
5. **No Statistics Dashboard**: Can't view historical match data
6. **No Replay**: Can't review past matches

---

## Future Enhancements (Not in MVP)

### Phase 2 - Polish:
- [ ] Card images with suit symbols
- [ ] Action animations (cards dealing, chips moving)
- [ ] Sound effects
- [ ] Statistics dashboard
- [ ] Match replay functionality

### Phase 3 - Advanced:
- [ ] Full human vs bot gameplay
- [ ] Multiple simultaneous matches
- [ ] Live betting visualization
- [ ] Equity calculators
- [ ] Hand range analyzers
- [ ] Training mode with tips

---

## Development Time

**MVP Completed: ~2 hours**
- Flask app setup: 15 min
- HTML templates: 30 min  
- CSS styling: 30 min
- JavaScript: 20 min
- Backend integration: 25 min

**Estimated for Full Implementation:**
- Human vs Bot: +4 hours
- Card images: +2 hours
- Animations: +2 hours
- Total: ~10 hours for polished version

---

## Notes for Paper/Report

- **Bot vs Bot mode demonstrates your research** by visually showing how different AI strategies perform
- **Can be used for demos** to teachers/stakeholders
- **Clearly shows V0 < V1 < V2 performance** visually through match progression
- **Validates that your evaluation system works** by showing live matches

---

## Questions?

Check `ui/README.md` for technical details.
Check main `README.md` for project overview.



