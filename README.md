# The Archive of Ash - Voice-First RPG Encounter Vertical Slice

A voice-first 2D retro RPG encounter vertical slice featuring an AI custodian NPC (**Archivist**), a deterministic game engine state boundary, Gemini AI API native function calling, RAG lore retrieval (`rpg://lore/context`), streaming TTS with pure-function text cleanup, a Pygame pixel art frontend, and an extensive 32-scenario evaluation harness.

---

## 🚀 Quick Start & Setup

### 1. Prerequisites
- Python 3.10+ (Verified on Python 3.14.3)
- Working Microphone & Speakers
- Gemini API Key (`GEMINI_API_KEY`)

### 2. Installation
Install all Python dependencies:
```bash
pip install -r requirements.txt
```

### 3. Configuration
Copy `config/example.env` to `config/.env` and add your Gemini API Key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

---

## 🎮 Running the Game

### Launch Pygame Client (Standalone Mode)
To launch the 2D retro game client directly:
```bash
python -m src.client.main
```
- **Controls**:
  - `WASD` / `Arrow Keys`: Move player avatar around archive chamber
  - `E` / `Space`: Interact with terminals, Power Console, or talk to Archivist
  - `V` (Hold): Push-to-Talk voice recording input
  - `Enter`: Submit typed text input
  - `L` / `Tab`: Toggle Session Log terminal modal
  - `Esc` / `S`: Settings & control map

### Launch Backend Server (Optional API Server Mode)
To launch the FastAPI engine server:
```bash
uvicorn src.backend.server:app --reload --port 8000
```
- API Endpoints:
  - `GET /api/state`: Returns current world state JSON
  - `POST /api/turn`: Processes dialogue turn (returns text, tool validation, TTS audio path, and performance metrics)
  - `POST /api/power_allocation`: Direct UI power grid solver submission
  - `GET /api/metrics`: Performance latency & token cost summary

---

## 🧪 Testing & Evaluation Harness

### Run Unit Tests
Verifies deterministic state boundary protection, pure-function text cleanup, puzzle solver rules, and RAG lore retrieval:
```bash
python -m pytest tests/
```

### Run Standalone Evaluation Harness
Executes 32 scripted scenarios across 9 required categories (identity, boundaries, schemas, state consistency, session memory, puzzle allocations, hints, prompt injection, API failure recovery):
```bash
python -m evaluations.eval_harness
```
- Outputs results to [evaluations/results.json](file:///c:/Users/Umair/Desktop/voice-rpg-archive-of-ash/evaluations/results.json) and human-readable report in [evaluations/results.md](file:///c:/Users/Umair/Desktop/voice-rpg-archive-of-ash/evaluations/results.md).

---

## 📑 Repository Structure & Documentation

```
voice-rpg-archive-of-ash/
├── README.md                      # Setup & overview (This file)
├── requirements.txt               # Dependencies
├── config/
│   └── example.env                # Environment configuration template
├── docs/
│   ├── architecture.md            # System architecture diagram & component spec
│   ├── design-memo.md             # 2-4 page design memo (tradeoffs & 2nd NPC extension)
│   ├── performance_summary.md     # Measured latency, token count, & cost analysis
│   └── demo_script.md             # 5-minute evaluation demo script (3 paths)
├── src/
│   ├── engine/                    # Deterministic Game Engine Layer (WorldState, Pydantic actions, EngineValidator)
│   ├── agent/                     # LLM & Conversation Orchestration (Gemini function calling, RAG, state graph)
│   ├── voice/                     # Voice Layer & Text Cleanup (clean_text_for_speech, ElevenLabs / edge-tts)
│   ├── backend/                   # FastAPI Server & Performance Tracker
│   └── client/                    # Pygame 2D Retro Presentation Layer (384x216 integer scaled display, UI, sprites)
├── tests/                         # Automated pytest suite
└── evaluations/                   # 32-scenario evaluation harness & results reports
```
