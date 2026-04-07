# 🤖 AI Nurse Avatar

A conversational AI patient pre-assessment system powered by a lifelike avatar. Patients speak naturally with the avatar, which collects their information and stores it — no forms, no typing.

![AI Avatar Demo](AI_Avatar.gif)

---

## How It Works

A patient visits the web page, clicks **Start Conversation**, and speaks with an AI nurse avatar powered by [Tavus](https://tavus.io). The avatar:

1. Greets the patient by name if they're a returning visitor
2. Registers new patients automatically
3. Records the reason for today's visit
4. Stores everything securely in a local PostgreSQL database

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| AI Avatar | [Tavus](https://tavus.io) — lip-synced video + speech |
| WebRTC | [Daily.co](https://daily.co) — real-time audio/video |
| Backend | FastAPI + PostgreSQL |
| Frontend | Vanilla JS (7 modules) |

---

## Project Structure

```
ai-nurse-avatar/
├── frontend/
│   ├── index.html          ← 3-column layout (debug, video, chat)
│   └── js/
│       ├── main.js         ← Entry point
│       ├── tavus.js        ← Event routing + tool execution
│       ├── daily.js        ← WebRTC iframe lifecycle
│       ├── chat.js         ← Chat messages + de-duplication
│       ├── ui.js           ← Show/hide UI elements
│       ├── logger.js       ← Debug panel
│       └── config.js       ← Backend URL
├── backend/
│   ├── app/
│   │   ├── main.py         ← FastAPI app
│   │   ├── api/routes/     ← Tool endpoints
│   │   ├── services/       ← Tavus + patient logic
│   │   ├── db/             ← PostgreSQL models + repository
│   │   └── core/           ← Config, middleware, logging
│   ├── requirements.txt
│   └── .env.example        ← Copy to .env and fill in your keys
└── tavus/
    └── tools.json          ← Tavus tool definitions
```

---

## Getting Started

### 1. Clone the repo
```bash
git clone https://github.com/himanshu2904hk/ai-nurse-avatar.git
cd ai-nurse-avatar
```

### 2. Set up the backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy .env.example .env       # Then fill in your API keys
```

### 3. Configure `.env`
```env
TAVUS_API_KEY=your-tavus-api-key
TAVUS_PERSONA_ID=your-persona-id
DB_HOST=localhost
DB_PASSWORD=your-db-password
```

### 4. Run the backend
```bash
uvicorn app.main:app --reload
```

### 5. Open the frontend
Open `frontend/index.html` in your browser (or serve with Live Server).

---

## Available Tools

| Tool | Description |
|------|-------------|
| `lookup_patient` | Finds a returning patient by phone number |
| `store_patient` | Registers a new patient |
| `update_complaint` | Records the reason for today's visit |

---

## Architecture

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for the full function reference and flow diagrams, or open [`ai-avatar-architecture.html`](https://htmlpreview.github.io/?https://github.com/himanshu2904hk/ai-nurse-avatar/blob/main/ai-avatar-architecture.html) for the interactive visual diagram.

---

## Security

- API keys are stored in `.env` (never committed)
- Patient data stays on-premise in local PostgreSQL
- No PHI is sent to external cloud services
