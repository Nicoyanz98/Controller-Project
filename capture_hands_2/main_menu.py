import pygame
import sys
from config import AppConfig
from camera_system import CameraSystem

class MainMenu:
    def __init__(self, camera_system=None):
        pygame.init()
        self.screen = pygame.display.set_mode((AppConfig.SCREEN_WIDTH, AppConfig.SCREEN_HEIGHT))
        pygame.display.set_caption("Captura de Gestos - Menú Principal")
        
        self.font_title = pygame.font.Font(None, 72)
        self.font_button = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 32)
        
        self.running = True
        self.selected_option = None
        self.camera_system = camera_system
        if self.camera_system is None:
            self.camera_system = CameraSystem()

        
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
        
        # posiciono botones
        center_x = AppConfig.SCREEN_WIDTH // 2
        start_y = 200
        spacing = 130
        
        for i, (key, button) in enumerate(self.buttons.items()):
            button['rect'].centerx = center_x
            button['rect'].y = start_y + (i * spacing)
    
    def draw(self):
        self.screen.fill(AppConfig.BACKGROUND)
        
        # Título
        title = self.font_title.render("Captura de Gestos", True, AppConfig.TEXT)
        title_rect = title.get_rect(center=(AppConfig.SCREEN_WIDTH // 2, 80))
        self.screen.blit(title, title_rect)
        
        # Subtítulo
        subtitle = self.font_small.render("Selecciona una sección para empezar", True, (200, 200, 200))
        subtitle_rect = subtitle.get_rect(center=(AppConfig.SCREEN_WIDTH // 2, 140))
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
                self.running = False
                self.selected_option = None
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  
                    mouse_pos = pygame.mouse.get_pos()
                    
                    for key, button in self.buttons.items():
                        if button['rect'].collidepoint(mouse_pos):
                            if key == 'exit':
                                self.running = False
                                self.selected_option = None
                            else:
                                self.selected_option = key
                                self.running = False
                            return
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                    self.selected_option = None
    
    def run(self):
        clock = pygame.time.Clock()
        
        while self.running:
            self.handle_events()
            self.draw()
            clock.tick(60)
        
        return self.selected_option


def main():
    shared_camera = CameraSystem()

    if not shared_camera.initialize():
        print("No se pudo inicializar la cámara")
        shared_camera = None

    while True:
        menu = MainMenu(camera_system=shared_camera)
        selected = menu.run()
        
        if selected is None:
            pygame.quit()
            sys.exit()
        
        elif selected == 'right':
            from app_right import GestureRecorderRight
            app = GestureRecorderRight(camera_system=shared_camera)
            app.run()
            
        elif selected == 'left':
            from app_left import GestureRecorderLeft
            app = GestureRecorderLeft(camera_system=shared_camera)
            app.run()
            
        elif selected == 'triggers':
            from app_triggers import GestureRecorderTriggers
            app = GestureRecorderTriggers(camera_system=shared_camera)
            app.run()


if __name__ == "__main__":
    main()