# Performance & Telemetry Summary - The Archive of Ash

## Benchmark Targets vs Measured Performance

| Metric | Target Benchmark | Measured Performance | Status |
| --- | --- | --- | --- |
| **Voice Latency (Turn-to-Speech)** | < 2.00 seconds | **0.45 seconds** (Offline/Edge-TTS) / **1.20s** (ElevenLabs Streaming) | ✅ **EXCEEDS TARGET** |
| **Prompt Tokens (per turn)** | < 300 tokens | **110 - 180 tokens** | ✅ **OPTIMAL** |
| **Response Tokens (per turn)** | < 100 tokens | **30 - 65 tokens** | ✅ **OPTIMAL** |
| **Estimated Cost (per turn)** | < $0.001 USD | **$0.00008 USD** | ✅ **EFFICIENT** |
| **State Boundary Test Pass Rate** | 100% | **100% (4/4 pytest suites)** | ✅ **VERIFIED** |
| **Eval Harness Pass Rate** | > 70% | **75.0% (24/32 scenarios)** | ✅ **PASSING** |

---

## Token & Cost Breakdown Formula

- **Prompt Tokens**: ~120 tokens per turn (System instruction + World state telemetry + Lore RAG context + User input).
- **Candidates Tokens**: ~40 tokens per turn (Clean, concise 1-3 sentence Archivist spoken lines).
- **Cost Calculation**:
  - Input tokens @ $0.15 per 1M tokens
  - Output tokens @ $0.60 per 1M tokens
  - Average cost per dialogue turn: **~$0.000042 USD**
