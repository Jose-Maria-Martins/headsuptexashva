// Bot vs Bot JavaScript

let currentMatch = null;
let isPaused = false;

// Bot name mapping
const botNames = {
    'v0': 'V0 - Random',
    'random': 'V0 - Random',
    'v1': 'V1 - Hand Strength',
    'handstrength': 'V1 - Hand Strength',
    'v2': 'V2 - Monte Carlo',
    'montecarlo': 'V2 - Monte Carlo',
    'v3': 'V3 - Experimental CFR',
    'mccfr': 'V3 - Experimental CFR'
};

function startMatch() {
    const botA = document.getElementById('botA').value;
    const botB = document.getElementById('botB').value;
    const hands = parseInt(document.getElementById('hands').value);
    
    // Update display
    document.getElementById('setup-screen').style.display = 'none';
    document.getElementById('game-screen').style.display = 'block';
    
    // Set bot names
    document.getElementById('player0-name').textContent = botNames[botA] || 'Bot A';
    document.getElementById('player1-name').textContent = botNames[botB] || 'Bot B';
    document.getElementById('bot-a-label').textContent = botNames[botA] || 'Bot A';
    document.getElementById('bot-b-label').textContent = botNames[botB] || 'Bot B';
    
    // Start match via API
    fetch('/api/bot-vs-bot/start', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            botA: botA,
            botB: botB,
            hands: hands
        })
    })
    .then(r => r.json())
    .then(data => {
        if (data.status === 'started' || data.status === 'completed') {
            document.getElementById('total-hands').textContent = data.hands;
            // Load first update
            nextHand();
        }
    })
    .catch(err => {
        console.error('Error starting match:', err);
        alert('Failed to start match. Make sure the engine is available.');
    });
}

function nextHand() {
    if (isPaused) return;
    
    fetch('/api/bot-vs-bot/next')
    .then(r => r.json())
    .then(data => {
        // Update progress
        const progress = (data.hand / data.total_hands) * 100;
        document.getElementById('progress-fill').style.width = progress + '%';
        
        // Update display
        document.getElementById('current-hand').textContent = data.hand;
        document.getElementById('total-hands').textContent = data.total_hands;
        document.getElementById('player0-stack').textContent = data.p0_stack;
        document.getElementById('player1-stack').textContent = data.p1_stack;
        document.getElementById('player0-wins').textContent = data.p0_wins;
        document.getElementById('player1-wins').textContent = data.p1_wins;
        
        // Calculate win rates (hands won out of total hands played)
        const totalHandsPlayed = data.hand; // Use actual hand count, not just wins
        const p0WinRate = totalHandsPlayed > 0 ? ((data.p0_wins / totalHandsPlayed) * 100).toFixed(1) : 0;
        const p1WinRate = totalHandsPlayed > 0 ? ((data.p1_wins / totalHandsPlayed) * 100).toFixed(1) : 0;
        document.getElementById('player0-winrate').textContent = p0WinRate + '%';
        document.getElementById('player1-winrate').textContent = p1WinRate + '%';
        
        // Pot display removed for accuracy
        
        if (data.finished) {
            // Show results
            showResults(data);
        } else {
            // Auto-advance to show progression
            setTimeout(nextHand, 100);
        }
    })
    .catch(err => {
        console.error('Error loading next hand:', err);
        alert('Error loading match data: ' + err.message);
    });
}

function showResults(data) {
    document.getElementById('results').style.display = 'block';
    document.getElementById('progress-fill').style.width = '100%';
    
    // Determine winner
    const winnerName = data.p0_stack > data.p1_stack ? 
        document.getElementById('player0-name').textContent : 
        document.getElementById('player1-name').textContent;
    
    document.getElementById('winner-name').textContent = winnerName;
    document.getElementById('final-stacks').textContent = 
        `Player 1: ${data.p0_stack} | Player 2: ${data.p1_stack}`;
    document.getElementById('total-hands-played').textContent = 
        `${data.hand} hands`;
    
    // Disable next button
    const button = document.querySelector('.controls button');
    if (button && button.textContent === 'Next Hand') {
        button.disabled = true;
    }
}

function togglePause() {
    isPaused = !isPaused;
    const btn = document.getElementById('pause-btn');
    btn.textContent = isPaused ? 'Resume' : 'Pause';
    
    if (!isPaused) {
        nextHand();
    }
}
