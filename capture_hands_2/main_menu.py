import pygame
from camera_system import CameraSystem
from main_menu_renderer import MainMenuRenderer
class MainMenu:
    def __init__(self, screen, camera_system=None):
        self.name = "MAIN"
        self.screen = screen

        self.selected_option = None

        self.renderer = MainMenuRenderer(self.screen, self, "Captura de Gestos - Menú Principal")
        
        pygame.display.set_caption("Captura de Gestos")
        self.camera_system = camera_system
        if self.camera_system is None:
            self.camera_system = CameraSystem()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.selected_option = "QUIT"
            
            elif event.type == pygame.VIDEORESIZE:
                self.renderer.resize_by(event.w, event.h)
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  
                    mouse_pos = pygame.mouse.get_pos()
                    
                    if self.name == "MAIN":
                        self.renderer.handle_click(mouse_pos)
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.selected_option = "QUIT"
    
    def run_frame(self):
        self.handle_events()
        self.renderer.draw()

