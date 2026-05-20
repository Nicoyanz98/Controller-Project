import cv2, os, time

class CameraSystem():
    def __init__(self, window, dir_path):
        self.data_dir = os.path.join(dir_path, "data")
        self.window = window
        self.camera_connected = self._check_camera_connection()

    def _check_camera_connection(self):
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
        self.camera_connected = self._check_camera_connection()
        return self.camera_connected

    def get_current_frame(self):
        ret, frame = self.cap.read()
        if ret:
            return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        else:
            self.camera_connected = False
            raise Exception("Lost camera connection")
        
    def save_current_frame(self, frame_name):
        capture_dir = os.path.join(self.data_dir, frame_name)
        try:
            os.makedirs(capture_dir, exist_ok=True)
            pic_count = len([pic for pic in os.listdir(capture_dir) if pic.endswith('.jpg')])

            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"{capture_dir}/{pic_count}_{capture_dir}_{timestamp}.jpg"
            frame = self.get_current_frame()
            cv2.imwrite(filename, frame)

            capture_msg = f"Frame saved at: {filename}"
            if "trash" == frame_name:
                self.window.notify_warning(capture_msg)
            else:
                self.window.notify_success(capture_msg)

        except Exception as e:
            self.window.notify_error(f"Failure during saving: {e}")