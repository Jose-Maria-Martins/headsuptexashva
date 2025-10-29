# Poker AI UI - MVP

Simple web-based UI for the Heads-Up Poker research project.

## Features

- **Bot vs Bot**: Watch AI bots compete against each other
- **Human vs Bot**: Play against the AI (coming soon in full implementation)
- **Visual Game State**: See stacks, wins, and match progress
- **Multiple Difficulty Levels**: V0 (Easy), V1 (Medium), V2 (Hard)

## Setup

1. Ensure you're in the virtual environment:
   ```bash
   venv\Scripts\activate
   ```

2. Install Flask (if not already installed):
   ```bash
   pip install flask
   ```

3. Run the UI:
   ```bash
   cd ui
   python app.py
   ```

4. Open your browser to: `http://localhost:5000`

## Usage

### Bot vs Bot Mode

1. Select the bots to compete
2. Choose number of hands (50-500)
3. Click "Start Match"
4. Watch the match progress in real-time
5. View final results

### Play Against AI Mode

1. Choose difficulty level (V0/V1/V2)
2. Game starts automatically
3. (Full implementation pending)

## Architecture

- **Flask Backend**: `app.py` handles API requests and game logic
- **HTML Templates**: `templates/` directory for pages
- **Static Files**: `static/css/` and `static/js/` for styling and interactivity
- **Integration**: Uses existing C++ engine and Python bots

## API Endpoints

- `GET /` - Main menu
- `GET /bot-vs-bot` - Bot vs Bot page
- `GET /play` - Human vs Bot page
- `POST /api/bot-vs-bot/start` - Start bot match
- `GET /api/bot-vs-bot/next` - Get next hand state
- `POST /api/play/start` - Start human match

## Future Enhancements

- Full card visualization
- Betting action animations
- Player action history
- Match replay functionality
- Statistics dashboard
- Sound effects



