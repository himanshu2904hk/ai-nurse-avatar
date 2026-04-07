// ╔══════════════════════════════════════════════════════════════════════════╗
// ║                         MAIN ENTRY POINT                                 ║
// ║                                                                          ║
// ║   Wires all modules together:                                            ║
// ║   config → logger → chat → ui → daily → tavus                           ║
// ╚══════════════════════════════════════════════════════════════════════════╝

import { CONFIG } from './config.js';
import { log } from './logger.js';
import * as chat from './chat.js';
import * as ui from './ui.js';
import * as daily from './daily.js';
import { attachEventHandlers, prewarmBackend } from './tavus.js';

let currentConversationId = null;

// ┌────────────────────────────────────────────────────────────────────────┐
// │                      START CONVERSATION                                 │
// └────────────────────────────────────────────────────────────────────────┘

async function startConversation() {
    ui.showLoading();
    log('Creating Tavus conversation...');

    try {
        // 1. Create conversation via backend (no greeting yet — we send it after joining)
        const response = await fetch(`${CONFIG.backendUrl}/api/tool/create_conversation`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || `Failed to create conversation (${response.status})`);
        }
        const data = await response.json();
        log(`Conversation created: ${data.conversation_id}`, 'success');
        currentConversationId = data.conversation_id;

        // 2. Show video + chat UI
        ui.showVideo();
        chat.clear();
        chat.setEnabled(true);

        // 3. Create Daily frame and attach Tavus event handlers
        log('Creating Daily frame...');
        const frame = daily.createFrame(ui.getVideoContainer());
        attachEventHandlers(frame);

        // 4. Wire chat input → Tavus
        chat.setOnSendMessage((text) => {
            if (!frame || !currentConversationId) return;
            frame.sendAppMessage({
                message_type: 'conversation',
                event_type: 'conversation.respond',
                conversation_id: currentConversationId,
                properties: { text }
            }, '*');
        });

        // 5. Join the Daily room
        await daily.joinRoom(data.conversation_url);

        // 6. Wait for connection to stabilize, then send greeting
        setTimeout(() => {
            frame.sendAppMessage({
                message_type: 'conversation',
                event_type: 'conversation.echo',
                conversation_id: currentConversationId,
                properties: {
                    text: "    Hi there! Welcome to our clinic. I'm here to help you check in for your appointment. Have you visited us before?"
                }
            }, '*');
            log('Greeting sent after delay', 'success');
        }, 3000);

    } catch (error) {
        log(`Error: ${error.message}`, 'error');
        ui.showError(error.message);
    }
}

// ┌────────────────────────────────────────────────────────────────────────┐
// │                      STOP CONVERSATION                                  │
// └────────────────────────────────────────────────────────────────────────┘

async function stopConversation() {
    ui.showStopping();
    log('Stopping conversation... (triggered by: ' + new Error().stack.split('\n')[1].trim() + ')');

    try {
        await daily.leaveAndDestroy();

        if (currentConversationId) {
            await fetch(`${CONFIG.backendUrl}/api/tool/end_conversation/${currentConversationId}`, {
                method: 'POST'
            });
        }

        log('Conversation ended', 'success');
    } catch (e) {
        log(`End error (ignored): ${e.message}`, 'error');
    }

    chat.setEnabled(false);
    chat.clear();
    ui.resetToStart();
    currentConversationId = null;
}

// ┌────────────────────────────────────────────────────────────────────────┐
// │                        INITIALIZE                                       │
// └────────────────────────────────────────────────────────────────────────┘

document.getElementById('btn-start').addEventListener('click', startConversation);
document.getElementById('btn-stop').addEventListener('click', stopConversation);
prewarmBackend();
