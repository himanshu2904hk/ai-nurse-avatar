// ╔══════════════════════════════════════════════════════════════════════════╗
// ║                           LOGGING                                        ║
// ║                                                                          ║
// ║   Handles the debug log panel on the right side.                         ║
// ╚══════════════════════════════════════════════════════════════════════════╝

const panel = document.getElementById('log-panel');

export function log(message, type = 'info') {
    const div = document.createElement('div');
    div.className = type;
    div.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    panel.appendChild(div);
    panel.scrollTop = panel.scrollHeight;
    console.log(`[${type.toUpperCase()}]`, message);
}
