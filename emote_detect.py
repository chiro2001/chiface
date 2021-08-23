from base_logger import logger
import cv2
import dlib
import numpy as np
from actor import Actor


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
    def detect_faces(image: np.ndarray):
        height, width, channels = image.shape

        blob = cv2.dnn.blobFromImage(image, 1.0, (300, 300), [
                                     104, 117, 123], False, False)
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
                d = [x1, y1, x2, y2]
                # 适当调整发际线部分
                h = d[3] - d[1]
                d[1] += int(h * 0.15)
                faces.append(d)
        return faces


FaceDetection.load_models()
predictor_path = './shape_predictor_68_face_landmarks.dat'
predictor = dlib.shape_predictor(predictor_path)


def get_shapes(image: np.ndarray, faces: list = None) -> list:
    if faces is None:
        faces = FaceDetection.detect_faces(image)
    # print('faces', faces)
    shapes = []
    for face in faces:
        r = dlib.rectangle(*face)
        shape = predictor(image, r)
        shape = [(point.x, point.y) for point in shape.parts()]
        # print('shape', shape)
        shapes.append(np.array(shape))
    return shapes


class Emote:
    def __init__(self, args: dict = None) -> None:
        args = args if isinstance(args, dict) else {}
        # 0 ~ 1 表示打开程度
        self.eye = args.get('眼', 1.0)
        self.eyebrow = args.get('眉', 0.5)
        self.mouth = args.get('嘴', [0.5, 0])

    def __getstate__(self) -> dict:
        return self.__dict__

    @staticmethod
    def from_dict(data: dict):
        return Emote(data)

    def __str__(self) -> str:
        data = self.__getstate__()
        return f'{self.__class__.__name__}({", ".join([f"{key}={data[key]}" for key in data])})'

    def __repr__(self) -> str:
        return self.__str__()


class EmoteDetection:
    @staticmethod
    def parse_one(shape: np.ndarray, face: np.ndarray) -> Emote:
        # 首先标准化数据
        # d = np.array(shape.copy(), dtype=np.float)
        d = shape.copy() / 1.0
        # min_pos = (np.min([p[0] for p in d]), np.min([p[1] for p in d]))
        # max_pos = (np.max([p[0] for p in d]), np.max([p[1] for p in d]))
        min_pos = (face[0], face[1])
        max_pos = (face[2], face[3])
        for p in d:
            p -= min_pos
            p[0] /= max_pos[0] - min_pos[0]
            p[1] /= max_pos[1] - min_pos[1]
        e = Emote()
        e.eye = ((d[41] - d[37]) +
                 (d[40] - d[38]) +
                 (d[47] - d[43]) +
                 (d[46] - d[44]))[1]
        e.mouth[0] = (d[65] - d[59])[0]
        e.mouth[1] = ((d[67] - d[61]) +
                      (d[66] - d[62]) +
                      (d[65] - d[63]))[1]
        e.eyebrow = ((d[36] - d[18]) +
                     (d[37] - d[19]) +
                     (d[38] - d[20]) +
                     (d[39] - d[21]) +
                     (d[42] - d[22]) +
                     (d[43] - d[23]) +
                     (d[44] - d[24]) +
                     (d[45] - d[25]))[1]
        logger.debug(str(e))
        return e

    @staticmethod
    def parse(shapes: list, faces: list) -> list:
        return [EmoteDetection.parse_one(shape, faces[k]) for k, shape in enumerate(shapes)]

    @staticmethod
    def act(actor: Actor, emote: Emote):
        edges, adjust, orders = actor.edges, actor.adjust, actor.orders
        eye = emote.eye / adjust['眼']
        if eye > edges['眼']:
            actor.eye('开启')
        else:
            actor.eye('闭合')

        mouth = [emote.mouth[0] / adjust['嘴'][0],
                 emote.mouth[1] / adjust['嘴'][1]]
        if mouth[1] > edges['嘴'][1]:
            mouth_attr = '开启'
            actor.mouth(mouth_attr, '宽')
        else:
            mouth_attr = '闭合'
            if mouth[0] > edges['嘴'][0]:
                actor.mouth(mouth_attr, '宽')
            else:
                actor.mouth(mouth_attr, '窄')
        eyebrow = emote.eyebrow / adjust['眉']
        if eyebrow < edges['眉'][0]:
            actor.eyebrow('下')
        elif eyebrow < edges['眉'][1]:
            actor.eyebrow('中')
        else:
            actor.eyebrow('上')

