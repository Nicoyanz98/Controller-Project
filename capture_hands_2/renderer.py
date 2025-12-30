import pygame
from config import AppConfig
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Renderer:
    def __init__(self, screen, app, title, states, button_files, sticks=False):
        self.screen = screen
        self.app = app
        self.title = title
        self.button_files = button_files
        self.button_states = states
        self.draw_sticks = sticks

        self.button_rects = {}
        self.active_button = ''

        self.resize_by(self.screen.get_width(), self.screen.get_height())

    def resize_by(self, screen_width, screen_height):
        self.screen_size = (screen_width, screen_height)

        self.font = self.scaled_font(30)
        self.small_font = self.scaled_font(18)

        self.img_size = 60

        self.button_images_normal = self.load_button_images("normal")
        self.button_images_pressed = self.load_button_images("pressed")

        if self.draw_sticks:
            self.stick_images_normal = self.load_stick_images("normal")
            self.stick_images_pressed = self.load_stick_images("pressed")
        
        frame = self.app.camera_system.get_frame()
        if frame:
            new_camera_width = int(self.camera_scale * screen_width)
            new_camera_height = int(new_camera_width * (frame.get_width() / frame.get_height()))
            self.camera_rect = (screen_width // 2 - new_camera_width // 2, 50, new_camera_width, new_camera_height)
        else:
            self.camera_rect = (screen_width // 2, 50, 0, 0)
        
    def scaled_font(self, size):
        screen_width, screen_height = self.screen_size
        scale = screen_width / screen_height
        font_size = int(size * scale)
        return pygame.font.Font(None, font_size)

    def load_button_images(self, state):
        #Carga todas imágenes de botones para el feedback visual
        button_images = {}
        
        folder = "pressed" if state == "pressed" else "normal"

        width = height = self.img_size
        
        for button_name, filename in self.button_files.items():
            rel_path = f'assets/{folder}/{filename}'
            abs_path = os.path.join(BASE_DIR, rel_path)

            try:
                img = pygame.image.load(abs_path).convert_alpha()
                button_images[button_name] = pygame.transform.scale(img, (width, height))
            except Exception as e:
                # Creo un rectángulo placeholder si no existe la imagen
                button_images[button_name] = pygame.Surface((width, height), pygame.SRCALPHA)
                color = (100, 255, 100, 180) if state == "pressed" else (100, 100, 255, 180)
                pygame.draw.rect(button_images[button_name], color, (0, 0, width, height), border_radius=10)
                text_surface = self.small_font.render(button_name.split('_')[-1][:4], True, (255, 255, 255))
                text_rect = text_surface.get_rect(center=(width // 2, height // 2))
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
        
        width = height = self.img_size

        for pos, rel_path in positions.items():
            abs_path = os.path.join(BASE_DIR, rel_path)
            try:
                stick_images[pos] = pygame.image.load(abs_path).convert_alpha()
                if stick_images[pos].get_size() != (width, height):
                    stick_images[pos] = pygame.transform.scale(stick_images[pos], (width, height))
            except:
                print(f"Error cargando: {abs_path}")
                stick_images[pos] = pygame.Surface((width, height), pygame.SRCALPHA)
                if state == "normal":
                    pygame.draw.rect(stick_images[pos], (100, 100, 255, 128), (0, 0, width, height))
                else:
                    pygame.draw.rect(stick_images[pos], (255, 100, 100, 128), (0, 0, width, height))
        
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
        screen_width, _ = self.screen_size
        title = self.font.render(self.title, True, AppConfig.TEXT)
        self.screen.blit(title, (screen_width // 2 - title.get_width() // 2, 20))

    def draw_buttons(self, screen_size):
        raise NotImplementedError("Subclasses must implement this method.")
    
    def draw_camera_view(self):
        camera_frame = self.app.camera_system.get_frame()
        if camera_frame:
            frame_x, frame_y, camera_width, camera_height = self.camera_rect
            camera_frame = pygame.transform.scale(camera_frame, (camera_width, camera_height))

            self.screen.blit(camera_frame, (frame_x, frame_y))
            
            pygame.draw.rect(self.screen, AppConfig.TEXT, 
                           (frame_x - 2, frame_y - 2, 
                            camera_width + 4, 
                            camera_height + 4), 2)
    
    def draw_feedback(self):
        feedback_status = self.app.camera_system.get_feedback_status()

        screen_width, _ = self.screen_size
        
        if feedback_status:
            feedback_width = int(0.28 * screen_width)
            feedback_height = int(feedback_width * (50 / 230))

            # la esquina superior derecha
            x = int(screen_width * 0.02)
            y = 20
            

            feeback_rect = (x, y, feedback_width, feedback_height)
            color = AppConfig.WARNING
            msg_color = AppConfig.TEXT
            msg = "Foto a carpeta basura"
            if feedback_status == "success":
                color = AppConfig.SUCCESS
                msg_color = (30, 30, 30)
                msg = "Foto guardada en el directorio"
               
            pygame.draw.rect(self.screen, color, feeback_rect, border_radius=10)
            pygame.draw.rect(self.screen, (255, 255, 255), feeback_rect, 2, border_radius=10)
            text = self.small_font.render(msg, True, msg_color)
            
            self.screen.blit(text, (x + 5, y + feedback_height // 2 - text.get_height() // 2))
    
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
        
        screen_width, _ = self.screen_size

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
            x = int(0.04 * screen_width)
            y = 70

            button_feedback_width = int(0.15 * screen_width)
            button_feedback_height = int(button_feedback_width * (140 / 120))
            
            bg_rect = pygame.Rect(x, y, button_feedback_width, button_feedback_height)
            bg_surface = pygame.Surface((button_feedback_width, button_feedback_height), pygame.SRCALPHA)
            self.screen.blit(bg_surface, bg_rect)
            
            pygame.draw.rect(self.screen, border_color, bg_rect, 3, border_radius=15)

            img_width = int(0.8 * button_feedback_width)
            img_height = int(img_width * (button_img.get_height() / button_img.get_width()))
            scaled_button_img = pygame.transform.scale(button_img, (img_width, img_height))

            center_x = x + button_feedback_width // 2
            center_y = y + button_feedback_height // 2

            scaled_button_img_rect = scaled_button_img.get_rect(center=(center_x, center_y - int(0.05 * button_feedback_height)))
            self.screen.blit(scaled_button_img, scaled_button_img_rect)
            
            button_label = self.get_active_button_label(active_button)
            
            label_surface = self.small_font.render(button_label, True, AppConfig.TEXT)
            label_rect = label_surface.get_rect(center=(center_x, center_y + img_height // 2 + int(0.05 * button_feedback_height)))
            self.screen.blit(label_surface, label_rect)
            
            status_surface = self.small_font.render(status_text, True, text_color)
            status_rect = status_surface.get_rect(center=(center_x, center_y + button_feedback_height // 2 + int(0.1 * button_feedback_height)))
            self.screen.blit(status_surface, status_rect)

    def get_active_button_label(self, active_button):
        raise NotImplementedError("Subclasses must implement this method.")
    
    def get_active_button(self):
        return self.active_button

    def draw_gamepad_buttons(self, button_positions):
        screen_width, _ = self.screen_size
        _, camera_y, _, camera_height = self.camera_rect
        
        # Posicionamos debajodel stick
        button_size = int(0.07 * screen_width)
        button_spacing = int(0.0875 * screen_width)
        total_width = (button_size * 4) + (button_spacing * 3)
        start_x = screen_width // 2 - total_width // 2

        start_y = camera_height + camera_y + button_size + 40 * 2

        buttons_title = self.font.render("Botones", True, AppConfig.TEXT)
        title_x = screen_width // 2 - buttons_title.get_width() // 2
        self.screen.blit(buttons_title, (title_x, start_y - 30))

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
        screen_width, _ = self.screen_size
        _, camera_y, _, camera_height = self.camera_rect
        #Vemos posicion y
        start_y = camera_height + camera_y + 30

        #Vemos posicion x
        # Se Calcula posición horizontal centrada para los 9 sticks
        button_size = int(0.07 * screen_width)
        button_spacing = int(0.0125 * screen_width)
        total_width = (button_size * 9) + (button_spacing * 8)  # 9 imágenes de 60px + 8 espacios de 10px
        start_x = screen_width // 2 - total_width // 2

        sticks_title = self.font.render("Posiciones del Stick ", True, AppConfig.TEXT)
        title_x = screen_width // 2 - sticks_title.get_width() // 2
        self.screen.blit(sticks_title, (title_x, start_y - 30))

        stick_positions = ['up_left', 'up', 'up_right',
                           'left', 'neutral', 'right', 
                           'down_left', 'down', 'down_right'
        ]

        for i, pos in enumerate(stick_positions):
            button_name = f"stick_{self.name.lower()}_{pos}"
            stick_img = self.stick_images_pressed.get(pos) if self.button_states[button_name] else self.stick_images_normal.get(pos)
                
            if stick_img:
                x_pos = start_x + (i * (button_size + button_spacing))  # 60px imagen + 10px espacio
                y_pos = start_y
                
                self.screen.blit(stick_img, (x_pos, y_pos))

                if self.button_states[button_name]:
                    pygame.draw.rect(self.screen, AppConfig.SUCCESS, 
                                   (x_pos - 2, y_pos - 2, button_size + 4, button_size + 4), 3)
                
                #Nos guardmaos las posiciones de los botones para luego ver las colisiones
                self.button_rects[button_name] = pygame.Rect(x_pos, y_pos, button_size, button_size)