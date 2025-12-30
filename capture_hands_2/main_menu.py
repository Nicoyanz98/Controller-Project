import pygame
from config import AppConfig
from camera_system import CameraSystem

class MainMenu:
    def scaled_font(self, size):
        scale = self.screen.get_height() / AppConfig.VIRTUAL_HEIGHT
        font_size = int(size * scale)
        return pygame.font.Font(None, font_size)
    
    def __init__(self, window, camera_system=None):
        self.name = "MAIN"
        self.screen = window

        self.selected_option = None

        pygame.display.set_caption("Captura de Gestos - Menú Principal")
        self.camera_system = camera_system
        if self.camera_system is None:
            self.camera_system = CameraSystem()

        self.create_UI()

    def create_UI(self):
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

        self.resize_UI(self.screen.get_width(), self.screen.get_height())

    def resize_UI(self, width, height):
        self.font_title = self.scaled_font(72)
        self.font_button = self.scaled_font(40)
        self.font_small = self.scaled_font(30)

        # posiciono botones
        button_w = int(0.7 * width)
        button_h = int(0.1 * height)
        button_x = (width - button_w) // 2
        start_y = height // 3
        spacing = int(0.05 * height)
        
        for i, (key, button) in enumerate(self.buttons.items()):
            button['rect'].x = button_x
            button['rect'].y = start_y + (i * (button_h + spacing))
            button['rect'].w = button_w
            button['rect'].h = button_h

    def draw(self):
        self.screen.fill(AppConfig.BACKGROUND)

        width = self.screen.get_width()
        height = self.screen.get_height()
        
        # Título
        title = self.font_title.render("Captura de Gestos", True, AppConfig.TEXT)
        title_rect = title.get_rect(center=(width // 2, int(0.1 * height)))
        self.screen.blit(title, title_rect)
        
        # Subtítulo
        subtitle = self.font_small.render("Selecciona una sección para empezar", True, (200, 200, 200))
        subtitle_rect = subtitle.get_rect(center=(self.screen.get_width() // 2, 2 * int(0.1 * height)))
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
            text_rect = text.get_rect(center=(rect.centerx, rect.centery - 15 if button['subtitle'] else rect.centery))
            self.screen.blit(text, text_rect)
            
            if button['subtitle']:
                sub = self.font_small.render(button['subtitle'], True, (200, 200, 200))
                sub_rect = sub.get_rect(center=(rect.centerx, rect.centery + 20))
                self.screen.blit(sub, sub_rect)
    
        pygame.display.flip()
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.selected_option = "QUIT"
            
            elif event.type == pygame.VIDEORESIZE:
                self.resize_UI(event.w, event.h)
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  
                    mouse_pos = pygame.mouse.get_pos()
                    
                    if self.name == "MAIN":
                        for key, button in self.buttons.items():
                            if button['rect'].collidepoint(mouse_pos):
                                if key == 'exit':
                                    self.selected_option = "QUIT"
                                else:
                                    self.selected_option = key.upper()
                                return
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.selected_option = "QUIT"
    
    def run_frame(self):
        self.draw()
        self.handle_events()
