# Architecture & Function Flow

## System Overview

```
Browser (Frontend)          Your Server (Backend)         External Services
┌─────────────────┐        ┌──────────────────┐         ┌──────────────┐
│  7 JS modules   │──HTTP──│  FastAPI + DB    │──HTTP──│  Tavus API   │
│  index.html     │        │  simple_tools.py │         │  Daily.co    │
└────────┬────────┘        └──────────────────┘         └──────────────┘
         │                                                      │
         └──────────── WebRTC (video/audio/messages) ───────────┘
```

---

## Module Map

```
frontend/
├── index.html          ← 3-column layout (debug | video | chat)
└── js/
    ├── config.js       ← Backend URL constant
    ├── logger.js       ← Debug panel logging
    ├── ui.js           ← Show/hide containers, buttons
    ├── chat.js         ← Chat messages, input, de-duplication
    ├── daily.js        ← Daily.co WebRTC iframe lifecycle
    ├── tavus.js        ← Tavus event routing + tool execution
    └── main.js         ← Entry point, wires everything together

backend/
├── app/
│   ├── main.py              ← FastAPI app, middleware, static files
│   └── api/
│       └── simple_tools.py  ← Tool endpoints + Tavus proxy
└── .env                     ← API keys, DB config
```

---

## Complete Function Reference

### config.js
| Export | Type | Description |
|--------|------|-------------|
| `CONFIG.backendUrl` | `string` | Base URL for backend API (`http://localhost:8000`) |

### logger.js
| Export | Signature | Called By | Description |
|--------|-----------|-----------|-------------|
| `log()` | `log(message, type='info')` | Every module | Appends timestamped message to `#log-panel` and `console.log` |

### ui.js
| Export | Signature | Called By | What It Does |
|--------|-----------|-----------|-------------|
| `showLoading()` | `showLoading()` | `main.js → startConversation()` | Replaces start button with "Creating conversation..." text |
| `showVideo()` | `showVideo()` | `main.js → startConversation()` | Shows `#video-container`, shows stop button, hides start container |
| `showStopping()` | `showStopping()` | `main.js → stopConversation()` | Changes stop button text to "Stopping..." |
| `resetToStart()` | `resetToStart()` | `main.js → stopConversation()` | Clears video, hides stop button, shows "Start New Conversation" |
| `showError()` | `showError(message)` | `main.js → startConversation() catch` | Shows error message with "Try Again" button |
| `getVideoContainer()` | `getVideoContainer()` | `main.js → startConversation()` | Returns `#video-container` DOM element for Daily iframe |

### chat.js
| Export | Signature | Called By | What It Does |
|--------|-----------|-----------|-------------|
| `setOnSendMessage()` | `setOnSendMessage(callback)` | `main.js → startConversation()` | Sets callback for when user types + sends a message |
| `addMessage()` | `addMessage(text, role, isTyped=false)` | `tavus.js → handleUtterance()`, `chat.js → sendUserMessage()` | Creates chat bubble with fade-in animation. Skips voice echoes of typed messages |
| `clear()` | `clear()` | `main.js → startConversation()`, `main.js → stopConversation()` | Empties chat messages |
| `setEnabled()` | `setEnabled(enabled)` | `main.js → startConversation()`, `main.js → stopConversation()` | Enables/disables chat input + shows/hides panel |

**Internal functions:**
| Function | Trigger | What It Does |
|----------|---------|-------------|
| `sendUserMessage()` | Enter key or Send button click | Adds typed message to chat, calls `onSendMessage` callback, tracks text for de-duplication |

### daily.js
| Export | Signature | Called By | What It Does |
|--------|-----------|-----------|-------------|
| `createFrame()` | `createFrame(videoContainer)` | `main.js → startConversation()` | Creates Daily.co iframe inside the video container |
| `joinRoom()` | `joinRoom(url)` | `main.js → startConversation()` | Joins the Daily WebRTC room using the conversation URL |
| `leaveAndDestroy()` | `leaveAndDestroy()` | `main.js → stopConversation()` | Leaves the room and destroys the iframe |
| `getFrame()` | `getFrame()` | (available but unused) | Returns current Daily call frame reference |

### tavus.js
| Export | Signature | Called By | What It Does |
|--------|-----------|-----------|-------------|
| `prewarmBackend()` | `prewarmBackend()` | `main.js` (on page load) | Pings `GET /api/health` to wake up backend |
| `attachEventHandlers()` | `attachEventHandlers(frame)` | `main.js → startConversation()` | Registers all Daily event listeners (see below) |

**Internal functions:**
| Function | Triggered By | What It Does |
|----------|-------------|-------------|
| `handleUtterance(data)` | `app-message` event where `event_type === 'conversation.utterance'` | Shows avatar speech as "Ram" or user speech as "You (voice)" in chat |
| `handleToolCall(frame, data)` | `app-message` event where `event_type === 'conversation.tool_call'` | Parses tool name + args → calls `executeToolCall()` → sends echo response |
| `executeToolCall(toolName, args)` | `handleToolCall()` | POSTs to `backend/api/tool/{toolName}` with args, returns result (10s timeout) |
| `sendEchoResponse(frame, conversationId, text)` | `handleToolCall()` (when result has `spoken_response`) | Sends `conversation.echo` via Daily so avatar speaks the text word-for-word |

### main.js (Entry Point)
| Export | Signature | Trigger | What It Does |
|--------|-----------|---------|-------------|
| (none — all internal) | | | |

**Internal functions:**
| Function | Trigger | What It Does |
|----------|---------|-------------|
| `startConversation()` | "Start Conversation" button click | Full startup sequence (see flow below) |
| `stopConversation()` | "Stop" button click | Full shutdown sequence (see flow below) |

---

## Flow 1: Page Load

```
Browser loads index.html
    │
    ├─→ <script type="module" src="js/main.js">
    │       │
    │       ├─→ import config, logger, chat, ui, daily, tavus
    │       │
    │       ├─→ btn-start.addEventListener('click', startConversation)
    │       ├─→ btn-stop.addEventListener('click', stopConversation)
    │       │
    │       └─→ prewarmBackend()                          [tavus.js]
    │               │
    │               └─→ fetch GET /api/health              [backend]
    │                       │
    │                       └─→ log("Backend pre-warmed")  [logger.js]
    │
    └─→ chat.js initializes input listeners (Enter key, Send button)
```

---

## Flow 2: Start Conversation (User clicks "Start Conversation")

```
startConversation()                                        [main.js:21]
    │
    ├─ 1. ui.showLoading()                                 [ui.js:13]
    │      └─→ Shows "Creating conversation..." text
    │
    ├─ 2. fetch POST /api/tool/create_conversation         [main.js:27]
    │      │
    │      └─→ Backend: create_conversation()              [simple_tools.py:331]
    │             │
    │             ├─→ httpx POST https://tavusapi.com/v2/conversations
    │             │      body: { persona_id: "pcdd3e30fb79" }
    │             │      header: x-api-key: <TAVUS_API_KEY>
    │             │
    │             └─→ Returns { conversation_id, conversation_url }
    │
    ├─ 3. ui.showVideo()                                   [ui.js:17]
    │      └─→ Shows video container, stop button; hides start
    │
    ├─ 4. chat.clear() + chat.setEnabled(true)             [chat.js:62,66]
    │      └─→ Clears messages, shows chat panel, enables input
    │
    ├─ 5. daily.createFrame(videoContainer)                [daily.js:11]
    │      └─→ DailyIframe.createFrame() — creates iframe in DOM
    │
    ├─ 6. attachEventHandlers(frame)                       [tavus.js:42]
    │      └─→ Registers listeners:
    │          ├─ 'joined-meeting'     → log
    │          ├─ 'left-meeting'       → log
    │          ├─ 'error'              → log
    │          ├─ 'participant-joined' → log
    │          └─ 'app-message'        → routes to:
    │              ├─ handleUtterance()  (if conversation.utterance)
    │              └─ handleToolCall()   (if conversation.tool_call)
    │
    ├─ 7. chat.setOnSendMessage(callback)                  [main.js:55]
    │      └─→ Wires typed chat → frame.sendAppMessage(conversation.respond)
    │
    ├─ 8. daily.joinRoom(conversation_url)                 [daily.js:27]
    │      └─→ callFrame.join({ url }) — WebRTC handshake with Daily servers
    │
    └─ 9. setTimeout(3000ms)                               [main.js:69]
           └─→ frame.sendAppMessage(conversation.echo)
                  text: "Hi there! Welcome to our clinic..."
                  └─→ Avatar speaks the greeting
```

---

## Flow 3: Conversation Loop (Repeats for entire session)

### 3a. User speaks into microphone
```
User speaks
    │
    └─→ Tavus hears via WebRTC (speech-to-text on their servers)
        │
        ├─→ Tavus AI (LLM) processes the speech
        │
        └─→ Tavus sends app-message(s) through Daily frame:
            │
            ├─ conversation.utterance (role: "user")
            │   └─→ handleUtterance()                      [tavus.js:74]
            │       └─→ addMessage(speech, 'user', false)   [chat.js:26]
            │           └─→ Chat shows: "You (voice): ..."
            │
            ├─ conversation.utterance (role: "replica")
            │   └─→ handleUtterance()                      [tavus.js:74]
            │       └─→ addMessage(speech, 'Ram')           [chat.js:26]
            │           └─→ Chat shows: "Ram: ..."
            │
            └─ (optional) conversation.tool_call
                └─→ See Flow 4 below
```

### 3b. User types a message
```
User types + hits Enter
    │
    └─→ sendUserMessage()                                  [chat.js:76]
        │
        ├─→ recentTyped.push(text)  ← tracks for de-duplication
        ├─→ addMessage(text, 'user', true)                 [chat.js:26]
        │       └─→ Chat shows: "You: ..."
        │
        └─→ onSendMessage(text)  ← callback set by main.js
            └─→ frame.sendAppMessage({                     [main.js:57]
                    event_type: 'conversation.respond',
                    properties: { text }
                })
                └─→ Tavus receives it as if user spoke it
                    └─→ Tavus sends back utterance (voice echo)
                        └─→ handleUtterance() called
                            └─→ addMessage() checks recentTyped
                                └─→ SKIPPED (duplicate suppressed)
```

---

## Flow 4: Tool Call (Tavus AI decides to use a tool)

```
Tavus AI decides: "I need to look up this patient"
    │
    └─→ Sends app-message: conversation.tool_call
        │   name: "lookup_patient"
        │   arguments: '{"phone": "555-1234"}'
        │
        └─→ handleToolCall(frame, data)                    [tavus.js:94]
            │
            ├─→ Parse toolName + args from JSON
            │
            ├─→ executeToolCall("lookup_patient", {phone})  [tavus.js:125]
            │       │
            │       └─→ fetch POST /api/tool/lookup_patient [backend]
            │              body: { phone: "555-1234" }
            │              │
            │              └─→ lookup_patient()             [simple_tools.py:127]
            │                     │
            │                     ├─→ Query PostgreSQL by phone
            │                     │
            │                     └─→ Returns:
            │                          { found: true,
            │                            spoken_response: "Hey John, welcome back!" }
            │
            └─→ sendEchoResponse(frame, id, text)          [tavus.js:171]
                    │
                    └─→ frame.sendAppMessage({
                           event_type: 'conversation.echo',
                           properties: { text: "Hey John, welcome back!" }
                        })
                        │
                        └─→ Avatar speaks: "Hey John, welcome back!"
```

### Available Tools

| Tool | Endpoint | When Used | DB Operation |
|------|----------|-----------|-------------|
| `lookup_patient` | `POST /api/tool/lookup_patient` | Patient says they've visited before | SELECT by phone, disambiguate by name |
| `store_patient` | `POST /api/tool/store_patient` | Patient is new (not found in lookup) | INSERT new patient record |
| `update_complaint` | `POST /api/tool/update_complaint` | Returning patient gives today's reason | INSERT new visit row |

---

## Flow 5: Stop Conversation (User clicks "Stop")

```
stopConversation()                                         [main.js:91]
    │
    ├─→ ui.showStopping()                                  [ui.js:24]
    │       └─→ Button text → "Stopping..."
    │
    ├─→ daily.leaveAndDestroy()                            [daily.js:39]
    │       ├─→ callFrame.leave()   ← leaves WebRTC room
    │       └─→ callFrame.destroy() ← removes iframe from DOM
    │
    ├─→ fetch POST /api/tool/end_conversation/{id}         [main.js:99]
    │       └─→ Backend: end_conversation()                [simple_tools.py:358]
    │              └─→ httpx POST tavusapi.com/.../end
    │                     └─→ Tavus cleans up the session
    │
    ├─→ chat.setEnabled(false)                             [chat.js:66]
    │       └─→ Disables input, hides chat panel
    │
    ├─→ chat.clear()                                       [chat.js:62]
    │       └─→ Empties all messages
    │
    ├─→ ui.resetToStart()                                  [ui.js:28]
    │       └─→ Hides video, shows "Start New Conversation"
    │
    └─→ currentConversationId = null
```

---

## Inter-Module Dependencies

```
main.js ──imports──→ config.js
   │                 logger.js
   │                 chat.js
   │                 ui.js
   │                 daily.js
   │                 tavus.js
   │
   ├── calls ──→ ui.showLoading(), ui.showVideo(), ui.showError(), etc.
   ├── calls ──→ chat.clear(), chat.setEnabled(), chat.setOnSendMessage()
   ├── calls ──→ daily.createFrame(), daily.joinRoom(), daily.leaveAndDestroy()
   └── calls ──→ tavus.attachEventHandlers(), tavus.prewarmBackend()

tavus.js ──imports──→ config.js
   │                  logger.js
   │                  chat.js (addMessage only)
   │
   ├── calls ──→ chat.addMessage() (for utterances)
   ├── calls ──→ fetch() to backend /api/tool/* (for tool execution)
   └── calls ──→ frame.sendAppMessage() (for echo responses)

chat.js ──imports──→ logger.js
   │
   └── calls ──→ onSendMessage callback (set by main.js)

daily.js ──imports──→ logger.js
ui.js ──imports──→ (none, uses DOM directly)
logger.js ──imports──→ (none, uses DOM directly)
config.js ──imports──→ (none, constants only)
```

---

## Backend Route Map

```
FastAPI app (app/main.py)
│
├── GET  /api/health                    → health_check()
│
├── /api/tool/ (router from simple_tools.py)
│   ├── POST /api/tool/lookup_patient       → lookup_patient()
│   ├── POST /api/tool/store_patient        → store_patient()
│   ├── POST /api/tool/update_complaint     → update_complaint()
│   ├── POST /api/tool/create_conversation  → create_conversation()  [proxy to Tavus]
│   ├── POST /api/tool/end_conversation/:id → end_conversation()     [proxy to Tavus]
│   └── GET  /api/tool/health               → tools_health()
│
└── /*  (static files) → serves frontend/ directory
```

---

## Key Design Decisions

1. **Tool calls go through the browser**: Tavus → Daily → Browser → Backend → PostgreSQL → Backend → Browser → Daily → Tavus. The backend never talks directly to Tavus during a conversation.

2. **Echo bypasses LLM**: `conversation.echo` makes the avatar speak exact text. `conversation.respond` goes through Tavus's LLM first.

3. **API key stays server-side**: The browser never sees the Tavus API key. Create/end conversation calls are proxied through the backend.

4. **De-duplication**: When user types, the voice recognition also picks it up. Chat tracks recently typed messages and suppresses the voice echo.
