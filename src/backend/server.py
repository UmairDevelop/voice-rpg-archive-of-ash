import time
import asyncio
from typing import Dict, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.engine.validator import EngineValidator
from src.agent.archivist import ArchivistAgent
from src.voice.tts import TTSVoiceEngine
from src.backend.metrics import PerformanceTracker

app = FastAPI(title="The Archive of Ash - Backend Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core engine & agent instances
validator = EngineValidator()
archivist = ArchivistAgent(validator=validator)
tts_engine = TTSVoiceEngine()
tracker = PerformanceTracker(target_latency_sec=2.0)


class TurnRequest(BaseModel):
    user_input: str
    input_mode: str = "text"  # text or voice


class PowerAllocationRequest(BaseModel):
    security: float
    memory: float
    cooling: float


@app.get("/")
def root():
    return {"status": "online", "game": "The Archive of Ash", "version": "1.0.0"}


@app.get("/api/state")
def get_world_state():
    return validator.get_state().model_dump()


@app.post("/api/turn")
async def process_turn(req: TurnRequest):
    start_time = time.time()
    
    # Process turn through Archivist LLM & Engine
    text_out, validation_res, metrics = archivist.process_turn(req.user_input)
    
    # Generate speech audio
    tts_success, cleaned_text, audio_path = await tts_engine.generate_speech_audio(text_out)
    
    elapsed = time.time() - start_time
    
    # Record metrics
    metrics_record = tracker.record_turn(
        latency_sec=elapsed,
        prompt_tokens=metrics.get("prompt_tokens", 100),
        response_tokens=metrics.get("candidates_tokens", 30),
        cost_usd=metrics.get("estimated_cost", 0.0001),
        input_type=req.input_mode
    )

    return {
        "text": text_out,
        "cleaned_text": cleaned_text,
        "tts_audio_path": audio_path if tts_success else None,
        "tool_validation": validation_res.model_dump() if validation_res else None,
        "world_state": validator.get_state().model_dump(),
        "performance": metrics_record,
    }


@app.post("/api/power_allocation")
def submit_power_allocation(req: PowerAllocationRequest):
    res = validator.validate_and_apply("submit_power_allocation", {
        "security": req.security,
        "memory": req.memory,
        "cooling": req.cooling,
    })
    return {
        "validation_result": res.model_dump(),
        "world_state": validator.get_state().model_dump(),
    }


@app.get("/api/metrics")
def get_metrics():
    return tracker.get_summary()
