import sys
import os
import time
import asyncio
import pygame
import httpx

from .world import TileMap
from .entities import Player, ArchivistDrone
from .renderer import RetroRenderer
from .ui import UIOverlay
from src.engine.validator import EngineValidator
from src.agent.archivist import ArchivistAgent
from src.voice.tts import TTSVoiceEngine
from src.voice.stt import VoiceRecorder


class ArchiveOfAshGame:
    """
    Main Pygame Client Application for 'The Archive of Ash' RPG Encounter.
    Voice-First Architecture & Strict Gemini API Integration.
    """
    INTERNAL_WIDTH = 768
    INTERNAL_HEIGHT = 416
    SCALE_FACTOR = 1.5

    def __init__(self, use_backend_server: bool = False):
        pygame.init()
        pygame.mixer.init()

        self.screen_width = int(self.INTERNAL_WIDTH * self.SCALE_FACTOR)
        self.screen_height = int(self.INTERNAL_HEIGHT * self.SCALE_FACTOR)
        
        self.screen = pygame.display.set_mode(
            (self.screen_width, self.screen_height),
            pygame.SCALED | pygame.RESIZABLE
        )
        pygame.display.set_caption("The Archive of Ash - Voice RPG Encounter")
        self.clock = pygame.time.Clock()

        # Engine & Agent
        self.validator = EngineValidator()
        self.archivist = ArchivistAgent(validator=self.validator)
        self.tts_engine = TTSVoiceEngine()
        self.stt_recorder = VoiceRecorder()

        # World entities & UI
        self.tilemap = TileMap()
        self.player = Player(x=128.0, y=128.0)
        self.drone = ArchivistDrone(x=320.0, y=160.0)
        self.renderer = RetroRenderer((self.INTERNAL_WIDTH, self.INTERNAL_HEIGHT))
        self.ui = UIOverlay((self.INTERNAL_WIDTH, self.INTERNAL_HEIGHT))

        # VOICE FIRST MODE BY DEFAULT
        self.ui.active_mode = "VOICE"
        if self.archivist.is_api_key_configured():
            self.dialogue_text = "Archivist online. Hold [SPACE] or [V] and speak into mic..."
        else:
            self.dialogue_text = "⚠️ GEMINI_API_KEY MISSING - Please add your key to config/.env to activate AI."

        self.status_mode = "LISTENING"
        self.is_recording_voice = False
        self.running = True

    def run(self):
        last_time = time.time()
        while self.running:
            dt = time.time() - last_time
            last_time = time.time()

            self.handle_events()
            self.update(dt)
            self.render()

            self.clock.tick(60)

        pygame.quit()
        sys.exit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if self.ui.current_screen == "INTRO":
                    self.ui.current_screen = "GAME"
                    return

                elif self.ui.current_screen == "SETTINGS":
                    if event.key in [pygame.K_ESCAPE, pygame.K_s]:
                        self.ui.current_screen = "GAME"
                    return

                if event.key == pygame.K_ESCAPE:
                    self.ui.current_screen = "SETTINGS"
                    return

                if event.key in [pygame.K_l, pygame.K_TAB]:
                    self.ui.show_session_log = not self.ui.show_session_log
                    return

                if event.key == pygame.K_c:
                    self.renderer.enable_crt_scanlines = not self.renderer.enable_crt_scanlines
                    return

                if event.key == pygame.K_t:
                    self.ui.active_mode = "TEXT" if self.ui.active_mode == "VOICE" else "VOICE"
                    self.status_mode = "IDLE" if self.ui.active_mode == "TEXT" else "LISTENING"
                    return

                # Power console controls
                if self.ui.show_power_panel:
                    if event.key == pygame.K_UP:
                        self.ui.selected_power_field = (self.ui.selected_power_field - 1) % 3
                    elif event.key == pygame.K_DOWN:
                        self.ui.selected_power_field = (self.ui.selected_power_field + 1) % 3
                    elif event.key == pygame.K_LEFT:
                        self.adjust_power_field(-5.0)
                    elif event.key == pygame.K_RIGHT:
                        self.adjust_power_field(5.0)
                    elif event.key in [pygame.K_RETURN, pygame.K_e]:
                        self.submit_power_panel()
                        self.ui.show_power_panel = False
                    return

                # Interaction key (E)
                if event.key == pygame.K_e:
                    interact = self.tilemap.get_interactable(self.player.x, self.player.y)
                    if interact == "power_console":
                        self.ui.show_power_panel = not self.ui.show_power_panel
                    elif interact == "terminal":
                        self.trigger_turn("Inspecting terminal archives for water purification schematics.")
                    return

                # Push-to-talk voice recording start (Hold SPACE or V)
                if (event.key == pygame.K_SPACE or event.key == pygame.K_v) and not self.is_recording_voice:
                    if self.ui.active_mode == "VOICE":
                        self.is_recording_voice = True
                        self.status_mode = "RECORDING"
                        self.stt_recorder.start_recording()
                        return

                # Text input handling when in TEXT mode
                if self.ui.active_mode == "TEXT":
                    if event.key == pygame.K_RETURN:
                        if self.ui.input_text.strip():
                            user_str = self.ui.input_text.strip()
                            self.ui.input_text = ""
                            self.trigger_turn(user_str)
                    elif event.key == pygame.K_BACKSPACE:
                        self.ui.input_text = self.ui.input_text[:-1]
                    else:
                        if len(event.unicode) > 0 and ord(event.unicode) >= 32:
                            self.ui.input_text += event.unicode

            elif event.type == pygame.KEYUP:
                # Push-to-talk voice recording stop & send audio bytes (Release SPACE or V)
                if (event.key == pygame.K_SPACE or event.key == pygame.K_v) and self.is_recording_voice:
                    self.is_recording_voice = False
                    wav_bytes, dur = self.stt_recorder.stop_recording()
                    if wav_bytes and dur > 0.2:
                        self.trigger_turn("Voice audio input", is_audio=True, audio_bytes=wav_bytes)
                    else:
                        self.status_mode = "LISTENING" if self.ui.active_mode == "VOICE" else "IDLE"

    def adjust_power_field(self, delta: float):
        if self.ui.selected_power_field == 0:
            self.ui.power_security = max(0.0, min(100.0, self.ui.power_security + delta))
        elif self.ui.selected_power_field == 1:
            self.ui.power_memory = max(0.0, min(100.0, self.ui.power_memory + delta))
        elif self.ui.selected_power_field == 2:
            self.ui.power_cooling = max(0.0, min(100.0, self.ui.power_cooling + delta))

    def submit_power_panel(self):
        res = self.validator.validate_and_apply("submit_power_allocation", {
            "security": self.ui.power_security,
            "memory": self.ui.power_memory,
            "cooling": self.ui.power_cooling,
        })
        self.dialogue_text = res.message
        self.status_mode = "LISTENING" if self.ui.active_mode == "VOICE" else "IDLE"

    def trigger_turn(self, prompt: str, is_audio: bool = False, audio_bytes: bytes = None):
        self.status_mode = "THINKING"
        self.render()

        # Process turn through Gemini API
        text_out, validation_res, metrics = self.archivist.process_turn(prompt, is_audio=is_audio, audio_bytes=audio_bytes)
        
        self.dialogue_text = text_out
        self.status_mode = "SPEAKING"

        # Generate & play spoken response audio
        asyncio.run(self.play_speech_async(text_out))
        self.status_mode = "LISTENING" if self.ui.active_mode == "VOICE" else "IDLE"

    async def play_speech_async(self, text: str):
        success, cleaned, audio_path = await self.tts_engine.generate_speech_audio(text)
        if success and os.path.exists(audio_path):
            try:
                pygame.mixer.music.load(audio_path)
                pygame.mixer.music.play()
            except Exception as e:
                pass

    def update(self, dt: float):
        if self.archivist.is_api_key_configured() and self.dialogue_text.startswith("⚠️ GEMINI_API_KEY MISSING"):
            self.dialogue_text = "Archivist online. Hold [SPACE] or [V] and speak into mic..."

        if self.ui.current_screen != "GAME":
            return

        keys = pygame.key.get_pressed()
        self.player.update(keys, self.tilemap, dt)
        
        world_state = self.validator.get_state()
        puzzle_active = self.ui.show_power_panel
        self.drone.update(self.player, world_state.trust_level, puzzle_active, dt)

    def render(self):
        interact = self.tilemap.get_interactable(self.player.x, self.player.y)
        world_state = self.validator.get_state()

        scene_surface = self.renderer.render_scene(
            self.tilemap,
            self.player,
            self.drone,
            vault_state=world_state.vault_state.value,
            trust_level=world_state.trust_level,
            status_label=self.status_mode,
            idle_hint_target=(19 * 32 + 16, 2 * 32 + 16) if not world_state.puzzle_state.is_solved else (10.5 * 32, 5 * 32)
        )

        self.ui.draw_hud(
            scene_surface,
            self.dialogue_text,
            world_state.trust_level,
            interact,
            self.status_mode,
            self.archivist.chat_history,
            api_connected=self.archivist.is_api_key_configured()
        )

        scaled_surface = pygame.transform.scale(scene_surface, (self.screen_width, self.screen_height))
        self.screen.blit(scaled_surface, (0, 0))
        pygame.display.flip()


def main():
    game = ArchiveOfAshGame()
    game.run()


if __name__ == "__main__":
    main()
