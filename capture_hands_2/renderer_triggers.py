import pygame
from config import AppConfig
import os
from renderer import Renderer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class RendererTriggers(Renderer):
    def __init__(self, screen, app):
        BUTTON_FILES = {
            'trigger_L': 'trigger_l2.png',
            'trigger_R': 'trigger_r2.png',
            'bumper_L': 'trigger_l1.png',
            'bumper_R': 'trigger_r1.png',
        }

        BUTTON_STATES = {
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

        super().__init__(screen, app, "Lado Superior - Triggers", BUTTON_STATES, BUTTON_FILES)

    def draw_buttons(self):
        self.draw_individual_triggers()
        self.draw_combo_triggers()
    
    def draw_individual_triggers(self):
        screen_width, _ = self.screen_size
        _, camera_y, _, camera_height = self.camera_rect
        start_y = camera_height + camera_y + 30

        button_size = int(0.07 * screen_width)
        button_spacing = int(0.0125 * screen_width)
        total_width = (button_size * 4) + (button_spacing * 3)
        start_x = screen_width // 2 - total_width // 2

        title = self.font.render("Triggers Individuales", True, AppConfig.TEXT)
        title_x = screen_width // 2 - title.get_width() // 2
        self.screen.blit(title, (title_x, start_y - 30))

        button_positions = ['bumper_L', 'trigger_L', 'bumper_R', 'trigger_R']
        button_labels = ['L1', 'L2', 'R1', 'R2']

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
        screen_width, screen_height = self.screen_size
        _, camera_y, _, camera_height = self.camera_rect
        
        # Posicionamos debajodel stick
        button_size = int(0.07 * screen_width)
        button_spacing_x = int(0.0875 * screen_width)
        total_width = (button_size * 4) + (button_spacing_x * 3)
        start_x = screen_width // 2 - total_width // 2

        start_y = camera_height + camera_y + button_size + 40 * 2


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

        button_spacing_y = int(0.0875 * screen_height)
        
        for row_idx, row in enumerate(combos):
            total_width = (button_size * 3) + (button_spacing_x * 2)
            start_x = screen_width // 2 - total_width // 2
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
    
    def get_active_button_label(self, active_button):
        button_label = ''
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
        return button_label