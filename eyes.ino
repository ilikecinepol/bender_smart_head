#include <Servo.h>
#include "Stepper.h"

// Пины для подключения сервомоторов
const int servoUpDownPinLeftEye = 5;       // пин для серво поворота вверх-вниз левого глаза
const int servoLeftRightPinLeftEye = 6;    // пин для серво поворота влево-вправо левого глаза
const int servoUpDownPinRightEye = 9;      // пин для серво поворота вверх-вниз правого глаза
const int servoLeftRightPinRightEye = 10;  // пин для серво поворота влево-вправо правого глаза

const int maxDeltaX = 20;
const int maxDeltaY = maxDeltaX;

const int stepsPerRevolution = 200;

// Объекты для управления сервомоторами
Servo servoUpDownLeftEye;
Servo servoLeftRightLeftEye;
Servo servoUpDownRightEye;
Servo servoLeftRightRightEye;

Stepper myStepper = Stepper(stepsPerRevolution, 3, 4, 7, 8);

void setup() {
  // Устанавливаем пины сервомоторов как выходы
  pinMode(servoUpDownPinLeftEye, OUTPUT);
  pinMode(servoLeftRightPinLeftEye, OUTPUT);
  pinMode(servoUpDownPinRightEye, OUTPUT);
  pinMode(servoLeftRightPinRightEye, OUTPUT);

  // Прикрепляем объекты к пинам
  servoUpDownLeftEye.attach(servoUpDownPinLeftEye);
  servoLeftRightLeftEye.attach(servoLeftRightPinLeftEye);
  servoUpDownRightEye.attach(servoUpDownPinRightEye);
  servoLeftRightRightEye.attach(servoLeftRightPinRightEye);

  // Инициализируем шаговый двигатель
  myStepper.setSpeed(100);

  // Инициализируем Serial порт
  Serial.begin(9600);

  servoUpDownLeftEye.write(90);
  servoLeftRightLeftEye.write(90);
  servoUpDownRightEye.write(90);
  servoLeftRightRightEye.write(90);
  eyes_on();
  delay(1000);
  eyes_off();
}

void eyes_off() {
  // Двигаем шаговый двигатель, чтобы глаза были включены
  myStepper.step(700);
  delay(2000);  // Ждем, пока глаза сместятся
}

void eyes_on() {
  // Двигаем шаговый двигатель, чтобы глаза были выключены
  myStepper.step(-700);
  delay(2000);  // Ждем, пока глаза сместятся
}

unsigned long lastDataTime = 0;  // Переменная для отслеживания времени последнего обновления данных

void loop() {
  // Проверяем, есть ли данные в Serial порте
  if (Serial.available() >= 7) {
    // Если данные есть, читаем их и обновляем переменную lastDataTime
    int delta_x = Serial.parseInt();
    int delta_y = Serial.parseInt();
    Serial.read();            // Пропускаем запятую
    lastDataTime = millis();  // Обновляем время последнего обновления данных

    // Переводим значения в углы поворота для сервомоторов
    int servoAngleX = map(delta_x, -320, 320, 135, 45);
    int servoAngleY = map(delta_y, -240, 240, 45, 135);

    // Поворачиваем сервомоторы в соответствии с углами
    servoUpDownLeftEye.write(180 - servoAngleY);
    servoLeftRightLeftEye.write(servoAngleX);
    servoUpDownRightEye.write(servoAngleY);
    servoLeftRightRightEye.write(servoAngleX);
  } else {
    // Если данные не поступают в течение определенного времени, возвращаем глаза в положение 90
    if (millis() - lastDataTime > 1000) {  // Если прошло более 1 секунды с последнего обновления данных
      servoUpDownLeftEye.write(90);
      servoLeftRightLeftEye.write(90);
      servoUpDownRightEye.write(90);
      servoLeftRightRightEye.write(90);
    }
  }
}
