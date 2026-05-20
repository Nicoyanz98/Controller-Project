import cv2

class CameraSystem():
    def __init__(self, window):
        self.window = window
        self.camera_connected = self.check_camera_connection()

    def check_camera_connection(self):
        self.cap = cv2.VideoCapture(0)

        if not self.cap.isOpened():
            self.window.notify_error("No camera connected")
            return False
            
        self.window.notify_success("Camera connected")
        return True
    
    def close(self):
        self.camera_connected = False
        self.cap.release()
    
    def is_camera_connected(self):
        self.camera_connected = self.check_camera_connection()
        return self.camera_connected

    def get_current_frame(self):
        ret, frame = self.cap.read()
        if ret:
            return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        else:
            self.camera_connected = False
            raise Exception("Lost camera connection")
        