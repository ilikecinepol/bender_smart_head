#include <Servo.h>
#include <AccelStepper.h> // Подключаем библиотеку для шагового двигателя

// Пины для подключения сервомоторов
const int servoUpDownPinLeftEye = 5;    // пин для серво поворота вверх-вниз левого глаза
const int servoLeftRightPinLeftEye = 6; // пин для серво поворота влево-вправо левого глаза
const int servoUpDownPinRightEye = 9;   // пин для серво поворота вверх-вниз правого глаза
const int servoLeftRightPinRightEye = 10; // пин для серво поворота влево-вправо правого глаза

// Пины для подключения шагового двигателя
const int stepperMotorPins[] = {2, 3, 4, 7}; // IN1, IN2, IN3, IN4

// Пины для подключения джойстика
const int joyStickXPin = A0; // Пин для оси X джойстика
const int joyStickYPin = A1; // Пин для оси Y джойстика
const int joyStickSwPin = 8; // Пин для кнопки джойстика

// Объекты для управления сервомоторами
Servo servoUpDownLeftEye;
Servo servoLeftRightLeftEye;
Servo servoUpDownRightEye;
Servo servoLeftRightRightEye;

// Объект для управления шаговым мотором
AccelStepper stepperMotor(1, stepperMotorPins[0], stepperMotorPins[1], stepperMotorPins[2], stepperMotorPins[3]); // указываем тип драйвера и пины подключения

// Текущие позиции сервомоторов
int currentUpDownPosLeftEye = 90;
int currentLeftRightPosLeftEye = 90;
int currentUpDownPosRightEye = 90;
int currentLeftRightPosRightEye = 90;

// Переменные для сглаживания движения глаз
int previousUpDownPosLeftEye = 90;
int previousLeftRightPosLeftEye = 90;
int previousUpDownPosRightEye = 90;
int previousLeftRightPosRightEye = 90;

// Функция для сглаживания движения глаз
void smoothEyeMovement(int& currentPos, int& previousPos, int targetPos) {
  currentPos = (targetPos * 0.02) + (previousPos * 0.98);
  previousPos = currentPos;
}

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

  // Устанавливаем пины шагового двигателя как выходы
  for (int i = 0; i < 4; i++) {
    pinMode(stepperMotorPins[i], OUTPUT);
  }

  // Устанавливаем скорость шагового двигателя
  stepperMotor.setSpeed(100);
}

void loop() {
  // Получаем значения с джойстика
  int joyStickXValue = analogRead(joyStickXPin);
  int joyStickYValue = analogRead(joyStickYPin);

  // Преобразуем значения джойстика в углы для движения глазами
  int eyeMovementXLeft = map(joyStickXValue, 0, 1023, 175, 15);
  int eyeMovementYLeft = map(joyStickYValue, 0, 1023, 175, 15);
  int eyeMovementXRight = map(joyStickXValue, 0, 1023, 175, 15);
  int eyeMovementYRight = map(joyStickYValue, 0, 1023, 15, 175);

  // Двигаем глазами в зависимости от позиции джойстика
  smoothEyeMovement(currentUpDownPosLeftEye, previousUpDownPosLeftEye, eyeMovementYLeft);
  smoothEyeMovement(currentLeftRightPosLeftEye, previousLeftRightPosLeftEye, eyeMovementXLeft);
  smoothEyeMovement(currentUpDownPosRightEye, previousUpDownPosRightEye, eyeMovementYRight);
  smoothEyeMovement(currentLeftRightPosRightEye, previousLeftRightPosRightEye, eyeMovementXRight);

  // Поворачиваем сервомоторы в соответствии с новыми позициями
  servoUpDownLeftEye.write(currentUpDownPosLeftEye);
  servoLeftRightLeftEye.write(currentLeftRightPosLeftEye);
  servoUpDownRightEye.write(currentUpDownPosRightEye);
  servoLeftRightRightEye.write(currentLeftRightPosRightEye);

  // Другие операции управления шаговым двигателем
}
