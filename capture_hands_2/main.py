import pygame
import sys
from config import AppConfig
from camera_system import CameraSystem
from main_menu import MainMenu

from gesture_recorder import GestureRecorder
from renderer_left import RendererLeft
from renderer_right import RendererRight
from renderer_triggers import RendererTriggers

def main():
    pygame.init()
    shared_camera = CameraSystem()

    clock = pygame.time.Clock()

    if not shared_camera.initialize():
        print("No se pudo inicializar la cámara")
        shared_camera = None

    window = pygame.display.set_mode((AppConfig.VIRTUAL_WIDTH, AppConfig.VIRTUAL_HEIGHT), pygame.RESIZABLE)
    menu = MainMenu(window, shared_camera)

    running = True
    while running:
        clock.tick(60)

        menu.run_frame()

        if menu.selected_option == "QUIT":
            if menu.name == "MAIN":
                running = False
            else:
                menu.cleanup()
                menu = MainMenu(window, shared_camera)
        
        elif menu.selected_option == "RIGHT":
            menu = GestureRecorder("RIGHT", window, RendererRight, shared_camera)
            
        elif menu.selected_option == 'LEFT':
            menu = GestureRecorder("LEFT", window, RendererLeft, shared_camera)
            
        elif menu.selected_option == 'TRIGGERS':
            menu = GestureRecorder("TRIGGERS", window, RendererTriggers, shared_camera)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()