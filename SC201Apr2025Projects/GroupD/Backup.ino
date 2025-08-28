#define CUSTOM_SETTINGS
#define INCLUDE_GAMEPAD_MODULE
// #include <Dabble.h>

const uint8_t maskA = (1 << PC0) | (1 << PC1);
volatile uint8_t *portC;

#define motorLF 5
#define motorLB 6
#define motorRF 10
#define motorRB 9
#define Trig 7
#define Echo 8
int a = 0;

// /* --------- joystick tuning --------- */
const uint8_t deadZone = 1;  
extern const float turnScale;
int baseSpeed = 80;
int IRL = A1;
int IRR = A0;
int IRLState;
int IRRState;
float echotime;
float distance;
float T = 22.0;

// void ultrasound() {
//   digitalWrite(Trig, LOW);
//   delayMicroseconds(2);
//   digitalWrite(Trig, HIGH);
//   delayMicroseconds(10);
//   digitalWrite(Trig, LOW);

//   echotime = pulseIn(Echo, HIGH, 30000);
//   distance = v * (echotime / 2);

//   Serial.print("D = ");
//   Serial.print(distance);
//   Serial.println(" cm");
// }

// // Switch between modes
enum Mode { MODE_JOYSTICK = 0,
            MODE_LINE_OUT,
            MODE_LINE_IN  };

Mode curMode = MODE_LINE_IN;

void setup() {
    Serial.begin(9600);
  pinMode(motorLF, OUTPUT);
  pinMode(motorLB, OUTPUT);
  Serial.println("Test0");
  pinMode(motorRF, OUTPUT);
  pinMode(motorRB, OUTPUT);
Serial.println("Test1");
    pinMode(Trig, OUTPUT);
    pinMode(Echo, INPUT);
Serial.println("Test2");
  pinMode(IRL, INPUT);
  pinMode(IRR, INPUT);
Serial.println("Test3");
  PORTC |= maskA;
  portC = portInputRegister(digitalPinToPort(IRL));
  Serial.println("Test");
  stop();
//   Dabble.begin(9600);
}


void loop() {
    line_mode_inside_1();
//   Dabble.processInput();
  
//   if (GamePad.isTrianglePressed()) {
//       curMode = MODE_JOYSTICK;
//       stop();
//   }
//   else if (GamePad.isStartPressed()) {
//       curMode = MODE_LINE_OUT;
//       stop();
//   }
//   else if (GamePad.isSelectPressed()) {
//       curMode = MODE_LINE_IN;
//       stop();
//   }

//   switch (curMode) {
//       case MODE_JOYSTICK:
//           joyXY();
//           break;

//       case MODE_LINE_OUT:
//           line_mode_outside();
//           break;

//       case MODE_LINE_IN:
//           line_mode_inside();
//           break;
//   }
}
const int obstacle_cm = 15;
float v = (331 + 0.6 * T) * 100 / 1000000;

void ultrasound() {
  digitalWrite(Trig, LOW);
  digitalWrite(Trig, HIGH);
  delay(5);
  digitalWrite(Trig, LOW);
  echotime = pulseIn(Echo, HIGH);
  distance = v * (echotime / 2);
  Serial.print("D = ");
  Serial.print(distance);
  Serial.println(" cm");
}

void line_mode_inside_1() {
  ultrasound(); 

  if (distance < obstacle_cm) { 
    stop();
    return;
  }

  uint8_t pins = *portC & maskA;
  switch (pins) {
    case ((1 << PC0) | (1 << PC1)):
      forward(40);
      break;

    case ((1 << PC0) | (0 << PC1)):
      left();
      break;

    case ((0 << PC0) | (1 << PC1)):
      right();
      break;

    default:
      if (a == 0){
        forward(40);
        delay(150);
        left();
        delay(700);
        a=a+1;
      } else if (a==1){
        right();
        delay(1500);
        a=a+1;
      } else if (a==2) {
        right();
        delay(300);
        a=a+1;
      } else {
        
        stop();
      }
      break;
  }
}

void line_mode_inside_2() {
  ultrasound(); 

  if (distance < obstacle_cm) { 
    stop();
    return;
  }

  uint8_t pins = *portC & maskA;
  switch (pins) {
    case ((1 << PC0) | (1 << PC1)):
      forward(40);
      break;

    case ((1 << PC0) | (0 << PC1)):
      left();
      break;

    case ((0 << PC0) | (1 << PC1)):
      right();
      break;

    default:
      if (a == 2){
        forward(40);
        delay(30);
        left();
        delay(300);
        a=a+1;
      } else if (a==1){
        right();
        delay(1400);
        a=a+1;
      } else if (a==0) {
        forward(40);
        delay(30);
        right();
        delay(300);
        a=a+1;
      } else {
        // forward(40);
        // delay(150);
        stop();
      }
      break;
  }
}

void line_mode_outside() {
  ultrasound();

  if (distance < obstacle_cm) { 
    stop();
    return;
  }

  uint8_t pins = *portC & maskA;
  switch (pins) {
    case ((1 << PC0) | (1 << PC1)):
      forward(40);
      break;

    case ((1 << PC0) | (0 << PC1)):
      left();
      break;

    case ((0 << PC0) | (1 << PC1)):
      right();
      break;

    default:
      stop();
      break;
  }
}
