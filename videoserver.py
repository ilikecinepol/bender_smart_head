import cv2
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
picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (320, 240), "stride": 320 * 3}))  # Уменьшаем размер изображения и указываем правильный ключ конфигурации
picam2.start()

# Инициализируем Serial порт
ser = serial.Serial('/dev/ttyUSB0', 9600)

# Определим центр экрана
screen_center_x = 320 // 2  # Уменьшаем размер изображения
screen_center_y = 240 // 2  # Уменьшаем размер изображения

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
                    frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)  # Поворачиваем изображение на 90 градусов
                    frame = detect_faces(frame)
                    ret, buffer = cv2.imencode('.jpg', frame)
                    frame_bytes = buffer.tobytes()
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame_bytes))
                    self.end_headers()
                    self.wfile.write(frame_bytes)
                    self.wfile.write(b'\r\n')
                    time.sleep(0.05)  # Уменьшаем задержку между кадрами
            except Exception as e:
                print('Exception while streaming frames: %s' % str(e))
        else:
            self.send_error(404)
            self.end_headers()


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    pass


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
        try:
            ser.write(f"{delta_x},{delta_y}\n".encode())
        except Exception as e:
            print('error')
        time.sleep(0.05)  # Уменьшаем задержку между отправкой координат
    return frame


class StreamingServer:
    def __init__(self, server_class=ThreadedHTTPServer, handler_class=VideoStreamHandler, port=8000):
        self.server = server_class(('0.0.0.0', port), handler_class)

    def start(self):
        print('Starting server...')
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        print('Server started.')

    def stop(self):
        print('Stopping server...')
        self.server.shutdown()
        self.server.server_close()
        print('Server stopped.')


PAGE = """\
<html>
<head>
<title>Face Detection Stream</title>
</head>
<body>
<h1>Bender smart robot</h1>
<img src="/video_feed" width="320" height="240" />  <!-- Уменьшаем размер изображения -->
</body>
</html>
"""

try:
    server = StreamingServer()
    server.start()
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    server.stop()
    picam2.stop()
    ser.close()
    cv2.destroyAllWindows()




