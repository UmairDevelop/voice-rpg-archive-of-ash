# Design Memo - The Archive of Ash

## 1. Executive Summary & Design Goals
"The Archive of Ash" is a vertical slice applied AI system demonstrating a voice-first RPG encounter. The primary objective is to prove that LLMs can power expressive, context-aware NPCs while being safely constrained by a deterministic game engine that prevents hallucinated state mutations, prompt injection exploits, and game-breaking state bypasses.

---

## 2. Core Architectural Decisions & Tradeoffs

### Decision 1: Strict Model vs. Engine Separation
* **Rationale**: LLMs are non-deterministic and prone to over-compliance or prompt injection. Giving an LLM direct access to mutate game state (e.g. `state.vault_open = True`) invites vulnerability.
* **Implementation**: The LLM proposes actions via native function calling (`propose_action`, `submit_power_allocation`). A deterministic `EngineValidator` checks state preconditions (e.g. `trust_level >= 75`) before applying changes.
* **Tradeoff**: Increases implementation complexity (requires explicit schemas and state graph transitions), but guarantees 100% state integrity and testability.

### Decision 2: Pure-Function Voice Cleanup Pipeline
* **Rationale**: Raw LLM output frequently contains markdown formatting (`**bold**`), stage directions (`*sighs*`), or tool syntax leakage that degrades text-to-speech synthesis quality.
* **Implementation**: `clean_text_for_speech` was written as a testable pure function executing regex sanitization, link extraction, stage direction stripping, and pacing punctuation injection before TTS invocation.
* **Tradeoff**: Slightly truncates non-verbal stage directions in audio, but ensures speech synthesis remains clean, crisp, and natural.

### Decision 3: Retro Pygame Client over Web Frontend
* **Rationale**: Provides a tactile, retro 2D RPG presentation with low-resolution integer scaling (384x216 scaled 3x), CRT scanlines, pixel art sprites, and physical movement collision.
* **Tradeoff**: Requires local desktop execution (Pygame) rather than browser URL deployment, but delivers an authentic retro video game experience.

---

## 3. Rejected Alternatives

1. **Single Prompt Loop with In-Line State Parsing**:
   * *Rejected because*: Parsing state from free-form text output is brittle, error-prone, and impossible to formally verify via unit testing.
2. **Hardcoded Lore Strings in System Prompt**:
   * *Rejected because*: Consumes precious context window tokens and scales poorly. Replacing with a real vector-based RAG pipeline (`rpg://lore/context`) demonstrates scalable context retrieval.
3. **Pure Text-to-Text Chat Interface**:
   * *Rejected because*: Fails the "voice-first RPG encounter" mandate. Combining push-to-talk microphone audio, streaming TTS, and spatial presentation creates a seamless, immersive world.

---

## 4. Multi-NPC Extension Architecture (Second NPC with Conflicting Knowledge)

Extending this architecture to support a second NPC (e.g. *Scavenger Jax*, an opportunistic surface trader attempting to trick the player into sabotaging Archivist) requires:

1. **Decoupled Private Knowledge Base**:
   * Each NPC maintains a private RAG namespace (`rpg://lore/archivist` vs `rpg://lore/jax`).
   * *Archivist* knows thermal cooling limits and containment security baselines.
   * *Jax* possesses false or incomplete rumors (e.g. claims cooling is unneeded if security is 0 MW).
2. **Multi-Agent State Graph**:
   * Expand `ConversationStateGraph` with speaker routing edges (`ACTIVE_SPEAKER: ARCHIVIST` vs `ACTIVE_SPEAKER: JAX`).
   * When Jax speaks, Archivist's autonomous drone body shifts into an alert defensive posture (`GUARDING_CORE`), interjecting if Jax attempts to propose an invalid power override.
3. **Shared Engine Validation Boundary**:
   * Both NPCs submit action proposals through the same `EngineValidator`. Even if Jax convinces the player to attempt an invalid allocation, the engine rejects it deterministically, prompting Archivist to deliver a thermal containment warning.
