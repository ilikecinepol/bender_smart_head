import pyaudio
import vosk
import json
from yandexgptlite import YandexGPTLite
import subprocess

MODEL_PATH = "vosk-model-small-ru-0.22"

# Инициализация модели Vosk
model = vosk.Model(MODEL_PATH)
rec = vosk.KaldiRecognizer(model, 44100)

# Подключаемся к Яндекс
account = YandexGPTLite('**********', '***********' )

# Функция для обработки аудио из микрофона
def process_microphone_input():
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100

    p = pyaudio.PyAudio()

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("* Recording audio...")

    while True:
        data = stream.read(CHUNK)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            result = rec.Result()
            result_dict = json.loads(result)
            promt = result_dict['text']
            print(promt)
            answer = account.create_completion(promt, '0.6', system_prompt='Разговаривай как робот Бендер из м/ф Футурама')
            print(answer) #Sounds good!

            command = 'echo %s | spd-say -o rhvoice -l ru -e -t male1' % str(answer)
            # subprocess.run(command, shell=True)

    print("* Recording finished")

    stream.stop_stream()
    stream.close()
    p.terminate()

# Запуск обработки аудио с микрофона
if __name__ == "__main__":
    process_microphone_input()
    
