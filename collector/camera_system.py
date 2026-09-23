import cv2

class CameraSystem:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)

    def inform(self, message):
        print(message)

    def run(self, callback_fn=None):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break

            if callback_fn:
                callback_fn(frame)

            cv2.imshow('Camera Feed', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.cap.release()
        cv2.destroyAllWindows()