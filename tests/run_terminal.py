import cv2
from actor import Actor, actor, psd_default
from camera import Camera, camera
from emote_detect import get_shapes, FaceDetection, EmoteDetection

def main():
    actor.load(psd_default)
    camera.open()
    while True:
        frame = camera.read()
        faces = FaceDetection.detect_faces(frame)
        shapes = get_shapes(frame, faces=faces)
        emotes = EmoteDetection.parse(shapes[:1], faces)
        # print(emotes)
        for face in faces:
            cv2.rectangle(frame, face[0:2], face[2:4], (0, 0, 255), 2)
        for shape in shapes:
            for point in shape:
                cv2.circle(frame, point, 3, (0, 255, 0), -1)
        cv2.imshow("frame", frame)
        if len(emotes) == 1:
            emote = emotes[0]
            EmoteDetection.act(actor, emote)
            im = actor.get_image()
            cv2.imshow("im", im)
        key = chr(cv2.waitKey(1) & 0xFF)
        if key == 'q':
            break

if __name__ == '__main__':
    main()
