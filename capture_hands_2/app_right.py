import pygame
import sys
from config import AppConfig
from camera_system import CameraSystem
from event_handler import EventHandler
from renderer_right import RendererRight


class GestureRecorderRight:
    def __init__(self, camera_system):
        pygame.init()
        self.screen = pygame.display.set_mode((AppConfig.SCREEN_WIDTH, AppConfig.SCREEN_HEIGHT))
        pygame.display.set_caption("Captura de Gestos - Lado Derecho")
        
        self.camera_system = camera_system
        self.event_handler = EventHandler(self)
        self.renderer = RendererRight(self.screen, self)
        
        self.running = False
        self.recording = False
        self.frame_count = 0
    
    def initialize(self):        
        self.running = True
        return True
    
    def update(self):
        if self.recording:
            self.frame_count += 1
    
    def run(self):
        if not self.initialize():
            print("Error")
            return
        
        clock = pygame.time.Clock()
        
        while self.running:
            self.event_handler.process_events()
            self.update()
            self.renderer.draw()
            
            pygame.display.flip()
            clock.tick(AppConfig.FPS)
        
        self.cleanup()
    
    def cleanup(self):
        if self.camera_system.auto_capture:
        
            self.camera_system.auto_capture = False
            self.camera_system.frame_counter = 0