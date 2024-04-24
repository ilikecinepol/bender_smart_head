import cv2
import os
from picamera2 import Picamera2
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
import threading
import time
import io
import serial

# Инициализируем каскадный классификатор для обнаружения лиц
face_cascade = cv2.CascadeClassifier("/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml")

# Инициализируем камеру
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (640, 480)}))
picam2.start()

# Инициализируем Serial порт
ser = serial.Serial('/dev/ttyUSB0', 9600)

# Определим центр экрана
screen_center_x = 640 // 2
screen_center_y = 480 // 2

class VideoStreamHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/video_feed':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    frame = picam2.capture_array()
                    # Поворачиваем изображение на 90 градусов по часовой стрелке
                    rotated_frame = rotate_image(frame, -90)
                    rotated_frame = detect_faces(rotated_frame)
                    ret, buffer = cv2.imencode('.jpg', rotated_frame)
                    frame_bytes = buffer.tobytes()
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame_bytes))
                    self.end_headers()
                    self.wfile.write(frame_bytes)
                    self.wfile.write(b'\r\n')
                    time.sleep(0.1)
            except Exception as e:
                print('Exception while streaming frames: %s' % str(e))
        else:
            self.send_error(404)
            self.end_headers()

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    pass

def rotate_image(image, angle):
    # Получаем размеры изображения
    (h, w) = image.shape[:2]
    # Определяем центр изображения
    center = (w // 2, h // 2)
    # Поворачиваем изображение на заданный угол
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated_image = cv2.warpAffine(image, M, (w, h))
    return rotated_image

def detect_faces(frame):
    # Преобразуем изображение в оттенки серого для обнаружения лиц
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Обнаруживаем лица на кадре
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    # Рисуем прямоугольные рамки вокруг обнаруженных лиц и вычисляем координаты их центров
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        center_x = x + w // 2
        center_y = y + h // 2
        cv2.circle(frame, (center_x, center_y), 5, (255, 0, 0), -1)
        # Вычисляем разницу между центром лица и центром экрана
        delta_x = center_x - screen_center_x
        delta_y = center_y - screen_center_y
        # Отправляем переменные delta_x и delta_y в Serial порт
        print(delta_x, delta_y)
        ser.write(f"{delta_x},{delta_y}\n".encode())
        time.sleep(0.1)
    return frame

PAGE = """\
<html>
<head>
<title>Face Detection Stream</title>
</head>
<body>
<h1>Face Detection Stream</h1>
<img src="/video_feed" width="640" height="480" />
</body>
</html>
"""

def main():
    global server
    global picam2
    global ser

    try:
        server = ThreadedHTTPServer(('0.0.0.0', 8000), VideoStreamHandler)
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        server.shutdown()
        server.server_close()
        picam2.stop()
        ser.close()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
