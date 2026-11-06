// Real-Time Dashboard Client for SG90 Servo Condition Monitoring System

let isRecording = false;
const MAX_POINTS = 60;

// Data histories for canvas charting
const historyData = {
  voltage: [],
  current: [],
  accelX: [],
  accelY: [],
  accelZ: [],
  sound: [],
  angle: []
};

// Canvas elements and contexts
const canvases = {
  elec: { el: document.getElementById('chart-electrical'), ctx: null },
  vib:  { el: document.getElementById('chart-vibration'), ctx: null },
  snd:  { el: document.getElementById('chart-acoustic'), ctx: null },
  ang:  { el: document.getElementById('chart-angle'), ctx: null }
};

// Initialize contexts
for (const k in canvases) {
  if (canvases[k].el) {
    canvases[k].ctx = canvases[k].el.getContext('2d');
    canvases[k].el.width = canvases[k].el.clientWidth;
    canvases[k].el.height = canvases[k].el.clientHeight;
  }
}

// -------------------------------------------------------------
// Telemetry Polling Loop (10 Hz)
// -------------------------------------------------------------
async function updateTelemetry() {
  try {
    const res = await fetch('/api/sensors/latest');
    if (!res.ok) return;
    const data = await res.json();
    const tel = data.telemetry;
    const pred = data.prediction || {};
    const connected = data.connected;

    // 1. Connection Pill
    const pill = document.getElementById('pill-arduino');
    if (connected) {
      pill.className = 'pill pill-green';
      pill.innerText = '● Arduino Connected';
    } else {
      pill.className = 'pill pill-red';
      pill.innerText = '● Arduino Disconnected';
    }

    // 2. Metrics Cards
    document.getElementById('val-angle').innerText = (tel.servo_angle !== undefined ? tel.servo_angle : 90) + '°';
    document.getElementById('val-voltage').innerText = (tel.voltage_v || 0).toFixed(2) + ' V';
    document.getElementById('val-current').innerText = (tel.current_a || 0).toFixed(3) + ' A';
    document.getElementById('val-accel').innerText = `(${tel.accel_x || 0}, ${tel.accel_y || 0}, ${tel.accel_z || 0})`;
    document.getElementById('val-sound').innerText = `${(tel.sound_rms || 0).toFixed(1)} / ${tel.sound_p2p || 0}`;

    // 3. Anomaly Banner
    const banner = document.getElementById('anomaly-banner');
    const statusText = document.getElementById('anomaly-status-text');
    const driversText = document.getElementById('anomaly-drivers');
    const scoreVal = document.getElementById('anomaly-score-val');
    const scoreBar = document.getElementById('anomaly-score-bar');

    const score = (tel.current_a !== undefined && tel.current_a > 0.200) ? 0.95 : (pred.anomaly_score || 0.0);
    const isAnomaly = (tel.current_a !== undefined && tel.current_a > 0.200) || (pred.is_anomaly || false);

    scoreVal.innerText = score.toFixed(2);
    scoreBar.style.width = Math.min(100, Math.max(0, score * 100)) + '%';

    if (isAnomaly) {
      banner.className = 'anomaly-banner banner-anomaly';
      statusText.innerText = 'ANOMALY DETECTED';
      statusText.style.color = 'var(--accent-red)';
      scoreBar.style.backgroundColor = 'var(--accent-red)';
      if (tel.current_a !== undefined && tel.current_a > 0.200) {
        driversText.innerText = `Current threshold exceeded: ${tel.current_a.toFixed(3)} A > 0.200 A`;
      } else if (pred.contributing_features && pred.contributing_features.length > 0) {
        driversText.innerText = 'Contributing drivers: ' + pred.contributing_features.map(f => `${f[0]} (z=${f[1]})`).join(', ');
      } else {
        driversText.innerText = 'Multivariate anomaly score exceeds baseline safety envelope';
      }
    } else {
      banner.className = 'anomaly-banner banner-normal';
      statusText.innerText = 'NORMAL OPERATION';
      statusText.style.color = 'var(--accent-green)';
      scoreBar.style.backgroundColor = 'var(--accent-green)';
      driversText.innerText = 'Current <= 0.200 A & all multivariate sensor parameters within normal baseline';
    }

    // 4. Update Rolling History
    pushHistory(historyData.voltage, tel.voltage_v || 0);
    pushHistory(historyData.current, tel.current_a || 0);
    pushHistory(historyData.accelX, tel.accel_x || 350);
    pushHistory(historyData.accelY, tel.accel_y || 350);
    pushHistory(historyData.accelZ, tel.accel_z || 350);
    pushHistory(historyData.sound, tel.sound_p2p || 0);
    pushHistory(historyData.angle, tel.servo_angle || 90);

    // 5. Redraw Canvas Charts
    drawCharts();

  } catch (err) {
    // Silently continue polling
  }
}

function pushHistory(arr, val) {
  arr.push(val);
  if (arr.length > MAX_POINTS) arr.shift();
}

// -------------------------------------------------------------
// Canvas Waveform Renderers
// -------------------------------------------------------------
function drawCharts() {
  // Chart 1: Electrical (Voltage & Current)
  drawLines(canvases.elec, [
    { data: historyData.voltage, color: '#58a6ff', min: 0, max: 6 },
    { data: historyData.current, color: '#d29922', min: 0, max: 1.0 }
  ]);

  // Chart 2: Vibration (X, Y, Z Acceleration)
  drawLines(canvases.vib, [
    { data: historyData.accelX, color: '#f85149', min: 100, max: 600 },
    { data: historyData.accelY, color: '#3fb950', min: 100, max: 600 },
    { data: historyData.accelZ, color: '#58a6ff', min: 100, max: 600 }
  ]);

  // Chart 3: Acoustic Amplitude
  drawLines(canvases.snd, [
    { data: historyData.sound, color: '#bc8cff', min: 0, max: 200 }
  ]);

  // Chart 4: Servo Angle
  drawLines(canvases.ang, [
    { data: historyData.angle, color: '#39d353', min: 0, max: 180 }
  ]);
}

function drawLines(chartObj, seriesList) {
  const ctx = chartObj.ctx;
  if (!ctx) return;
  const w = chartObj.el.width;
  const h = chartObj.el.height;

  ctx.clearRect(0, 0, w, h);

  // Subtle grid lines
  ctx.strokeStyle = '#1b222c';
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(0, h * 0.25); ctx.lineTo(w, h * 0.25);
  ctx.moveTo(0, h * 0.50); ctx.lineTo(w, h * 0.50);
  ctx.moveTo(0, h * 0.75); ctx.lineTo(w, h * 0.75);
  ctx.stroke();

  for (const s of seriesList) {
    const arr = s.data;
    if (arr.length < 2) continue;

    ctx.strokeStyle = s.color;
    ctx.lineWidth = 2;
    ctx.beginPath();

    const range = (s.max - s.min) || 1;
    const step = w / (MAX_POINTS - 1);

    for (let i = 0; i < arr.length; i++) {
      const x = i * step;
      const normalized = Math.min(1, Math.max(0, (arr[i] - s.min) / range));
      const y = h - (normalized * (h - 10) + 5);

      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
  }
}

// -------------------------------------------------------------
// Anomaly Alerts Polling Loop (1 Hz)
// -------------------------------------------------------------
async function updateAlerts() {
  try {
    const res = await fetch('/api/anomalies');
    if (!res.ok) return;
    const alerts = await res.json();

    const container = document.getElementById('alert-list');
    document.getElementById('alert-count').innerText = `${alerts.length} Events`;

    if (!alerts || alerts.length === 0) {
      container.innerHTML = '<div style="color: var(--text-muted); padding: 0.5rem;">No active alerts. System healthy.</div>';
      return;
    }

    container.innerHTML = alerts.slice(0, 15).map(a => {
      const timeStr = a.timestamp.substring(11, 19);
      return `
        <div class="alert-item alert-${a.severity}">
          <div>
            <strong>[${a.severity}]</strong> ${a.message}
          </div>
          <div style="color: var(--text-muted);">${timeStr}</div>
        </div>
      `;
    }).join('');

  } catch (e) {}
}

// -------------------------------------------------------------
// Dataset Recording Controls
// -------------------------------------------------------------
async function toggleRecording() {
  const btn = document.getElementById('btn-record');
  const statusEl = document.getElementById('recording-status');
  const nameInput = document.getElementById('session-name');
  const modeInput = document.getElementById('session-mode');

  if (!isRecording) {
    const sessionName = nameInput.value.trim() || 'session_01';
    const mode = modeInput.value;

    const res = await fetch('/api/recording/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_name: sessionName, mode: mode })
    });
    const data = await res.json();

    isRecording = true;
    btn.className = 'btn btn-stop';
    btn.innerText = 'Stop Recording';
    statusEl.innerText = `Recording Active: ${data.session_id}`;
    statusEl.style.color = 'var(--accent-green)';
  } else {
    const res = await fetch('/api/recording/stop', { method: 'POST' });
    const data = await res.json();

    isRecording = false;
    btn.className = 'btn btn-start';
    btn.innerText = 'Start Recording';
    statusEl.innerText = `Saved: ${data.records_saved} records to session ${data.session_id}`;
    statusEl.style.color = 'var(--text-muted)';
  }
}

// Window resize handler for canvas
window.addEventListener('resize', () => {
  for (const k in canvases) {
    if (canvases[k].el) {
      canvases[k].el.width = canvases[k].el.clientWidth;
      canvases[k].el.height = canvases[k].el.clientHeight;
    }
  }
});

// Start update intervals
setInterval(updateTelemetry, 100);  // 10 Hz telemetry
setInterval(updateAlerts, 1500);     // 1.5s alerts poll
updateTelemetry();
updateAlerts();
