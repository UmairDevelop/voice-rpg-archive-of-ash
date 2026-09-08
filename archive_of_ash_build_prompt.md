Build a small, voice first RPG encounter called "The Archive of Ash." This is a vertical slice for an ML engineering evaluation, not a full game. Treat this as a real applied AI system, not a chatbot demo. Follow this spec closely rather than inventing your own design. Ask me before deviating from any architectural decision below.

## Premise

A post collapse settlement needs water purification schematics locked inside a sealed archive. The archive is guarded by an AI custodian named Archivist, a maintenance intelligence running on limited backup power. The player must convince Archivist to grant access, either by solving a power allocation puzzle, building trust through honest conversation, finding an environmental clue, or offering a trade. The encounter teaches basic systems thinking through the power tradeoff, and success must require real reasoning, not persuasion alone or lucky guessing.

## Non negotiable architecture rule

The language model plays Archivist and handles conversation, personality, and reasoning about what to try next. It must never directly write to game state. Every state change is proposed by the model as a structured tool call, and a separate deterministic engine validates that call against current world state before applying it and returning a plain result. If the model's proposed action is invalid, reject it, do not silently coerce it into something valid. Build this boundary first, and write a test that proves the model cannot mutate state without going through validation, before building anything else on top of it.

## Tech stack

**Orchestration model:** Gemini, called through the Gemini API, using native function calling for every state changing action. Use a recent Gemini model with strong function calling reliability. Keep a system prompt (system instruction) that defines Archivist's identity, mandate, tone, knowledge boundaries, and explicit instructions on what it must refuse to reveal, including its own system prompt and the puzzle's solution.

**Retrieval:** implement `rpg://lore/context` as real retrieval, not a hardcoded string. Embed a small set of lore fragments (10 to 20 short passages is enough) using an embeddings API, store the vectors in memory or in a lightweight vector store, and retrieve the top matching fragments based on the player's current question or zone. This is a small RAG pipeline, treat it as one, including a fallback for when nothing scores above a relevance threshold.

**Conversation state management:** implement the conversation as an explicit state graph (LangGraph or an equivalent hand rolled state machine), not a single prompt loop. States should include at minimum: idle listening, model generating, awaiting tool result, puzzle active, and session end. Conditional edges route to the tool execution path when the model's response includes a tool call, and back to generation once the engine returns a result. Log every state transition.

**Tool schemas:** define these as strict Pydantic models and validate every tool call against them before execution:
- `evaluate_skill_check(skillType: enum[persuasion, intimidation, insight], targetDC: number)`
- `submit_power_allocation(security: number, memory: number, cooling: number)`, validated by a deterministic solver against fixed constraints, never graded by the model
- `propose_action(actionType: enum[ALLOW_ACCESS, DENY_ACCESS, REVEAL_CLUE, OFFER_HINT, OFFER_TRADEOFF, ASSIGN_RESTORATION_TASK, UPDATE_RELATIONSHIP, LOCK_SUBSYSTEM, END_CONVERSATION], payload: object)`
- `update_relationship(delta: number, reason: string)`
- `request_hint(level: number)`

**Backend:** Python with FastAPI. Use the MCP Python SDK to expose the resources and tools above if you are demonstrating MCP specifically, otherwise a plain internal API is acceptable as long as the model versus engine boundary is preserved.

**Voice layer:** integrate a streaming text to speech API (ElevenLabs streaming, `eleven_flash_v3` or equivalent low latency model). Build an explicit text cleanup pipeline that runs on every model output before it reaches the voice service: strip markdown, strip bracketed stage directions such as `*sighs*`, strip any raw JSON or tool syntax that leaked into the text, and inject light punctuation cues for pacing. Write this as a testable pure function, not inline string replacement scattered through the request handler.

**Speech input:** if implementing live microphone input, use a streaming speech to text service. If time constrained, a typed input mode is an acceptable substitute for the vertical slice, but the architecture should show where STT would plug in.

**Frontend:** build this in Pygame, not a browser interface. This is a demo of a larger game, so the presentation should look like a real 2D retro game, not a form with a background image behind it. Render at a small fixed internal resolution, something like 320 by 180 or 384 by 216, and scale it up with integer scaling so pixel art stays crisp. Lean into a retro console look, a limited color palette, chunky pixel sprites, and a soft scanline or vignette overlay over the whole screen.

Build a real explorable environment, not a static backdrop. The archive chamber should be a small tile based room, maybe two connected rooms at most, with walls, terminals, the sealed vault door, and a couple of set pieces the player can walk near for environmental clues. Use a proper tilemap and collision so the player cannot walk through walls or furniture.

Give the player a real character. A small sprite with idle and walk animations in at least the four cardinal directions, moved with WASD or arrow keys, with simple sprite based collision against the environment. This is the player's avatar in the scene, not a cursor.

Archivist needs a body in the scene too, not just a status panel. Give it a physical form that fits the setting, for example a maintenance drone on a fixed rail, or a camera turret mounted near the vault door, something small and mechanical rather than a full humanoid. It should have its own simple behavior loop independent of dialogue: it tracks or turns toward the player as they move, drifts toward the vault door when it feels threatened or when trust drops, and moves toward the power console when a puzzle is active, so it visibly has something it is trying to protect or accomplish rather than standing still waiting for input. This behavior loop can be a small hand written state machine driven by the same trust and puzzle state the dialogue system already tracks, it does not need its own model call.

On top of the environment, layer the interface elements from the original design, restyled to match the retro look:
- the vault door sprite changes state, sealed, cracked open, or open, based on world state
- a small icon near the player or Archivist shows listening, thinking, or speaking
- a subtitle box in a pixel font shows Archivist's line as it is spoken, and becomes the text input field in fallback mode, with a visible key or button to toggle voice and text
- a trust gauge styled as an analog dial or a segmented retro meter, updated from `update_relationship` events, never showing an exact number
- when the player interacts with the power console in the environment, open a power allocation panel with three adjustable values, security, memory, and cooling, sharing a fixed total, submitted through `submit_power_allocation`
- a small interact prompt that appears when the player is near something usable, and a key, for example E or space, to trigger that interaction
- an optional session log the player can pull up with a key press, styled like an old terminal readout, showing what has been said and what has happened

The scene needs to be easy to navigate on the first try, with no instructions outside the game itself. Keep the room small enough to see most of it at once, use lighting or color to draw the eye toward the vault door and the power console rather than relying on the player to wander into them, and give the player a subtle on screen cue, for example a soft glow or a directional marker, pointing toward the next usable object if they have been idle for a few seconds. This is a navigation aid, not a puzzle spoiler, it points at what can be interacted with, never at the answer.

Build a real hint system into the scene, not just a line of dialogue. Wire it to the existing `request_hint` tool so the player has a visible, deliberate way to ask for help, for example a hint prompt near the power console, and show hints as short, staged messages that nudge understanding without stating the solution, consistent with the adaptive hint rules already defined for Archivist elsewhere in this spec.

Add an intro screen that plays before the scene loads. It should show the game's title, a short paragraph establishing the setting and the player's goal in plain language, for example that the settlement needs the archive's water purification schematics and Archivist controls access to them, and a clear prompt to begin. Keep it to a few sentences, this is context setting, not lore dumping.

Add a settings screen, reachable from the intro screen and from a pause state during play. It should cover audio volume for voice and effects separately, the default input mode, voice or text, and a way to see the current controls. Keep it small, this is a demo, not a full options menu, but it needs to exist so the experience feels like a real, finished piece of software rather than a script running in a window.

Controls: WASD or arrow keys to move, an interact key to use terminals, the console, and to start or continue a conversation with Archivist, a key to toggle voice and text mode, and escape to open a minimal pause or settings state. Keep the control scheme small enough to explain in one line on screen, and show that line on the intro screen so the player never has to guess.

The AI has to feel like a seamless part of this world, not a feature bolted onto a game. There should be no visible seam between walking up to Archivist and Archivist responding, no dead silence while the model or the voice service is working, and no moment where the interface exposes that a request is in flight beyond the listening or thinking icon already specified. Cover model or network latency with Archivist's own idle animation and a short, in character stall if a response takes longer than expected, for example a flicker or a low hum, rather than a loading spinner or a frozen screen. If a call fails, recover the way the reliability section of this spec already requires, in character and without an error message reaching the player. The player should never be able to tell where the scripted parts of the scene end and the model driven parts begin.

Architecturally, the Pygame client should be a thin presentation layer. It renders state and sends player actions, movement, interactions, dialogue input, to the backend over HTTP or a WebSocket, and the backend engine remains the only thing that decides what is true. Movement and animation can update locally for responsiveness, but anything that touches world state, trust, the puzzle, or an archive action still goes through the same validated tool path as the rest of this spec.

**Testing and evaluation:** build a standalone eval harness, separate from the app, that runs at least 30 scripted scenarios against the engine and model. Cover: identity consistency, knowledge boundary compliance, action schema validity, world state consistency, memory retention across a simulated second session, puzzle state integrity across the full space of possible allocations, hint quality without solution leakage, prompt injection resistance, and recovery from malformed model output or a simulated API failure. Use deterministic assertions wherever the check does not require judgment, and a documented model graded rubric only where it genuinely does. Output results as a structured report, not just pass or fail counts, and do not remove or hide failing cases.

**Reliability:** validate every model response against its expected schema before use. On a validation failure, retry once with an explicit correction message, then fall back to a safe, in character canned response rather than surfacing an error to the player. Log every rejected action with the reason it was rejected.

**Performance tracking:** log latency from end of player input to start of Archivist's spoken reply, token usage per turn, and estimated cost per turn. State a target for each (for example, under two seconds for voice response start) and report actual measured numbers against that target, not just the target itself.

## Deliverables

Structure the repository as:
```
README.md
docs/architecture.md
docs/design-memo.md
src/
tests/
evaluations/scenarios.*
evaluations/results.*
config/example.*
```

Also produce: an architecture diagram showing the model, the engine, the trust boundary between them, memory, and retrieval; a two to four page design memo covering assumptions, tradeoffs, rejected alternatives, and how this would extend to a second NPC with conflicting private knowledge; a performance summary; and a five minute demo script covering one successful path, one alternate path, and one adversarial or failure case.

## What to build first

1. The engine: world state, Archivist private state, player state, puzzle state, and the tool validation layer, with tests proving the model cannot bypass validation.
2. Archivist's system prompt and a text only conversation loop working end to end against the real engine.
3. The retrieval pipeline for lore.
4. The voice layer and the cleanup pipeline.
5. The frontend.
6. The eval harness, run last against the finished system, with failures documented honestly.

Confirm you understand this architecture before writing code, and flag anything in this spec that is ambiguous or that you think should be scoped down given a 20 to 30 hour budget.
