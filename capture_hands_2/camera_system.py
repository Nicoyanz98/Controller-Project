import cv2
import pygame
import threading
import time
import queue
import os
from config import AppConfig


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class CameraSystem:
    def __init__(self):
        self.cap = None
        self.initialized = False
        self.current_frame = None
        
        # Sistema de hilos
        self.camera_thread = None
        self.running = False
        self.frame_queue = queue.Queue(maxsize=1)
        self.lock = threading.Lock()


        #Sistema de captura de imagenes
        self.auto_capture = False
        self.frame_capture_interval = 120  
        self.frame_counter = 0
        self.capture_count = 0

        self.capture_dir = os.path.join(BASE_DIR, "data")


        self.last_capture_status = None  
        self.last_capture_time = 0
        self.feedback_duration = 2.0 
    
    def initialize(self):
        #print("Cámara desactivada (temporal)")
        #self.initialized = True
        #return True
        try:
            print(f"Intentando inicializar cámara en índice {AppConfig.CAMERA_INDEX}...")
            print(f"Resolución objetivo: {AppConfig.CAMERA_WIDTH}x{AppConfig.CAMERA_HEIGHT}")
            
            self.cap = cv2.VideoCapture(0)
            self.cap.set(3, AppConfig.CAMERA_WIDTH)   
            self.cap.set(4, AppConfig.CAMERA_HEIGHT) 
            self.cap.set(5, 60)
            
            actual_fps = self.cap.get(5)
            print(f"FPS de cámara: {actual_fps}")
            
            # Iniciar hilo de cámara
            self.running = True
            self.camera_thread = threading.Thread(target=self._camera_loop, daemon=True)
            self.camera_thread.start()
            
            self.initialized = True
            print("Cámara inicializada correctamente con hilo separado")
            return True
            
        except Exception as e:
            self.error_message = f"Error al inicializar cámara: {str(e)}"
            print(self.error_message)
            return False
    
    def _camera_loop(self):
        """Hilo separado para capturar frames de la cámara"""
        print("Hilo de cámara iniciado")
        frame_count = 0
        start_time = time.time()
        error_count = 0
        
        while self.running and error_count < 10:  
            try:
                ret, frame = self.cap.read()
                if not ret:
                    error_count += 1
                    print(f"Error capturando frame ({error_count}/10)")
                    time.sleep(0.01)
                    continue
                
                error_count = 0  
                
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Redimensionamox
                if (frame_rgb.shape[1] != AppConfig.CAMERA_WIDTH or 
                    frame_rgb.shape[0] != AppConfig.CAMERA_HEIGHT):
                    frame_rgb = cv2.resize(frame_rgb, (AppConfig.CAMERA_WIDTH, AppConfig.CAMERA_HEIGHT))
                
                # Convertimos a superficie de PyGame
                frame_surface = pygame.image.frombuffer(frame_rgb.tobytes(), (AppConfig.CAMERA_WIDTH, AppConfig.CAMERA_HEIGHT), "RGB")

                if self.auto_capture:
                    self.frame_counter += 1
                    if self.frame_counter >= self.frame_capture_interval:
                        self.take_capture(frame_rgb)
                        self.frame_counter = 0
                
                # Ponemos el frame en la cola
                if not self.frame_queue.empty():
                    try:
                        self.frame_queue.get_nowait()
                    except queue.Empty:
                        pass
                
                self.frame_queue.put(frame_surface)
                
                
                frame_count += 1
                if frame_count % 100 == 0:
                    elapsed = time.time() - start_time
                    fps = frame_count / elapsed
                    print(f"📷 FPS de cámara: {fps:.1f}")
                    
            except Exception as e:
                error_count += 1
                print(f"Error en hilo de cámara ({error_count}/10): {e}")
                time.sleep(0.01)
    
    def get_frame(self):
        try:
            if not self.frame_queue.empty():
                self.current_frame = self.frame_queue.get_nowait()
                return self.current_frame
            return self.current_frame 
        except queue.Empty:
            return self.current_frame
        
    def get_feedback_status(self):
        if self.last_capture_status and (time.time() - self.last_capture_time < self.feedback_duration):
            return self.last_capture_status
        return None
        

    def take_capture(self, frame_rgb):
        try:
            # Verificamos que el directorio existe (por si acaso)
            os.makedirs(self.capture_dir, exist_ok=True)
        
            # Contamos los archivos JPG en el directorio
            pic_count = len([pic for pic in os.listdir(self.capture_dir) if pic.endswith('.jpg')])

            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"{self.capture_dir}/{pic_count}_{self.capture_dir}_{timestamp}.jpg"
            frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
            cv2.imwrite(filename, frame_bgr)

            if "basura" in self.capture_dir:
                self.last_capture_status = "trash"
                print(f"🗑️ Captura enviada a BASURA: {filename}")
            else:
                self.last_capture_status = "success"
                print(f"✅ Captura guardada correctamente: {filename}")

            self.last_capture_time = time.time()
            
        except Exception as e:
            print(f"Error en captura automática: {e}")


    def toggle_auto_capture(self, button_name):
        was_active = self.auto_capture
        self.auto_capture = not self.auto_capture

        if self.auto_capture:
            self.capture_dir = os.path.join(BASE_DIR, "data", button_name)
            os.makedirs(self.capture_dir, exist_ok=True)

            if not was_active:
                self.frame_counter = 0
                print(f"Captura automática ACTIVADA")

        else:
            print(f"Captura automática DESACTIVADA")
            self.frame_counter = 0 
        return self.auto_capture
    
    def set_current_directory(self, directory):
        self.capture_dir = os.path.join(BASE_DIR, "data", directory)
        os.makedirs(self.capture_dir, exist_ok=True)
        os.makedirs(self.capture_dir, exist_ok=True)


    def change_capture_button(self, button_name):
        if self.auto_capture:
            self.capture_dir = os.path.join(BASE_DIR, "data", button_name)
            os.makedirs(self.capture_dir, exist_ok=True)
            print(f"Cambiado a: {button_name}")
    