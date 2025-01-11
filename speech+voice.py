import pyaudio
import vosk
import json
from yandexgptlite import YandexGPTLite
import os
import requests
from pydub import AudioSegment
from pydub.playback import play
from dotenv import load_dotenv
import itertools
import threading
import time

# Загрузка переменных окружения
load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
YANDEX_API_KEY_1 = os.getenv("YANDEX_API_KEY_1")
YANDEX_API_KEY_2 = os.getenv("YANDEX_API_KEY_2")
MODEL_PATH = os.getenv("MODEL_PATH", "vosk-model")
LOADING_SPINNER_SYMBOLS = os.getenv("LOADING_SPINNER_SYMBOLS", "|,/,\\,-").split(",")
LOADING_SPEED = float(os.getenv("LOADING_SPEED", 0.1))

if not ELEVENLABS_API_KEY or not YANDEX_API_KEY_1 or not YANDEX_API_KEY_2:
    raise Exception("API ключи не найдены. Проверьте файл .env.")

HEADERS = {
    "Accept": "audio/mpeg",
    "Content-Type": "application/json",
    "xi-api-key": ELEVENLABS_API_KEY,
}

model = vosk.Model(MODEL_PATH)
rec = vosk.KaldiRecognizer(model, 44100)
account = YandexGPTLite(YANDEX_API_KEY_1, YANDEX_API_KEY_2)

def loading_spinner(stop_event):
    for symbol in itertools.cycle(LOADING_SPINNER_SYMBOLS):
        if stop_event.is_set():
            break
        print(f"\rОбработка... {symbol}", end="", flush=True)
        time.sleep(LOADING_SPEED)
    print("\rОбработка завершена!   ", flush=True)

def generate_voice(text):
    url = "https://api.elevenlabs.io/v1/text-to-speech/WYdgUKpu35hxv59yCeG3"
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.8,
            "style": 0.67,
            "use_speaker_boost": True
        }
    }

    response = requests.post(url, headers=HEADERS, json=data)
    if response.status_code == 200:
        mp3_path = "response.mp3"
        with open(mp3_path, "wb") as f:
            f.write(response.content)

        audio = AudioSegment.from_mp3(mp3_path)
        audio.export("response.wav", format="wav")
        return "response.wav"
    else:
        print(f"Ошибка: {response.status_code}")
        return None

def play_audio(file_path):
    audio = AudioSegment.from_file(file_path, format="wav")
    play(audio)

def process_microphone_input():
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100

    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

    print("* Начало записи...")

    conversation_history = []  # Хранение истории диалога
    last_bot_reply = ""  # Последний ответ ассистента

    while True:
        data = stream.read(CHUNK)
        if len(data) == 0:
            break

        if rec.AcceptWaveform(data):
            result = rec.Result()
            result_dict = json.loads(result)
            user_input = result_dict.get('text', '').strip()  # Текст пользователя
            if not user_input or user_input == last_bot_reply.lower():
                continue  # Пропуск, если текст совпадает с последним ответом бота

            print(f"👨‍💻 Пользователь: {user_input}")
            conversation_history.append(f"Пользователь: {user_input}")

            system_prompt = f"Мы ведем разговор, в котором я играю роль робота Бендера. История разговора:\n"
            for message in conversation_history[-6:]:
                system_prompt += f"{message}\n"
            system_prompt += "Ответь как Бендер из м/ф 'Футурама'."

            stop_event = threading.Event()
            spinner_thread = threading.Thread(target=loading_spinner, args=(stop_event,))
            spinner_thread.start()

            try:
                answer = account.create_completion(user_input, '0.9', system_prompt=system_prompt)
            finally:
                stop_event.set()
                spinner_thread.join()

            print(f"🤖 Бендер: {answer}")
            conversation_history.append(f"Бендер: {answer}")
            last_bot_reply = answer  # Сохранение последнего ответа ассистента

            # Отключение микрофона во время воспроизведения ответа
            stream.stop_stream()
            audio_file = generate_voice(answer)
            if audio_file:
                play_audio(audio_file)
            stream.start_stream()  # Включение микрофона после воспроизведения

    print("* Запись завершена")
    stream.stop_stream()
    stream.close()
    p.terminate()

if __name__ == "__main__":
    process_microphone_input()
