#include <Servo.h>

// Пины для подключения сервомоторов
const int servoUpDownPinLeftEye = 5;      // пин для серво поворота вверх-вниз левого глаза
const int servoLeftRightPinLeftEye = 6;   // пин для серво поворота влево-вправо левого глаза
const int servoUpDownPinRightEye = 9;     // пин для серво поворота вверх-вниз правого глаза
const int servoLeftRightPinRightEye = 10; // пин для серво поворота влево-вправо правого глаза

const int maxDeltaX = 20;
const int maxDeltaY = maxDeltaX;

// Объекты для управления сервомоторами
Servo servoUpDownLeftEye;
Servo servoLeftRightLeftEye;
Servo servoUpDownRightEye;
Servo servoLeftRightRightEye;

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

  servoUpDownLeftEye.write(90);
  servoLeftRightLeftEye.write(90);
  servoUpDownRightEye.write(90);
  servoLeftRightRightEye.write(90);

  delay(100000);

  // Инициализируем Serial порт
  Serial.begin(9600);
}

void loop() {
  // Ждем, пока данные придут через Serial порт
  while (Serial.available() < 7) {
    delay(10);
  }

  // Читаем данные из Serial порта
  int delta_x = Serial.parseInt();
  int delta_y = Serial.parseInt();
  // Считываем разделитель
  Serial.read(); // Пропускаем запятую

  // Переводим значения в углы поворота для сервомоторов
  int servoAngleX = map(delta_x, -320, 320, (90 + (maxDeltaX / 2)), (90 - (maxDeltaX / 2)));
  //int servoAngleY = map(delta_y, -240, 240, (90 - (maxDeltaX / 2)), (90 + (maxDeltaX / 2)));
  int servoAngleY = 90;
  // Поворачиваем сервомоторы в соответствии с углами
  servoUpDownLeftEye.write(servoAngleY);
  servoLeftRightLeftEye.write(servoAngleX);
  servoUpDownRightEye.write(servoAngleY);
  servoLeftRightRightEye.write(servoAngleX);
}
