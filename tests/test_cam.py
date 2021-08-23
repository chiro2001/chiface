import cv2
import os
import time
import sys
import dlib
import numpy as np

class FaceDetection:
    verification_threshold = 0.8
    net = None
    image_size = 160

    def __init__(self):
        FaceDetection.load_models()

    @staticmethod
    def load_models():
        if not FaceDetection.net:
            FaceDetection.net = FaceDetection.load_opencv()

    @staticmethod
    def load_opencv():
        model_path = "./models/OpenCV/opencv_face_detector_uint8.pb"
        model_pbtxt = "./models/OpenCV/opencv_face_detector.pbtxt"
        net = cv2.dnn.readNetFromTensorflow(model_path, model_pbtxt)
        return net

    @staticmethod
    def is_same(emb1, emb2):
        diff = np.subtract(emb1, emb2)
        diff = np.sum(np.square(diff))
        return diff < FaceDetection.verification_threshold, diff

    @staticmethod
    def detect_faces(image, display_images=False): # Make display_image to True to manually debug if you run into errors
        height, width, channels = image.shape

        blob = cv2.dnn.blobFromImage(image, 1.0, (300, 300), [104, 117, 123], False, False)
        FaceDetection.net.setInput(blob)
        detections = FaceDetection.net.forward()

        faces = []

        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            if confidence > 0.5:
                x1 = int(detections[0, 0, i, 3] * width)
                y1 = int(detections[0, 0, i, 4] * height)
                x2 = int(detections[0, 0, i, 5] * width)
                y2 = int(detections[0, 0, i, 6] * height)
                # faces.append([x1, y1, x2 - x1, y2 - y1])
                faces.append([x1, y1, x2, y2])

                if display_images:
                    cv2.rectangle(image, (x1, y1), (x2, y2), (255, 0, 0), 3)
    
        if display_images:
            print("Face co-ordinates: ", faces)
            # cv2.imshow("Training Face", cv2.resize(image, (300, 300)))
            cv2.imshow("Training Face", image)
            # cv2.waitKey(0)
        return faces


def test():
    FaceDetection.load_models()
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    predictor_path = './shape_predictor_68_face_landmarks.dat'
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(predictor_path)
    times = []
    while True:
        times.append(time.time())
        _, frame = cap.read()
        times.append(time.time())
        # dets2 = detector(frame, 1)
        dets = FaceDetection.detect_faces(frame, display_images=False)
        times.append(time.time())
        # print("Number of faces detected: {}".format(len(dets)))
        for k, d in enumerate(dets):
            # print("Detection {}: Left: {} Top: {} Right: {} Bottom: {}".format(
                # k, d.left(), d.top(), d.right(), d.bottom()))
            # try:
            #     d2 = dets2[k]
            #     cv2.rectangle(frame, (d2.left(), d2.top()), (d2.right(), d2.bottom()), (255, 0, 0), 2)
            # except Exception as e:
            #     print(e)
            height = d[3] - d[1]
            d[1] += int(height * 0.15)
            cv2.rectangle(frame, d[0:2], d[2:4], (0, 0, 255), 2)
            r = dlib.rectangle(*d)
            # print(d, r)
            shape = predictor(frame, r)
            # shape = predictor(frame, (0, 0, frame.shape[0], frame.shape[1]))
            for point in shape.parts():
                cv2.circle(frame, (point.x, point.y), 3, (0, 255, 0), -1)
        times.append(time.time())
        cv2.imshow("camera", frame)
        times.append(time.time())
        # deltas = [times[i + 1] - times[i] for i in range(len(times) - 1)]
        # print(deltas)
        times = []
        key = chr(cv2.waitKey(1) & 0xFF)
        if key == 'q':
            # sys.exit(0)
            break
    cv2.destroyAllWindows()

if __name__ == '__main__':
    test()
