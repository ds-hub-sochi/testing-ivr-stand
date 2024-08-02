import time
import av
import socketio
import cv2
import base64
import json
import os
from dotenv import load_dotenv

# Загрузка переменных окружения из файла .env
load_dotenv()
host_socker_url = os.getenv('host_socker_url')
socker_path = os.getenv('socker_path')

# Создание клиента Socket.IO
sio = socketio.Client()
geasures = []

# Обработчик события подключения
@sio.event
def connect():
    global geasures
    geasures = []

# Обработчик события отключения
@sio.event
def disconnect():
    print(geasures)

# Обработчик события получения данных
@sio.on("send_not_normalize_text")
def receive_data(data):
    decoded_data = json.loads(data)
    for key in decoded_data:
        if decoded_data[key] not in geasures:
            geasures.append(decoded_data[key])
            break

# Функция отправки видео через сокет
def send_video(video_path):
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print("Error: Cannot open video file.")
        return

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Изменение размера кадра до 224x224 пикселей
        resized_frame = cv2.resize(frame, (224, 224))

        # Кодирование кадра в формат JPEG
        _, buffer = cv2.imencode('.jpg', resized_frame)
        image_data = base64.b64encode(buffer).decode('utf-8')
        sio.emit("data", f"data:image/jpeg;base64,{image_data}")
        cv2.waitKey(33)  # Ожидание 33 мс для отправки примерно 30 кадров в секунду

    time.sleep(4)
    cap.release()
    sio.disconnect()

# Функция отправки видео в формате RGB через сокет
def send_video_rgb(video_path):
    # Открытие видеофайла
    container = av.open(video_path)

    for frame in container.decode(video=0):
        # Переформатирование кадра до 224x224 и конвертация в формат RGB
        video_frame = frame.reformat(224, 224).to_ndarray(format="rgb24")

        # Кодирование кадра в формат JPEG
        _, buffer = cv2.imencode('.jpg', video_frame)
        image_data = base64.b64encode(buffer).decode('utf-8')
        sio.emit("data", f"data:image/jpeg;base64,{image_data}")

        # Ожидание для поддержания примерно 30 кадров в секунду
        cv2.waitKey(33)

    time.sleep(4)
    sio.disconnect()

# Функция обработки видеофайлов в папке
def process_videos_in_folder(folder_path):
    # Получение списка всех файлов в указанной папке
    video_files = [f for f in os.listdir(folder_path) if f.endswith('.mp4')]

    for video_file in video_files:
        video_path = os.path.join(folder_path, video_file)
        sio.connect(host_socker_url, socketio_path=socker_path)
        print('Processing video {}'.format(video_file), 'in default')
        send_video(video_path)
        time.sleep(2)
        sio.connect(host_socker_url, socketio_path=socker_path)
        print('Processing video {}'.format(video_file), 'in RGB')
        send_video_rgb(video_path)

    # Отключение после обработки всех видеофайлов
    sio.disconnect()

# Точка входа в программу
if __name__ == '__main__':
    folder_path = 'videos'
    process_videos_in_folder(folder_path)
