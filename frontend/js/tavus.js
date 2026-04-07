// ╔══════════════════════════════════════════════════════════════════════════╗
// ║                      TAVUS EVENT HANDLER                                 ║
// ║                                                                          ║
// ║   Handles all communication between the browser and Tavus via Daily.     ║
// ║                                                                          ║
// ║   Flow:                                                                  ║
// ║   1. prewarmBackend()       → test backend connection on page load       ║
// ║   2. attachEventHandlers()  → listen for Tavus events on Daily frame     ║
// ║   3. handleUtterance()      → display speech in chat panel               ║
// ║   4. handleToolCall()       → receive tool_call → execute → echo back    ║
// ║   5. executeToolCall()      → POST to backend API, return result         ║
// ║   6. sendEchoResponse()     → send spoken_response back to Tavus         ║
// ╚══════════════════════════════════════════════════════════════════════════╝

import { CONFIG } from './config.js';
import { log } from './logger.js';
import { addMessage } from './chat.js';


// ┌────────────────────────────────────────────────────────────────────────┐
// │  STEP 1: PRE-WARM BACKEND CONNECTION                                   │
// │                                                                        │
// │  Called on page load to wake up ngrok/backend.                         │
// └────────────────────────────────────────────────────────────────────────┘

export function prewarmBackend() {
    fetch(`${CONFIG.backendUrl}/api/health`).then(() => log('Backend connection pre-warmed', 'success'))
      .catch(() => log('Backend not reachable (will retry on tool call)', 'error'));
}


// ┌────────────────────────────────────────────────────────────────────────┐
// │  STEP 2: ATTACH EVENT HANDLERS TO DAILY FRAME                          │
// │                                                                        │
// │  Listens for app-message events and routes them:                       │
// │  - conversation.utterance  → handleUtterance()                         │
// │  - conversation.tool_call  → handleToolCall()                          │
// └────────────────────────────────────────────────────────────────────────┘

export function attachEventHandlers(frame) {
    // Connection lifecycle events
    frame.on('joined-meeting', () => log('Joined Daily room', 'success'));
    frame.on('left-meeting', () => log('Left Daily room'));
    frame.on('error', (e) => log(`Daily error: ${e.errorMsg}`, 'error'));
    frame.on('participant-joined', (e) => log(`Participant joined: ${e.participant.user_name || 'unknown'}`));

    // Main event router
    frame.on('app-message', async (event) => {
        log(`Received app-message: ${JSON.stringify(event.data)}`);
        const data = event.data;
        if (!data) return;

        if (data.event_type === 'conversation.utterance') {
            handleUtterance(data);
        }

        if (data.message_type === 'conversation' && data.event_type === 'conversation.tool_call') {
            await handleToolCall(frame, data);
        }
    });
}


// ┌────────────────────────────────────────────────────────────────────────┐
// │  STEP 3: HANDLE UTTERANCE                                              │
// │                                                                        │
// │  Display speech transcripts in the chat panel.                         │
// │  - replica speech → shown as "Ram"                                     │
// │  - user speech    → shown as "You (voice)"                             │
// └────────────────────────────────────────────────────────────────────────┘

function handleUtterance(data) {
    const role = data.properties?.role;
    const speech = data.properties?.speech;
    if (!speech) return;

    if (role === 'replica') {
        addMessage(speech, 'Ram');
    } else if (role === 'user') {
        addMessage(speech, 'user', false);
    }
}


// ┌────────────────────────────────────────────────────────────────────────┐
// │  STEP 4: HANDLE TOOL CALL                                              │
// │                                                                        │
// │  Tavus LLM decided to call a tool.                                     │
// │  Parse name + args → execute → send echo response.                     │
// └────────────────────────────────────────────────────────────────────────┘

async function handleToolCall(frame, data) {
    const toolName = data.properties?.name || data.properties?.tool_name;
    const argsStr = data.properties?.arguments || data.properties?.tool_arguments;

    log(`Tool call detected: ${toolName}`, 'tool');

    if (!toolName || !argsStr) {
        log('Missing tool name or arguments', 'error');
        return;
    }

    try {
        const args = JSON.parse(argsStr);
        const result = await executeToolCall(toolName, args);

        if (result.spoken_response) {
            sendEchoResponse(frame, data.conversation_id, result.spoken_response);
        }
    } catch (e) {
        log(`Failed to process tool call: ${e.message}`, 'error');
    }
}


// ┌────────────────────────────────────────────────────────────────────────┐
// │  STEP 5: EXECUTE TOOL CALL                                             │
// │                                                                        │
// │  POST to backend API: /api/tool/{toolName}                             │
// │  Returns the backend response (includes spoken_response).              │
// └────────────────────────────────────────────────────────────────────────┘

async function executeToolCall(toolName, args) {
    log(`TOOL CALL: ${toolName}(${JSON.stringify(args)})`, 'tool');

    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000);

        const response = await fetch(`${CONFIG.backendUrl}/api/tool/${toolName}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Connection': 'keep-alive'
            },
            body: JSON.stringify(args),
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const result = await response.json();
        log(`TOOL RESULT: ${JSON.stringify(result)}`, 'success');
        return result;

    } catch (error) {
        if (error.name === 'AbortError') {
            log(`TOOL TIMEOUT: ${toolName} took too long`, 'error');
            return { error: 'Request timed out' };
        }
        log(`TOOL ERROR: ${error.message}`, 'error');
        return { error: error.message };
    }
}


// ┌────────────────────────────────────────────────────────────────────────┐
// │  STEP 6: SEND ECHO RESPONSE                                            │
// │                                                                        │
// │  Sends spoken_response back to Tavus via conversation.echo.            │
// │  The avatar speaks this text exactly (bypasses LLM).                   │
// └────────────────────────────────────────────────────────────────────────┘

function sendEchoResponse(frame, conversationId, text) {
    frame.sendAppMessage({
        message_type: 'conversation',
        event_type: 'conversation.echo',
        conversation_id: conversationId,
        properties: { text }
    }, '*');

    log('Sent echo response to Tavus', 'success');
}
