import pygame
from event_handler import EventHandler

class GestureRecorder:
    def __init__(self, name, window, renderer, camera_system):
        self.name = name
        self.screen = window
        pygame.display.set_caption("Captura de Gestos - " + name)
        
        self.camera_system = camera_system
        self.event_handler = EventHandler(self)
        self.renderer = renderer(self.screen, self)
        
        self.recording = False
        self.frame_count = 0

        self.selected_option = None
    
    def update(self):
        if self.recording:
            self.frame_count += 1
    
    def handle_resize(self, width, height):
        self.renderer.resize_by(width, height)
    
    def run_frame(self):
        self.event_handler.process_events()
        self.update()
        self.renderer.draw()
        
        pygame.display.flip()
    
    def cleanup(self):
        if self.camera_system.auto_capture:
            self.camera_system.auto_capture = False
            self.camera_system.frame_counter = 0