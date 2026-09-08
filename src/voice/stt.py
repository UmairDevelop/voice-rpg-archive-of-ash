import io
import wave
import time
import logging
from typing import Optional, Tuple
import numpy as np

logger = logging.getLogger("STTRecorder")


class VoiceRecorder:
    """
    Microphone recording helper supporting both continuous Voice Activity Detection (VAD)
    and push-to-talk speech input.
    """
    def __init__(self, sample_rate: int = 16000, vad_threshold: int = 400):
        self.sample_rate = sample_rate
        self.vad_threshold = vad_threshold
        self.recording = False
        self.auto_listening = False
        self.frames = []
        self.last_speech_time = 0.0
        self.speech_detected = False
        self.stream = None

    def start_recording(self):
        """Manual push-to-talk start."""
        try:
            import sounddevice as sd
            self.frames = []
            self.recording = True
            self.speech_detected = True

            def callback(indata, frames, time_info, status):
                if status:
                    logger.warning(f"Audio record status: {status}")
                if self.recording:
                    self.frames.append(indata.copy())

            if self.stream:
                try:
                    self.stream.stop()
                    self.stream.close()
                except Exception:
                    pass

            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype="int16",
                callback=callback,
            )
            self.stream.start()
            logger.info("Manual voice recording started.")
        except Exception as e:
            logger.error(f"Failed to start sounddevice recording: {e}")
            self.recording = False

    def stop_recording(self) -> Tuple[Optional[bytes], float]:
        """Stops recording and returns (wav_bytes, duration_seconds)"""
        if not self.recording:
            return None, 0.0

        self.recording = False
        try:
            if self.stream:
                self.stream.stop()
                self.stream.close()
                self.stream = None

            if not self.frames:
                return None, 0.0

            audio_data = np.concatenate(self.frames, axis=0)
            duration = len(audio_data) / self.sample_rate

            wav_io = io.BytesIO()
            with wave.open(wav_io, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_data.tobytes())

            return wav_io.getvalue(), duration
        except Exception as e:
            logger.error(f"Error stopping recording: {e}")
            return None, 0.0

    def start_auto_vad(self):
        """Starts continuous Voice Activity Detection listening."""
        try:
            import sounddevice as sd
            self.frames = []
            self.auto_listening = True
            self.speech_detected = False
            self.last_speech_time = time.time()

            def vad_callback(indata, frames, time_info, status):
                if not self.auto_listening:
                    return
                rms = np.sqrt(np.mean(indata.astype(np.float32)**2))
                if rms > self.vad_threshold:
                    self.speech_detected = True
                    self.last_speech_time = time.time()
                    self.frames.append(indata.copy())
                elif self.speech_detected:
                    self.frames.append(indata.copy())

            if self.stream:
                try:
                    self.stream.stop()
                    self.stream.close()
                except Exception:
                    pass

            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype="int16",
                callback=vad_callback,
            )
            self.stream.start()
            logger.info("Continuous VAD auto-listening active.")
        except Exception as e:
            logger.error(f"VAD start failed: {e}")
            self.auto_listening = False

    def check_vad_complete(self, silence_duration: float = 1.0) -> Tuple[bool, Optional[bytes], float]:
        """
        Checks if user finished speaking during VAD auto-listening.
        Returns (is_complete, wav_bytes, duration)
        """
        if not self.auto_listening or not self.speech_detected:
            return False, None, 0.0

        if time.time() - self.last_speech_time > silence_duration:
            self.auto_listening = False
            wav_bytes, dur = self.stop_recording()
            return True, wav_bytes, dur

        return False, None, 0.0
