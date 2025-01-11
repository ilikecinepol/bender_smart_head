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
picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (320, 240)}))  # Уменьшаем размер изображения
picam2.start()

# Инициализируем Serial порт для связи с Arduino
ser = serial.Serial('/dev/ttyUSB0', 9600)

# Время, через которое глаза возвращаются в центральное положение (4 секунды)
last_face_time = time.time()

# Функция для отправки команд на Arduino
def send_to_arduino(center_x, center_y):
    """
    Отправляем координаты центра лица в Arduino через Serial порт.
    """
    try:
        data = f"{center_x},{center_y}\n"
        ser.write(data.encode())
        print(f"Sent to Arduino: {data.strip()}")

        # Ожидаем обратной связи от Arduino
        if ser.in_waiting > 0:
            response = ser.readline().decode('utf-8').strip()
            print(f"Received from Arduino: {response}")
    except Exception as e:
        print(f"Error sending data to Arduino: {e}")

# Функция для обработки видеопотока
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

# Функция для обнаружения лиц
def detect_faces(frame):
    global last_face_time

    # Преобразуем изображение в оттенки серого для обнаружения лиц
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Обнаруживаем лица на кадре
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    # Если лицо найдено, обновляем время
    if len(faces) > 0:
        last_face_time = time.time()
        # Рисуем прямоугольные рамки вокруг обнаруженных лиц и вычисляем координаты их центров
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            center_x = x + w // 2
            center_y = y + h // 2
            cv2.circle(frame, (center_x, center_y), 5, (255, 0, 0), -1)

            # Отправляем координаты центра лица в Serial порт
            send_to_arduino(center_x, center_y)

    else:
        # Если лицо не найдено и прошло больше 4 секунд, возвращаем глаза в центр
        if time.time() - last_face_time > 4:
            print("No face detected for 4 seconds, returning eyes to center.")
            send_to_arduino(160, 120)  # Отправляем центральные координаты для глаз (например, 160, 120)

    return frame

# Функция для запуска видеопотока
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
<h1>Face Detection Stream</h1>
<img src="/video_feed" width="320" height="240" />  <!-- Уменьшаем размер изображения -->
</body>
</html>
"""

# Запуск сервера
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
