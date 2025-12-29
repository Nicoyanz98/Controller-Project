import pygame
from config import AppConfig
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Renderer:
    def __init__(self, screen, app, title, states, button_files, sticks=False):
        self.screen = screen
        self.app = app
        
        self.title = title
        self.font = self.scaled_font(30)
        self.small_font = self.scaled_font(20)

        self.button_files = button_files
        self.button_states = states

        self.button_images_normal = self.load_button_images("normal")
        self.button_images_pressed = self.load_button_images("pressed")

        if sticks:
            self.stick_images_normal = self.load_stick_images("normal")
            self.stick_images_pressed = self.load_stick_images("pressed")

        self.button_rects = {}
        self.active_button = ''

    def scaled_font(self, size):
        scale = self.screen.get_width() / AppConfig.VIRTUAL_WIDTH
        font_size = int(size * scale)
        return pygame.font.Font(None, font_size)

    def load_button_images(self, state):
        #Carga todas imágenes de botones para el feedback visual
        button_images = {}
        
        folder = "pressed" if state == "pressed" else "normal"
        
        for button_name, filename in self.button_files.items():
            rel_path = f'assets/{folder}/{filename}'
            abs_path = os.path.join(BASE_DIR, rel_path)
            
            try:
                img = pygame.image.load(abs_path).convert_alpha()
                button_images[button_name] = pygame.transform.scale(img, (100, 100))
            except Exception as e:
                # Creo un rectángulo placeholder si no existe la imagen
                button_images[button_name] = pygame.Surface((100, 100), pygame.SRCALPHA)
                color = (100, 255, 100, 180) if state == "pressed" else (100, 100, 255, 180)
                pygame.draw.rect(button_images[button_name], color, (0, 0, 100, 100), border_radius=10)
                text_surface = self.small_font.render(button_name.split('_')[-1][:4], True, (255, 255, 255))
                text_rect = text_surface.get_rect(center=(50, 50))
                button_images[button_name].blit(text_surface, text_rect)
        
        return button_images

    def load_stick_images(self, state):
        stick_images = {}
        
        if state == "normal":
            positions = {
                'neutral':   'assets/sticks/normal/stick_center.png',
                'up':        'assets/sticks/normal/stick_up.png',
                'down':      'assets/sticks/normal/stick_down.png',
                'left':      'assets/sticks/normal/stick_left.png',
                'right':     'assets/sticks/normal/stick_right.png',
                'up_left':   'assets/sticks/normal/stick_up_left.png',
                'up_right':  'assets/sticks/normal/stick_up_right.png',
                'down_left': 'assets/sticks/normal/stick_down_left.png',
                'down_right':'assets/sticks/normal/stick_down_right.png'
            }
        else:  
            positions = {
                'neutral':   'assets/sticks/pressed/stick_center.png',
                'up':        'assets/sticks/pressed/stick_up.png',
                'down':      'assets/sticks/pressed/stick_down.png',
                'left':      'assets/sticks/pressed/stick_left.png',
                'right':     'assets/sticks/pressed/stick_right.png',
                'up_left':   'assets/sticks/pressed/stick_up_left.png',
                'up_right':  'assets/sticks/pressed/stick_up_right.png',
                'down_left': 'assets/sticks/pressed/stick_down_left.png',
                'down_right':'assets/sticks/pressed/stick_down_right.png'
            }
        
        for pos, rel_path in positions.items():
            abs_path = os.path.join(BASE_DIR, rel_path)
            try:
                stick_images[pos] = pygame.image.load(abs_path).convert_alpha()
                if stick_images[pos].get_size() != (60, 60):
                    stick_images[pos] = pygame.transform.scale(stick_images[pos], (60, 60))
            except:
                print(f"Error cargando: {abs_path}")
                stick_images[pos] = pygame.Surface((60, 60), pygame.SRCALPHA)
                if state == "normal":
                    pygame.draw.rect(stick_images[pos], (100, 100, 255, 128), (0, 0, 60, 60))
                else:
                    pygame.draw.rect(stick_images[pos], (255, 100, 100, 128), (0, 0, 60, 60))
        
        return stick_images

    def draw(self):
        self.screen.fill(AppConfig.BACKGROUND)
        self.draw_title()
        self.draw_camera_view()
        
        self.draw_buttons()

        self.draw_feedback()
        self.draw_button_pressed_feedback()
        pygame.display.flip()

    def draw_title(self):
        title = self.font.render(self.title, True, AppConfig.TEXT)
        self.screen.blit(title, (AppConfig.VIRTUAL_WIDTH // 2 - title.get_width() // 2, 20))

    def draw_buttons(self):
        raise NotImplementedError("Subclasses must implement this method.")
    
    def draw_camera_view(self):
        camera_frame = self.app.camera_system.get_frame()
        if camera_frame:
            frame_x = AppConfig.VIRTUAL_WIDTH // 2 - camera_frame.get_width() // 2
            frame_y = 60
            self.screen.blit(camera_frame, (frame_x, frame_y))
            
            pygame.draw.rect(self.screen, AppConfig.TEXT, 
                           (frame_x - 2, frame_y - 2, 
                            camera_frame.get_width() + 4, 
                            camera_frame.get_height() + 4), 2)
    
    def draw_feedback(self):
        feedback_status = self.app.camera_system.get_feedback_status()
        
        if feedback_status:
            # la esquina superior derecha
            x = AppConfig.VIRTUAL_WIDTH - 250
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
        for button_name, rect in self.button_rects.items():
            #Si colsiona un clickeado del mouse con un boton
            if rect.collidepoint(pos):
                #Desactivamos todos los botones
                for button in self.button_states:
                    self.button_states[button] = False

                #En caso que se pulsa el mismo boton, desactivarlo
                if button_name == self.active_button:
                    self.active_button = ''
                    return None, False

                #En caso de que se active otro boton,
                else:
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
        

        if button_img:
            # esquina superior izquierda
            x = 20
            y = 70
            
            bg_rect = pygame.Rect(x - 10, y - 10, 120, 150)
            bg_surface = pygame.Surface((120, 150), pygame.SRCALPHA)
            pygame.draw.rect(bg_surface, (40, 40, 40, 200), (0, 0, 120, 150), border_radius=15)
            self.screen.blit(bg_surface, (x - 10, y - 10))
            
            pygame.draw.rect(self.screen, border_color, (x - 10, y - 10, 120, 150), 3, border_radius=15)
            
            self.screen.blit(button_img, (x, y))
            
            button_label = self.gte_active_button_label(active_button)
            
            label_surface = self.small_font.render(button_label, True, AppConfig.TEXT)
            label_rect = label_surface.get_rect(center=(x + 50, y + 115))
            self.screen.blit(label_surface, label_rect)
            
            status_surface = self.small_font.render(status_text, True, text_color)
            status_rect = status_surface.get_rect(center=(x + 50, y + 135))
            self.screen.blit(status_surface, status_rect)

    def get_active_button_label(self, active_button):
        raise NotImplementedError("Subclasses must implement this method.")
    
    def get_active_button(self):
        return self.active_button

    def draw_gamepad_buttons(self, button_positions):
        camera_frame = self.app.camera_system.get_frame()
        
        # Posicionamos debajodel stick
        if camera_frame:
            start_y = 60 + camera_frame.get_height() + 30 + 90  
        else:
            start_y = 290

        buttons_title = self.font.render("Botones", True, AppConfig.TEXT)
        title_x = AppConfig.VIRTUAL_WIDTH // 2 - buttons_title.get_width() // 2
        self.screen.blit(buttons_title, (title_x, start_y - 30))

        button_size = 60
        button_spacing = 70
        total_width = (button_size * 4) + (button_spacing * 3)
        start_x = AppConfig.VIRTUAL_WIDTH // 2 - total_width // 2

        for i, button_name in enumerate(button_positions):
            if self.button_states[button_name]:
                button_img = self.button_images_pressed.get(button_name)
            else:
                button_img = self.button_images_normal.get(button_name)
            
            if button_img:
                # Escalamos imagen al tamaño del botón
                button_img_scaled = pygame.transform.scale(button_img, (button_size, button_size))
                
                x_pos = start_x + (i * (button_size + button_spacing))
                y_pos = start_y
                
                self.screen.blit(button_img_scaled, (x_pos, y_pos))

                if self.button_states[button_name]:
                    pygame.draw.rect(self.screen, AppConfig.SUCCESS, 
                                   (x_pos - 2, y_pos - 2, button_size + 4, button_size + 4), 3)
                
                # Guardar rect para clicks
                self.button_rects[button_name] = pygame.Rect(x_pos, y_pos, button_size, button_size)

    def draw_sticks_display(self):
        camera_frame = self.app.camera_system.get_frame()
        #Vemos posicion y
        if camera_frame:
            start_y = 60 + camera_frame.get_height() + 30  
        else:
            start_y = 200  

        #Vemos posicion x
        # Se Calcula posición horizontal centrada para los 9 sticks
        total_width = (60 * 9) + (10 * 8)  # 9 imágenes de 60px + 8 espacios de 10px
        start_x = AppConfig.VIRTUAL_WIDTH // 2 - total_width // 2


        sticks_title = self.font.render("Posiciones del Stick ", True, AppConfig.TEXT)
        title_x = AppConfig.VIRTUAL_WIDTH // 2 - sticks_title.get_width() // 2
        self.screen.blit(sticks_title, (title_x, start_y - 30))


        stick_positions = ['up_left', 'up', 'up_right',
                           'left', 'neutral', 'right', 
                           'down_left', 'down', 'down_right'
        ]

        for i, pos in enumerate(stick_positions):
            direction = pos
            stick_img = self.stick_images_pressed.get(pos) if self.button_states[f"stick_{self.name.lower()}_{pos}"] else self.stick_images_normal.get(pos)
                
            if stick_img:
                x_pos = start_x + (i * (60 + 10))  # 60px imagen + 10px espacio
                y_pos = start_y
                
                self.screen.blit(stick_img, (x_pos, y_pos))
                
                #Nos guardmaos las posiciones de los botones para luego ver las colisiones
                self.button_rects[f"stick_{self.name.lower()}_{pos}"] = pygame.Rect(x_pos, y_pos, 60, 60)

    def resize_by(self, width, height):
        pass