import pygame
from config import AppConfig

class Renderer:
    def __init__(self, screen, app, title):
        self.screen = screen
        self.app = app
        self.title = title

        self.resize_by(self.screen.get_width(), self.screen.get_height())

    def resize_by(self, screen_width, screen_height):
        raise NotImplementedError("Subclasses must implement this method.")
        
    def scaled_font(self, size):
        screen_width, screen_height = self.screen_size
        scale = screen_width / screen_height
        font_size = int(size * scale)
        return pygame.font.Font(None, font_size)
    
    def draw(self):
        self.screen.fill(AppConfig.BACKGROUND)
        self.draw_app()
        pygame.display.flip()

    def draw_app(self):
        raise NotImplementedError("Subclasses must implement this method.")