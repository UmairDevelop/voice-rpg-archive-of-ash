import pygame
from typing import Dict, Any, List, Tuple, Optional


class UIOverlay:
    """
    HUD and GUI Layer for Pygame Client (Crisp HD 768x416 Resolution):
    - Voice-First Interface with API Key status checking
    - Subtitle dialogue box & text input field
    - Trust gauge analog meter
    - Power allocation panel UI
    - Session log terminal modal
    - Intro, Settings, and Pause screens
    """
    def __init__(self, resolution: Tuple[int, int] = (768, 416)):
        self.width, self.height = resolution
        pygame.font.init()
        self.font_small = pygame.font.SysFont("Verdana", 12, bold=True)
        self.font_title = pygame.font.SysFont("Verdana", 18, bold=True)

        self.input_text = ""
        self.active_mode = "VOICE"
        self.show_power_panel = False
        self.show_session_log = False
        self.current_screen = "INTRO"
        self.api_connected = False

        # Settings
        self.voice_volume = 0.8
        self.sfx_volume = 0.7

        # Power Console UI values
        self.power_security = 50.0
        self.power_memory = 30.0
        self.power_cooling = 20.0
        self.selected_power_field = 0

    def draw_hud(
        self,
        surface: pygame.Surface,
        dialogue_text: str,
        trust_level: float,
        interact_prompt: Optional[str],
        status_mode: str,
        session_log: List[Dict[str, Any]],
        api_connected: bool = False
    ):
        self.api_connected = api_connected

        if self.current_screen == "INTRO":
            self.draw_intro_screen(surface)
            return
        elif self.current_screen == "SETTINGS":
            self.draw_settings_screen(surface)
            return

        # 0. API Missing Warning Banner at top if not connected
        if not self.api_connected:
            warn_rect = pygame.Rect(16, 8, self.width - 32, 26)
            pygame.draw.rect(surface, (200, 40, 40), warn_rect)
            pygame.draw.rect(surface, (255, 255, 255), warn_rect, 2)
            w_txt = self.font_small.render("⚠️ GEMINI_API_KEY NOT SET in config/.env! Add your key to activate Gemini Voice AI.", True, (255, 255, 255))
            surface.blit(w_txt, (warn_rect.x + 10, warn_rect.y + 4))

        # 1. Subtitle & Dialogue Box (Bottom Overlay)
        box_rect = pygame.Rect(16, self.height - 82, self.width - 32, 70)
        pygame.draw.rect(surface, (14, 18, 26), box_rect)
        pygame.draw.rect(surface, (70, 160, 240), box_rect, 2)

        # Draw Subtitle Line (Archivist spoken text)
        sub_txt = self.font_small.render(f"Archivist: {dialogue_text[:68]}", True, (255, 255, 255))
        surface.blit(sub_txt, (box_rect.x + 12, box_rect.y + 6))

        # Mode Display & Input Status Line
        if self.active_mode == "VOICE":
            if status_mode == "RECORDING":
                voice_status = "🔴 RECORDING VOICE... Release [SPACE / V] to send to Gemini API"
                status_color = (255, 80, 80)
            elif status_mode == "THINKING":
                voice_status = "⚡ GEMINI AI THINKING & TRANSCRIBING VOICE..."
                status_color = (100, 200, 255)
            else:
                voice_status = "🎤 VOICE MODE: Hold [SPACE or V] to speak to Gemini AI"
                status_color = (80, 240, 130)

            inp_txt = self.font_small.render(voice_status, True, status_color)
            surface.blit(inp_txt, (box_rect.x + 12, box_rect.y + 26))
            
            hint_txt = self.font_small.render(f"Status: [{status_mode}] | Press [T] for Optional Text Chat Mode", True, (160, 185, 210))
            surface.blit(hint_txt, (box_rect.x + 12, box_rect.y + 46))
        else:
            input_prompt = f"> Text Chat: {self.input_text}_"
            inp_txt = self.font_small.render(input_prompt, True, (255, 190, 40))
            surface.blit(inp_txt, (box_rect.x + 12, box_rect.y + 26))

            hint_txt = self.font_small.render(f"Status: [{status_mode}] | ENTER: Send | Press [T] for Voice Mode", True, (160, 185, 210))
            surface.blit(hint_txt, (box_rect.x + 12, box_rect.y + 46))

        # 2. Trust Gauge (Top Right Meter)
        y_offset = 38 if not self.api_connected else 40
        meter_rect = pygame.Rect(self.width - 170, y_offset, 154, 28)
        pygame.draw.rect(surface, (14, 18, 26), meter_rect)
        pygame.draw.rect(surface, (120, 135, 160), meter_rect, 2)

        fill_width = int((trust_level / 100.0) * 148)
        trust_color = (230, 50, 50) if trust_level < 40 else ((255, 170, 30) if trust_level < 70 else (50, 230, 110))
        pygame.draw.rect(surface, trust_color, (meter_rect.x + 3, meter_rect.y + 3, fill_width, 22))
        
        trust_lbl = self.font_small.render(f"TRUST: {int(trust_level)}%", True, (255, 255, 255))
        surface.blit(trust_lbl, (meter_rect.x + 36, meter_rect.y + 4))

        # 3. Interact Prompt Overlay
        if interact_prompt:
            prompt_bg = pygame.Rect(self.width // 2 - 130, y_offset, 260, 28)
            pygame.draw.rect(surface, (20, 32, 50), prompt_bg)
            pygame.draw.rect(surface, (255, 190, 40), prompt_bg, 2)
            p_txt = self.font_small.render(f"Press [E]: {interact_prompt}", True, (255, 255, 255))
            surface.blit(p_txt, (prompt_bg.x + 16, prompt_bg.y + 5))

        # 4. Power Console Overlay Panel
        if self.show_power_panel:
            self.draw_power_console_panel(surface)

        # 5. Session Log Terminal Modal
        if self.show_session_log:
            self.draw_session_log_modal(surface, session_log)

    def draw_power_console_panel(self, surface: pygame.Surface):
        panel_rect = pygame.Rect(self.width // 2 - 250, 48, 500, 260)
        pygame.draw.rect(surface, (16, 22, 32), panel_rect)
        pygame.draw.rect(surface, (255, 150, 0), panel_rect, 3)

        title = self.font_title.render("POWER ALLOCATION GRID CONSOLE", True, (255, 180, 0))
        surface.blit(title, (panel_rect.x + 70, panel_rect.y + 16))

        fields = [
            ("Security Subsystem (MW):", self.power_security, 0),
            ("Memory / Schematic (MW):", self.power_memory, 1),
            ("Thermal Cooling   (MW):", self.power_cooling, 2),
        ]

        total_alloc = self.power_security + self.power_memory + self.power_cooling
        tot_color = (50, 230, 110) if abs(total_alloc - 100.0) < 0.1 else (240, 60, 60)

        for name, val, idx in fields:
            y_pos = panel_rect.y + 60 + (idx * 45)
            color = (255, 255, 255) if idx == self.selected_power_field else (150, 165, 185)
            lbl = self.font_small.render(f"{name} [{val:.0f}]", True, color)
            surface.blit(lbl, (panel_rect.x + 24, y_pos))

            bar_rect = pygame.Rect(panel_rect.x + 250, y_pos + 2, 210, 18)
            pygame.draw.rect(surface, (32, 40, 56), bar_rect)
            pygame.draw.rect(surface, (255, 255, 255), bar_rect, 1)
            fill_w = int((val / 100.0) * 210)
            pygame.draw.rect(surface, (240, 140, 30), (bar_rect.x, bar_rect.y, fill_w, 18))

        tot_txt = self.font_title.render(f"TOTAL POWER: {total_alloc:.0f} / 100 MW", True, tot_color)
        surface.blit(tot_txt, (panel_rect.x + 24, panel_rect.y + 195))

        instructions = self.font_small.render("[UP/DN] Select Field | [LEFT/RIGHT] Adjust | [ENTER/E] Submit", True, (170, 185, 205))
        surface.blit(instructions, (panel_rect.x + 24, panel_rect.y + 228))

    def draw_session_log_modal(self, surface: pygame.Surface, log: List[Dict[str, Any]]):
        modal_rect = pygame.Rect(40, 32, self.width - 80, self.height - 64)
        pygame.draw.rect(surface, (12, 16, 24), modal_rect)
        pygame.draw.rect(surface, (50, 200, 130), modal_rect, 3)

        hdr = self.font_title.render("ARCHIVE TERMINAL SESSION LOG", True, (50, 230, 140))
        surface.blit(hdr, (modal_rect.x + 24, modal_rect.y + 16))

        y = modal_rect.y + 50
        for entry in log[-6:]:
            p_text = f"PLAYER: {entry.get('player', '')[:60]}"
            a_text = f"ARCHIVIST: {entry.get('archivist', '')[:60]}"
            t1 = self.font_small.render(p_text, True, (255, 210, 80))
            t2 = self.font_small.render(a_text, True, (180, 225, 255))
            surface.blit(t1, (modal_rect.x + 20, y))
            surface.blit(t2, (modal_rect.x + 20, y + 18))
            y += 40

        close_txt = self.font_small.render("Press [L] or [TAB] to Close", True, (150, 165, 185))
        surface.blit(close_txt, (modal_rect.x + 240, modal_rect.y + modal_rect.height - 28))

    def draw_intro_screen(self, surface: pygame.Surface):
        surface.fill((14, 18, 26))
        title = self.font_title.render("THE ARCHIVE OF ASH - VOICE RPG ENCOUNTER", True, (255, 180, 0))
        surface.blit(title, (self.width // 2 - 230, 28))

        api_color = (80, 240, 130) if self.api_connected else (255, 80, 80)
        api_status = "[CONNECTED ✅]" if self.api_connected else "[MISSING ⚠️ - Add key to config/.env]"

        body_lines = [
            f"GEMINI API STATUS: {api_status}",
            "",
            "A post-collapse settlement needs water purification schematics",
            "locked inside a sealed archive guarded by Archivist, an AI custodian",
            "running on emergency backup power.",
            "",
            "*** VOICE-FIRST ENCOUNTER ***",
            "Hold [SPACE] or [V] and speak into your microphone to talk to Archivist.",
            "Release key to send audio directly to Gemini API.",
            "",
            "CONTROLS:",
            "WASD / Arrows: Move Avatar",
            "Hold SPACE or V: Speak (Voice In)",
            "E: Interact with Terminals & Power Console",
            "T: Toggle Optional Text Chat Mode | L / TAB: Session Log",
            "",
            "PRESS ANY KEY TO BEGIN ENCOUNTER"
        ]

        y = 58
        for line in body_lines:
            color = api_color if "GEMINI API STATUS" in line else ((80, 240, 130) if "VOICE-FIRST" in line or "Hold" in line else ((255, 210, 80) if "CONTROLS" in line or "PRESS" in line else (190, 205, 225)))
            lbl = self.font_small.render(line, True, color)
            surface.blit(lbl, (self.width // 2 - 240, y))
            y += 18

    def draw_settings_screen(self, surface: pygame.Surface):
        surface.fill((14, 18, 26))
        title = self.font_title.render("SETTINGS & CONTROLS", True, (255, 180, 0))
        surface.blit(title, (self.width // 2 - 120, 36))

        api_status = "CONNECTED" if self.api_connected else "NOT SET (Add key to config/.env)"

        lines = [
            f"Gemini API Status: [{api_status}]",
            f"Voice Volume:       [{int(self.voice_volume * 100)}%]",
            f"SFX Volume:         [{int(self.sfx_volume * 100)}%]",
            f"Active Input Mode:  [{self.active_mode}]",
            "",
            "Press ESC or S to Return to Game"
        ]

        y = 90
        for line in lines:
            color = (80, 240, 130) if "CONNECTED" in line else ((255, 80, 80) if "NOT SET" in line else (230, 230, 230))
            lbl = self.font_small.render(line, True, color)
            surface.blit(lbl, (80, y))
            y += 24
