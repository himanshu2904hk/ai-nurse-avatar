// ╔══════════════════════════════════════════════════════════════════════════╗
// ║                          CHAT PANEL                                      ║
// ║                                                                          ║
// ║   Handles chat message display, input, and send.                         ║
// ║   Typed messages are sent to Tavus via a callback.                       ║
// ╚══════════════════════════════════════════════════════════════════════════╝

import { log } from './logger.js';

const messagesEl = document.getElementById('chat-messages');
const inputEl = document.getElementById('chat-input');
const sendBtn = document.getElementById('btn-send');
const panelEl = document.getElementById('chat-panel');

// Called when user sends a typed message — set by main.js
let onSendMessage = null;

// Track recently typed messages to suppress voice echo duplicates
const recentTyped = [];

export function setOnSendMessage(callback) {
    onSendMessage = callback;
}

export function addMessage(text, role, isTyped = false) {
    // Skip voice echo of a recently typed message
    if (role === 'user' && !isTyped) {
        const normalized = text.trim().toLowerCase();
        const idx = recentTyped.indexOf(normalized);
        if (idx !== -1) {
            recentTyped.splice(idx, 1);
            return; // skip — this is the voice echo of a typed message
        }
    }

    const msgDiv = document.createElement('div');
    const typeClass = role === 'user' ? (isTyped ? 'typed' : 'spoken') : '';
    msgDiv.className = `chat-msg ${role === 'user' ? 'user' : 'Ram'} ${typeClass}`;

    const senderLabel = role === 'user' ? (isTyped ? 'You' : 'You (voice)') : 'Ram';
    msgDiv.innerHTML = `
        <span class="sender">${senderLabel}</span>
        <div class="bubble">${text}</div>
    `;

    // Animate in
    msgDiv.style.opacity = '0';
    msgDiv.style.transform = 'translateY(8px)';
    msgDiv.style.transition = 'opacity 0.25s ease, transform 0.25s ease';
    messagesEl.appendChild(msgDiv);

    requestAnimationFrame(() => {
        msgDiv.style.opacity = '1';
        msgDiv.style.transform = 'translateY(0)';
    });

    messagesEl.scrollTop = messagesEl.scrollHeight;
}

export function clear() {
    messagesEl.innerHTML = '';
    recentTyped.length = 0;
}

export function setEnabled(enabled) {
    inputEl.disabled = !enabled;
    sendBtn.disabled = !enabled;
    if (enabled) {
        panelEl.classList.remove('hidden');
    } else {
        panelEl.classList.add('hidden');
    }
}

function sendUserMessage() {
    const text = inputEl.value.trim();
    if (!text || !onSendMessage) return;

    // Track this so we can suppress the voice echo
    recentTyped.push(text.toLowerCase());
    // Clean up after 10 seconds
    setTimeout(() => {
        const idx = recentTyped.indexOf(text.toLowerCase());
        if (idx !== -1) recentTyped.splice(idx, 1);
    }, 10000);

    addMessage(text, 'user', true);
    inputEl.value = '';
    onSendMessage(text);
    log(`Chat sent: ${text}`, 'success');
}

// Event listeners
inputEl.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendUserMessage();
});
sendBtn.addEventListener('click', sendUserMessage);
