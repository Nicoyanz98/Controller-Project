import pygame


class EventHandler:
    def __init__(self, app):
        self.app = app

        self.joystick = None
        self.init_joystick()


    def update_joystick(self):
        if self.joystick:
            pygame.joystick.Joystick(0).init() 
            pygame.event.pump()


    def init_joystick(self):
       
        pygame.joystick.init()
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            print(f"Joystick conectado: {self.joystick.get_name()}")
            print(f"Botones disponibles: {self.joystick.get_numbuttons()}")
        else:
            print("No se encontró joystick/gamepad")

    def is_button_pressed(self, button_name):
        if not self.joystick:
            return False
        
        if button_name == "trigger_L": 
            try:
                axis_value = self.joystick.get_axis(4)  
                return axis_value > 0.5 
            except:
                if self.joystick.get_numbuttons() > 6:
                    return self.joystick.get_button(6) == 1
                return False
        
        elif button_name == "trigger_R":  

            try:
                axis_value = self.joystick.get_axis(5)  
                return axis_value > 0.5  
            except:

                if self.joystick.get_numbuttons() > 7:
                    return self.joystick.get_button(7) == 1
                return False

       
        button_map = {
            "button_A": 0,     # Botón A (Xbox) / X (PlayStation)
            "button_B": 1,     # Botón B (Xbox) / Círculo (PlayStation)
            "button_X": 2,     # Botón X (Xbox) / Cuadrado (PlayStation)
            "button_Y": 3,     # Botón Y (Xbox) / Triángulo (PlayStation)
            "bumper_L": 4,     # LB (Xbox) / L1 (PlayStation)
            "bumper_R": 5,     # RB (Xbox) / R1 (PlayStation)
        }
        
        button_index = button_map.get(button_name)
        if button_index is not None and button_index < self.joystick.get_numbuttons():
            return self.joystick.get_button(button_index) == 1
        
        return False
    

    def get_dpad_direction(self):
        #Parte del gamepad izquierdo
        if not self.joystick:
            return None
        
        if self.joystick.get_numhats() < 1:
            return None
        
        hat = self.joystick.get_hat(0)
        # x: -1 = izquierda, 0 = centro, 1 = derecha
        # y: -1 = abajo, 0 = centro, 1 = arriba
        
        x, y = hat
        
        # Mapear ampeamos direcciones
        if y == 1 and x == 0:
            return 'up'
        elif y == -1 and x == 0:
            return 'down'
        elif x == -1 and y == 0:
            return 'left'
        elif x == 1 and y == 0:
            return 'right'
        else:
            return None  # Neutral o diagonal
        
    def is_dpad_pressed(self, direction):
        current_direction = self.get_dpad_direction()
        return current_direction == direction




    def get_stick_direction_9_way(self, stick_name):

        #Usamos (x,y) y cambia segun el stick
        axis_map = {
        "stick_left": (0, 1), #
        "stick_right": (2, 3)
        }

        #Vemos de cual se stick se trata y obtenemos sus valores
        x_axis, y_axis = axis_map[stick_name]
        x_value = self.joystick.get_axis(x_axis)
        y_value = self.joystick.get_axis(y_axis)


        threshold = 0.2

        #Vemos el valor de la psoicion y la pasamos a {1;0;-1}
        x_dir = 0 if abs(x_value) < threshold else (1 if x_value > 0 else -1)
        y_dir = 0 if abs(y_value) < threshold else (1 if y_value > 0 else -1)

        #Mapeamos las direcciones posibles
        directions = {
        (0, 0): "neutral",
        (1, 0): "right",
        (-1, 0): "left", 
        (0, -1): "up",     
        (0, 1): "down",    
        (1, -1): "up_right",
        (-1, -1): "up_left",
        (1, 1): "down_right",
        (-1, 1): "down_left"
        }

        
        return directions.get((x_dir, y_dir))
    
    def is_stick_in_direction(self, stick_name, direction):
   
        current_direction = self.get_stick_direction_9_way(stick_name)
        return current_direction == direction
    

    def is_pressing_correct_button(self, button_name):
        if not button_name:
            return False
        
        if not self.joystick:
            return False
        
        #Caso sticks
        if button_name.startswith(('stick_right_', 'stick_left_')):
            direction = button_name.replace("stick_right_", "").replace("stick_left_", "")
            stick_name_only = 'stick_right' if 'stick_right' in button_name else 'stick_left'
            return self.is_stick_in_direction(stick_name_only, direction)
        
        #Caso triggers
        elif button_name.startswith('combo_'):
            # Extraemos los dos botones de la combinación
            # combo_L1_R1 -> ['L1', 'R1']
            parts = button_name.replace('combo_', '').split('_')
            if len(parts) == 2:
                button1 = parts[0]  
                button2 = parts[1]  
                
                button_map = {
                    'L1': 'bumper_L',
                    'L2': 'trigger_L',
                    'R1': 'bumper_R',
                    'R2': 'trigger_R'
                }
                
                tech_button1 = button_map.get(button1)
                tech_button2 = button_map.get(button2)
                
                # Verifiamos ambos presionados
                return (self.is_button_pressed(tech_button1) and self.is_button_pressed(tech_button2))
            return False



        
        #Caso d-pad y gamepad derecho
        elif button_name.startswith('dpad_') or button_name.startswith('button_'):
            if button_name == 'button_UP':
                return self.is_dpad_pressed('up')
            elif button_name == 'button_DOWN':
                return self.is_dpad_pressed('down')
            elif button_name == 'button_LEFT':
                return self.is_dpad_pressed('left')
            elif button_name == 'button_RIGHT':
                return self.is_dpad_pressed('right')
            else:
                return self.is_button_pressed(button_name)
            
        #Triggers indiviaudales
        elif button_name in ['trigger_L', 'trigger_R', 'bumper_L', 'bumper_R']:
            return self.is_button_pressed(button_name)

        # otros botones
        else:
            return self.is_button_pressed(button_name)


    
    def process_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.app.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.handle_mouse_click(event)

        self.update_joystick()
        self.update_active_button()
        

    def get_capture_directory_for_active(self, button_name):

        #cASO STICKS
        if button_name.startswith(('stick_right_', 'stick_left_')):
            direction =  button_name.replace("stick_right_", "").replace("stick_left_", "")
            stick_name = 'stick_right' if 'stick_right' in button_name else 'stick_left'

            current_direction = self.get_stick_direction_9_way(stick_name)

            if current_direction == direction:
                return f"{stick_name}_{direction}"
            else:
                return "basura"

        #Triggers
        elif button_name.startswith('combo_'):
            if self.is_pressing_correct_button(button_name):
                return button_name 
            else:
                return "basura"


        # CASO D-Pad o gamepad derecho
        elif button_name.startswith('button_'):
            if button_name in ['button_UP', 'button_DOWN', 'button_LEFT', 'button_RIGHT']:
                direction_map = {
                    'button_UP': 'up',
                    'button_DOWN': 'down',
                    'button_LEFT': 'left',
                    'button_RIGHT': 'right'
                }
                expected_direction = direction_map[button_name]
                current_direction = self.get_dpad_direction()
                
                if current_direction == expected_direction:
                    return f"dpad_{expected_direction}"
                else:
                    return "basura"
            else:
                if self.is_button_pressed(button_name):
                    return button_name
                else:
                    return "basura"

        #Triggers indiviadules
        elif button_name in ['trigger_L', 'trigger_R', 'bumper_L', 'bumper_R']:
            if self.is_button_pressed(button_name):
                return button_name
            else:
                return "basura"


        #Otros botones
        else:
            if self.is_button_pressed(button_name):
                return button_name
            else:
                return "basura"


    def update_active_button(self):
        active = self.app.renderer.get_active_button()
        if not active:
            return

        directory = self.get_capture_directory_for_active(active)
        self.app.camera_system.set_current_directory(directory)

    
    def handle_mouse_click(self, event):
        if event.button == 1:  
            mouse_pos = pygame.mouse.get_pos()
         
            button_name, state = self.app.renderer.handle_click(mouse_pos)

            # Activar un botón nuevo
            if button_name and state:
                if self.app.camera_system.auto_capture:
                    print(f"Cambiando de botón")
                    self.app.camera_system.change_capture_button(button_name)

                else:
                    print(f"ACTIVANDO captura")
                    self.app.camera_system.toggle_auto_capture(button_name)

            #Desactivar el botón actual (click en mismo botón)
            elif not button_name and state is False:
                if self.app.camera_system.auto_capture:
                    print(f"DESACTIVANDO captura")
                    self.app.camera_system.toggle_auto_capture("")

            