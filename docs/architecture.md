# System Architecture - The Archive of Ash

## System Diagram

```
+-----------------------------------------------------------------------------------+
|                                 PYGAME 2D CLIENT                                  |
|   - 384x216 Pixel Art Renderer (Scaled 3x CRT scanline overlay)                   |
|   - Player Avatar (4-Way WASD) & Archivist Drone Entity                           |
|   - HUD: Trust Meter, Dialogue Subtitles, Power Allocation Console UI             |
|   - Push-to-Talk Voice Recording (sounddevice)                                    |
+-----------------------------------------------------------------------------------+
                                   |                 ^
                         Player    |                 |  Spoken Response &
                         Action    v                 |  World State Sync
+-----------------------------------------------------------------------------------+
|                              FASTAPI BACKEND ENGINE                               |
|                                                                                   |
|  +---------------------------+             +-----------------------------------+  |
|  |     Lore RAG Pipeline     |             |    Explicit State Graph Machine   |  |
|  |   (rpg://lore/context)    |             |  IDLE -> MODEL_GEN -> TOOL_AWAIT  |  |
|  |   Vector Embeddings &     |             |       -> PUZZLE -> SESSION_END    |  |
|  |   Relevance Threshold     |             +-----------------------------------+  |
|  +---------------------------+                              ^                     |
|                |                                            |                     |
|                v                                            v                     |
|  +-----------------------------------------------------------------------------+  |
|  |                            GEMINI AI ORCHESTRATOR                           |  |
|  |  - System Instruction (Archivist Identity, Persona & Refusal Rules)         |  |
|  |  - Native Function Calling (Pydantic Tool Schemas)                          |  |
|  |  - Multimodal Audio & Text Input                                            |  |
|  +-----------------------------------------------------------------------------+  |
|                                        |                                          |
|                                        | Proposed Tool Call (JSON)                |
|                                        v                                          |
|  +-----------------------------------------------------------------------------+  |
|  |                   DETERMINISTIC GAME ENGINE VALIDATOR                       |  |
|  |  - Validates pre-conditions, schemas & solver rules before mutation           |  |
|  |  - Rejects unauthorized or invalid action proposals                         |  |
|  |  - Updates WorldState (Vault State, Trust Level, Power Grid)                 |  |
|  +-----------------------------------------------------------------------------+  |
|                                        |                                          |
|                                        v                                          |
|  +-----------------------------------------------------------------------------+  |
|  |                           VOICE SYNTHESIS LAYER                             |  |
|  |  - Pure-Function Text Cleanup (Strips markdown, stage directions, tool leakage)| |
|  |  - ElevenLabs Streaming TTS / Edge-TTS Fallback                             |  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
```

---

## Core Components Specification

### 1. Deterministic State Boundary (`src/engine/validator.py`)
The game engine maintains a strict security boundary. The LLM acts solely as a decision proposer; it cannot write to `WorldState` directly. Tool proposals (`EvaluateSkillCheck`, `SubmitPowerAllocation`, `ProposeAction`, `UpdateRelationship`, `RequestHint`) are strictly validated against Pydantic models and game rules before state mutation.

### 2. Gemini Orchestrator (`src/agent/archivist.py`)
Gemini handles dialogue generation, persona consistency, and intent classification. System instructions enforce identity boundary protection (refusal to leak prompts or direct solutions).

### 3. Lore RAG Retriever (`src/agent/rag.py`)
Serves `rpg://lore/context` using cosine vector similarity over 12 lore passages. Queries scoring below relevance threshold (0.15) trigger a non-hallucinatory fallback.

### 4. Text-to-Speech Cleanup (`src/voice/cleanup.py`)
Pure function pipeline that cleans model output prior to audio synthesis by stripping markdown formatting, bracketed stage directions (`*sighs*`), and raw tool syntax leakage.

### 5. Pygame Client (`src/client/`)
Thin presentation layer rendering a retro pixel-art 2-room archive chamber with integer scaling (384x216 scaled 3x), player sprite collision, Archivist drone movement, power console sliders, analog trust dial, and CRT scanlines.
