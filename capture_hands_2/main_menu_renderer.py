import pygame
from config import AppConfig
from renderer import Renderer

class MainMenuRenderer(Renderer):
    def __init__(self, screen, app, title):
        self.buttons = {
            'right': {
                'text': 'Lado Derecho',
                'subtitle': 'Stick Derecho + Botones A/B/X/Y',
                'rect': pygame.Rect(0, 0, 500, 100),
                'color': (70, 130, 180),
                'hover_color': (100, 160, 210)
            },
            'left': {
                'text': 'Lado Izquierdo', 
                'subtitle': 'Stick Izquierdo + D-Pad',
                'rect': pygame.Rect(0, 0, 500, 100),
                'color': (180, 70, 130),
                'hover_color': (210, 100, 160)
            },
            'triggers': {
                'text': 'Triggers',
                'subtitle': 'L1/L2/R1/R2',
                'rect': pygame.Rect(0, 0, 500, 100),
                'color': (130, 180, 70),
                'hover_color': (160, 210, 100)
            },
            'exit': {
                'text': 'Salir',
                'subtitle': '',
                'rect': pygame.Rect(0, 0, 500, 80),
                'color': (220, 20, 60),
                'hover_color': (255, 50, 90)
            }
        }
        
        super().__init__(screen, app, title)

    def resize_by(self, screen_width, screen_height):
        self.screen_size = (screen_width, screen_height)

        self.font_title = self.scaled_font(50)
        self.font_button = self.scaled_font(30)
        self.font_small = self.scaled_font(20)

        # posiciono botones
        button_w = int(0.7 * screen_width)
        button_h = int(0.1 * screen_height)
        button_x = (screen_width - button_w) // 2
        start_y = screen_height // 3
        spacing = int(0.05 * screen_height)
        
        for i, (key, button) in enumerate(self.buttons.items()):
            button['rect'].x = button_x
            button['rect'].y = start_y + (i * (button_h + spacing))
            button['rect'].w = button_w
            button['rect'].h = button_h
    
    def draw_app(self):
        screen_width, screen_height = self.screen_size
        
        # Título
        title = self.font_title.render("Captura de Gestos", True, AppConfig.TEXT)
        title_rect = title.get_rect(center=(screen_width // 2, int(0.1 * screen_height)))
        self.screen.blit(title, title_rect)
        
        # Subtítulo
        subtitle = self.font_small.render("Selecciona una sección para empezar", True, (200, 200, 200))
        subtitle_rect = subtitle.get_rect(center=(self.screen.get_width() // 2, 2 * int(0.1 * screen_height)))
        self.screen.blit(subtitle, subtitle_rect)
        
        # Botones
        mouse_pos = pygame.mouse.get_pos()
        
        for key, button in self.buttons.items():
            rect = button['rect']
            
            is_hover = rect.collidepoint(mouse_pos)
            color = button['hover_color'] if is_hover else button['color']
            
            pygame.draw.rect(self.screen, color, rect, border_radius=15)
            pygame.draw.rect(self.screen, (255, 255, 255), rect, 3, border_radius=15)
            
            text = self.font_button.render(button['text'], True, AppConfig.TEXT)
            text_rect = text.get_rect(center=(rect.centerx, rect.centery - (int(0.025 * screen_height) if button['subtitle'] else 0)))
            self.screen.blit(text, text_rect)
            
            if button['subtitle']:
                sub = self.font_small.render(button['subtitle'], True, (200, 200, 200))
                sub_rect = sub.get_rect(center=(rect.centerx, rect.centery + int(0.025 * screen_height)))
                self.screen.blit(sub, sub_rect)
    
    def handle_click(self, pos):
        for key, button in self.buttons.items():
            if button['rect'].collidepoint(pos):
                if key == 'exit':
                    self.app.selected_option = "QUIT"
                else:
                    self.app.selected_option = key.upper()
                return