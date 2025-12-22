import pygame
from config import AppConfig
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class RendererTriggers:
    def __init__(self, screen, app):
        self.screen = screen
        self.app = app
        
        self.font = pygame.font.Font(None, 30)
        self.small_font = pygame.font.Font(None, 20)


        self.button_images_normal = self.load_button_images("normal")
        self.button_images_pressed = self.load_button_images("pressed")


        self.button_states = {
            # triggers solos
            'trigger_L': False,  # L2
            'trigger_R': False,  # R2
            'bumper_L': False,   # L1
            'bumper_R': False,   # R1
            
            # combinaciones L1 +
            'combo_L1_R1': False,
            'combo_L1_R2': False,
            'combo_L1_L2': False,
            
            # combinaciones L2 + 
            'combo_L2_R1': False,
            'combo_L2_R2': False,
            'combo_L2_L1': False,
            
            # combinaciones R1 + 
            'combo_R1_L1': False,
            'combo_R1_L2': False,
            'combo_R1_R2': False,
            
            # combinaciones R2 + 
            'combo_R2_L1': False,
            'combo_R2_L2': False,
            'combo_R2_R1': False,
        }

        self.button_rects = {}
        self.active_button = ''

    def get_active_button(self):
        return self.active_button

    
    def draw(self):
        self.screen.fill(AppConfig.BACKGROUND)
        self.draw_title()
        self.draw_camera_view()
        self.draw_individual_triggers()
        self.draw_combo_triggers()
        self.draw_feedback()
        self.draw_button_pressed_feedback()
        pygame.display.flip()

    
    def draw_title(self):
        title = self.font.render("Lado Izquierdo - Stick + Flechas", True, AppConfig.TEXT)
        self.screen.blit(title, (AppConfig.SCREEN_WIDTH // 2 - title.get_width() // 2, 20))
    
    def draw_camera_view(self):
        camera_frame = self.app.camera_system.get_frame()
        if camera_frame:
            frame_x = AppConfig.SCREEN_WIDTH // 2 - camera_frame.get_width() // 2
            frame_y = 60
            self.screen.blit(camera_frame, (frame_x, frame_y))
            
            pygame.draw.rect(self.screen, AppConfig.TEXT, 
                           (frame_x - 2, frame_y - 2, 
                            camera_frame.get_width() + 4, 
                            camera_frame.get_height() + 4), 2)


    def draw_individual_triggers(self):
        camera_frame = self.app.camera_system.get_frame()
        
        if camera_frame:
            start_y = 60 + camera_frame.get_height() + 30
        else:
            start_y = 200

        title = self.font.render("Triggers Individuales", True, AppConfig.TEXT)
        title_x = AppConfig.SCREEN_WIDTH // 2 - title.get_width() // 2
        self.screen.blit(title, (title_x, start_y - 30))

        button_positions = ['bumper_L', 'trigger_L', 'bumper_R', 'trigger_R']
        button_labels = ['L1', 'L2', 'R1', 'R2']
        
        button_size = 70
        button_spacing = 80
        total_width = (button_size * 4) + (button_spacing * 3)
        start_x = AppConfig.SCREEN_WIDTH // 2 - total_width // 2

        for i, (button_name, label) in enumerate(zip(button_positions, button_labels)):
            if self.button_states[button_name]:
                button_img = self.button_images_pressed.get(button_name)
            else:
                button_img = self.button_images_normal.get(button_name)
            
            if button_img:
                button_img_scaled = pygame.transform.scale(button_img, (button_size, button_size))
                
                x_pos = start_x + (i * (button_size + button_spacing))
                y_pos = start_y
                
                self.screen.blit(button_img_scaled, (x_pos, y_pos))

                if self.button_states[button_name]:
                    pygame.draw.rect(self.screen, AppConfig.SUCCESS, 
                                   (x_pos - 2, y_pos - 2, button_size + 4, button_size + 4), 3)
                
                self.button_rects[button_name] = pygame.Rect(x_pos, y_pos, button_size, button_size)
                
                label_surf = self.small_font.render(label, True, AppConfig.TEXT)
                label_rect = label_surf.get_rect(center=(x_pos + button_size // 2, y_pos + button_size + 15))
                self.screen.blit(label_surf, label_rect)



    def draw_combo_triggers(self):
       #Dibujamso combinaciones de triggers
        camera_frame = self.app.camera_system.get_frame()
        
        if camera_frame:
            start_y = 60 + camera_frame.get_height() + 10 + 120  
        else:
            start_y = 320


        combos = [
            # Fila 1: L1 + ...
            ['combo_L1_R1', 'combo_L1_R2', 'combo_L1_L2'],
            # Fila 2: L2 + ...
            ['combo_L2_R1', 'combo_L2_R2', 'combo_L2_L1'],
            # Fila 3: R1 + ...
            ['combo_R1_L1', 'combo_R1_L2', 'combo_R1_R2'],
            # Fila 4: R2 + ...
            ['combo_R2_L1', 'combo_R2_L2', 'combo_R2_R1'],
        ]
        
        combo_labels = {
            'combo_L1_R1': 'L1+R1',
            'combo_L1_R2': 'L1+R2',
            'combo_L1_L2': 'L1+L2',
            'combo_L2_R1': 'L2+R1',
            'combo_L2_R2': 'L2+R2',
            'combo_L2_L1': 'L2+L1',
            'combo_R1_L1': 'R1+L1',
            'combo_R1_L2': 'R1+L2',
            'combo_R1_R2': 'R1+R2',
            'combo_R2_L1': 'R2+L1',
            'combo_R2_L2': 'R2+L2',
            'combo_R2_R1': 'R2+R1',
        }

        button_size = 35
        button_spacing_x = 65
        button_spacing_y = 30
        
        for row_idx, row in enumerate(combos):
            total_width = (button_size * 3) + (button_spacing_x * 2)
            start_x = AppConfig.SCREEN_WIDTH // 2 - total_width // 2
            y_pos = start_y + (row_idx * button_spacing_y)
            
            for col_idx, combo_name in enumerate(row):
                x_pos = start_x + (col_idx * (button_size + button_spacing_x))
                

                if self.button_states[combo_name]:
                    color = (100, 200, 100)
                else:
                    color = (80, 80, 120)
                

                pygame.draw.rect(self.screen, color, (x_pos, y_pos, button_size, button_size), border_radius=8)
                pygame.draw.rect(self.screen, (255, 255, 255), (x_pos, y_pos, button_size, button_size), 2, border_radius=8)
                
                if self.button_states[combo_name]:
                    pygame.draw.rect(self.screen, AppConfig.SUCCESS, (x_pos - 2, y_pos - 2, button_size + 4, button_size + 4), 3, border_radius=8)
                
                label = combo_labels[combo_name]
                label_surf = self.small_font.render(label, True, AppConfig.TEXT)
                label_rect = label_surf.get_rect(center=(x_pos + button_size // 2, y_pos + button_size // 2))
                self.screen.blit(label_surf, label_rect)
                
                self.button_rects[combo_name] = pygame.Rect(x_pos, y_pos, button_size, button_size)
                

    

    def draw_feedback(self):
        feedback_status = self.app.camera_system.get_feedback_status()
        
        if feedback_status:
            # la esquina superior derecha
            x = AppConfig.SCREEN_WIDTH - 250
            y = 20
            
            if feedback_status == "success":
                pygame.draw.rect(self.screen, AppConfig.SUCCESS, (x, y, 230, 50), border_radius=10)
                pygame.draw.rect(self.screen, (255, 255, 255), (x, y, 230, 50), 2, border_radius=10)
                text = self.small_font.render("Foto guardada en el directorio", True, AppConfig.TEXT)
            else:  
                pygame.draw.rect(self.screen, AppConfig.WARNING, (x, y, 230, 50), border_radius=10)
                pygame.draw.rect(self.screen, (255, 255, 255), (x, y, 230, 50), 2, border_radius=10)
                text = self.small_font.render("Foto a carpeta basura", True, (30, 30, 30))
            
            self.screen.blit(text, (x + 15, y + 15))


    def handle_click(self, pos):

        def desactive_all_buttons():
            for button in self.button_states:
                self.button_states[button] = False


        for button_name, rect in self.button_rects.items():
            #Si colsiona un clickeado del mouse con un boton
            if rect.collidepoint(pos):

                #En caso que se pulsa el mismo boton, desactivarlo
                if button_name == self.active_button:
                    desactive_all_buttons()
                    self.active_button = ''
                    return None, False

                #En caso de que se active otro boton,
                else:
                    desactive_all_buttons()
                    self.button_states[button_name] = True #Activamos el boton
                    self.active_button = button_name
                    return button_name, True
        return None, None

    def draw_button_pressed_feedback(self):
        active_button = self.active_button
        
        if not active_button:
            return
        
        # Vemos si es el boton correcto
        is_pressing_correct = self.app.event_handler.is_pressing_correct_button(active_button)
        
        # Seleccionar la imagen correcta (normal o pressed)
        if is_pressing_correct:
            button_img = self.button_images_pressed.get(active_button)
            border_color = AppConfig.SUCCESS 
            status_text = "CORRECTO"
            text_color = AppConfig.SUCCESS
        else:
            button_img = self.button_images_normal.get(active_button)
            border_color = AppConfig.WARNING 
            status_text = "Presiona el botón"
            text_color = AppConfig.WARNING
        
        x = 20
        y = 70
        
        bg_surface = pygame.Surface((140, 120), pygame.SRCALPHA)
        pygame.draw.rect(bg_surface, (40, 40, 40, 200), (0, 0, 140, 120), border_radius=15)
        self.screen.blit(bg_surface, (x - 10, y - 10))
        
        pygame.draw.rect(self.screen, border_color, (x - 10, y - 10, 140, 120), 3, border_radius=15)
        
        button_label = active_button.replace('_', ' ').replace('combo ', '').replace('bumper', '').replace('trigger', '')
        
        if 'combo' in active_button:
            parts = active_button.replace('combo_', '').split('_')
            button_label = f"{parts[0]}+{parts[1]}"
        elif active_button == 'bumper_L':
            button_label = 'L1'
        elif active_button == 'bumper_R':
            button_label = 'R1'
        elif active_button == 'trigger_L':
            button_label = 'L2'
        elif active_button == 'trigger_R':
            button_label = 'R2'
        
        label_surface = self.font.render(button_label, True, AppConfig.TEXT)
        label_rect = label_surface.get_rect(center=(x + 60, y + 40))
        self.screen.blit(label_surface, label_rect)
        
        status_surface = self.small_font.render(status_text, True, text_color)
        status_rect = status_surface.get_rect(center=(x + 60, y + 80))
        self.screen.blit(status_surface, status_rect)


    def load_button_images(self, state):
        button_images = {}
        
        button_files = {
            'trigger_L': 'trigger_l2.png',
            'trigger_R': 'trigger_r2.png',
            'bumper_L': 'trigger_l1.png',
            'bumper_R': 'trigger_r1.png',
        }
        
        folder = "pressed" if state == "pressed" else "normal"
        
        for button_name, filename in button_files.items():
            rel_path = f'assets/{folder}/{filename}'
            abs_path = os.path.join(BASE_DIR, rel_path)
            
            try:
                img = pygame.image.load(abs_path).convert_alpha()
                button_images[button_name] = pygame.transform.scale(img, (100, 100))
            except:
                button_images[button_name] = pygame.Surface((100, 100), pygame.SRCALPHA)
                color = (100, 255, 100, 180) if state == "pressed" else (100, 100, 255, 180)
                pygame.draw.rect(button_images[button_name], color, (0, 0, 100, 100), border_radius=10)
                placeholder_font = pygame.font.Font(None, 24)
                text_surface = placeholder_font.render(button_name.split('_')[-1][:4], True, (255, 255, 255))
                text_rect = text_surface.get_rect(center=(50, 50))
                button_images[button_name].blit(text_surface, text_rect)
        
        return button_images