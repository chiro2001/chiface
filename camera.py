import cv2
import numpy as np

class Camera:
    def __init__(self, index: int = 0) -> None:
        self.index = index
        self.cap = None
    
    def open(self):
        self.cap = cv2.VideoCapture(self.index, cv2.CAP_DSHOW)
    
    def is_open(self) -> bool:
        return self.cap is None
    
    def read(self) -> np.ndarray:
        _, frame = self.cap.read()
        return frame

camera: Camera = Camera()