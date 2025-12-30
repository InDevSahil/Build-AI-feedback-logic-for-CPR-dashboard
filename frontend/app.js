// DOM Elements
const connStatus = document.getElementById('connection-status');
const valRate = document.getElementById('val-rate');
const valDepth = document.getElementById('val-depth');
const valRosc = document.getElementById('val-rosc');
const statusRate = document.getElementById('status-rate');
const statusDepth = document.getElementById('status-depth');
const barRate = document.getElementById('bar-rate');
const barDepth = document.getElementById('bar-depth');
const aiPath = document.getElementById('ai-circle-path');
const aiInsight = document.getElementById('ai-insight');
const eventLog = document.getElementById('event-log');
const aiChatBox = document.getElementById('ai-chat-box');
const poseFeedback = document.getElementById('pose-feedback');
const chestModel = document.getElementById('chest-model');

// Chart Setup
const ctx = document.getElementById('waveformChart').getContext('2d');
const waveformChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: Array(250).fill(''), // 250 points ~ 1 second at 250Hz, or window
        datasets: [{
            label: 'Force/Displacement',
            data: Array(250).fill(0),
            borderColor: '#3b82f6',
            borderWidth: 2,
            tension: 0.4, // Smooth curve
            pointRadius: 0,
            fill: true,
            backgroundColor: 'rgba(59, 130, 246, 0.1)'
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false, // Performance optimization for realtime
        scales: {
            x: { display: false },
            y: {
                display: true,
                min: -10,
                max: 80, // Adjust based on expected simulated amplitude
                grid: { color: 'rgba(255,255,255,0.05)' }
            }
        },
        plugins: {
            legend: { display: false }
        }
    }
});

// WebSocket Setup
const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
const wsUrl = `${protocol}://127.0.0.1:8000/ws/simulation`;
let ws = null;

function connect() {
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        connStatus.classList.add('connected');
        connStatus.innerHTML = '<span class="dot"></span> Live Connected';
        log("Connected to CPR feedback stream.");
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        updateDashboard(data);
    };

    ws.onclose = () => {
        connStatus.classList.remove('connected');
        connStatus.innerHTML = '<span class="dot"></span> Disconnected';
        log("Connection lost. Reconnecting in 3s...", "error");
        setTimeout(connect, 3000);
    };

    ws.onerror = (err) => {
        console.error(err);
    };
}

// Update Logic
// We'll store a rolling buffer for chart to avoid jittery full redraws if possible, 
// but Chart.js standard update is fine for 10hz updates.
const MAX_POINTS = 500; // 2 seconds of history

function updateDashboard(packet) {
    const { waveform, metrics, rosc_prediction } = packet;

    // 1. Update Chart
    // waveform is an array of new points
    const currentData = waveformChart.data.datasets[0].data;

    // Add new points
    for (let pt of waveform) {
        currentData.push(pt);
    }

    // Remove old points to keep window size
    while (currentData.length > MAX_POINTS) {
        currentData.shift();
    }

    // Update labels (dummy)
    while (waveformChart.data.labels.length < currentData.length) {
        waveformChart.data.labels.push('');
    }
    while (waveformChart.data.labels.length > currentData.length) {
        waveformChart.data.labels.pop();
    }

    waveformChart.update();

    // 2. Update Metrics
    if (metrics && metrics.rate_cpm !== undefined) {
        // Rate
        valRate.innerText = metrics.rate_cpm.toFixed(0);
        statusRate.innerText = metrics.rate_status;
        statusRate.className = `metric-status status-${getStatusClass(metrics.rate_status)}`;

        // Bar (limit 0 to 200 for scale)
        let ratePct = (metrics.rate_cpm / 200) * 100;
        barRate.style.width = `${Math.min(ratePct, 100)}%`;
        barRate.style.backgroundColor = getStatusColor(metrics.rate_status);

        // Depth
        valDepth.innerText = metrics.avg_depth.toFixed(1);
        statusDepth.innerText = metrics.depth_status;
        statusDepth.className = `metric-status status-${getStatusClass(metrics.depth_status)}`;

        // Bar (limit 0 to 100 for scale)
        let depthPct = (metrics.avg_depth / 100) * 100;
        barDepth.style.width = `${Math.min(depthPct, 100)}%`;
        barDepth.style.backgroundColor = getStatusColor(metrics.depth_status);
    }

    // 3. Update AI ROSC
    if (rosc_prediction !== undefined) {
        valRosc.innerText = `${rosc_prediction.toFixed(0)}%`;
        // Dasharray: value, 100
        aiPath.setAttribute('stroke-dasharray', `${rosc_prediction}, 100`);

        // Color based on prob
        if (rosc_prediction > 75) {
            aiPath.style.stroke = '#10b981'; // Green
            aiInsight.innerText = "High ROSC Probability. Keep going!";
        } else if (rosc_prediction > 40) {
            aiPath.style.stroke = '#f59e0b'; // Orange
            aiInsight.innerText = "Moderate Probability. Improve consistency.";
        } else {
            aiPath.style.stroke = '#ef4444'; // Red
            aiInsight.innerText = "Low Probability. Check compressions.";
        }
    }

    // 4. Update Gemini Feedback
    if (packet.ai_feedback && packet.ai_feedback !== "") {
        addAiMessage(packet.ai_feedback);
    }

    // 5. Update AR/Vision
    if (packet.vision) {
        poseFeedback.innerText = packet.vision.posture_feedback;
        if (packet.vision.elbow_angle < 160) {
            poseFeedback.style.color = '#ef4444';
            poseFeedback.style.borderColor = '#ef4444';
        } else {
            poseFeedback.style.color = '#10b981';
            poseFeedback.style.borderColor = '#10b981';
        }
    }

    // 6. Animate Chest Model (Visual Feedback)
    // If recent depth > 10, compress the model
    if (metrics && metrics.avg_depth > 10) {
        // Simple toggle for visual effect based on buffer or just activity
        // Ideally sync with waveform peak, but for now just pulse if active
        if (metrics.rate_cpm > 50) {
            chestModel.classList.add('compressing');
            setTimeout(() => chestModel.classList.remove('compressing'), 150); // fast recoil
        }
    }
}

function addAiMessage(msg) {
    // Avoid duplicates if same as last message
    const lastMsg = aiChatBox.lastElementChild;
    if (lastMsg && lastMsg.innerText === msg) return;

    const div = document.createElement('div');
    div.className = 'ai-message';
    div.innerText = msg;
    aiChatBox.appendChild(div);
    aiChatBox.scrollTop = aiChatBox.scrollHeight;
}


function getStatusClass(statusText) {
    if (statusText === 'Good') return 'good';
    if (statusText.includes('Push') || statusText.includes('Too')) return 'bad'; // Simplify
    return 'warn';
}

function getStatusColor(statusText) {
    if (statusText === 'Good') return '#10b981';
    return '#ef4444';
}

function log(msg, type = 'info') {
    const div = document.createElement('div');
    div.className = `log-item log-${type}`;
    div.innerText = `[${new Date().toLocaleTimeString()}] ${msg}`;
    eventLog.prepend(div);
}

// Start
connect();
