// void joyXY(){
//   Dabble.processInput();               // always first!

//   /* ---------- speed trim buttons ---------- */
//   static bool prevCircle = false, prevSquare = false;
//   bool curCircle = GamePad.isCirclePressed();
//   bool curSquare = GamePad.isSquarePressed();
//   if (curCircle && !prevCircle && baseSpeed < 200) baseSpeed += 10;
//   if (curSquare && !prevSquare && baseSpeed >  20) baseSpeed -= 10;
//   prevCircle = curCircle;
//   prevSquare = curSquare;

//   /* ---------- D‑pad tap moves ---------- */
//   if (GamePad.isUpPressed())    { forward(baseSpeed);  delay(70); stop(); }
//   if (GamePad.isDownPressed())  { backward(baseSpeed); delay(70); stop(); }
//   if (GamePad.isLeftPressed())  { left();              delay(70); stop(); }
//   if (GamePad.isRightPressed()) { right();             delay(70); stop(); }

//   /* ---------- Joystick analogue drive ---------- */
//   int joyX = GamePad.getXaxisData();   // –7 … +7
//   int joyY = GamePad.getYaxisData();   // –7 … +7

//   if (abs(joyX) <= deadZone && abs(joyY) <= deadZone) {
//     stop();                            // stick centred
//     return;
//   }

//   /* mostly forward/back?  then scale Y */
//   if (abs(joyY) >= abs(joyX)) {
//       int dyn = map(abs(joyY), 0, 7, 0, baseSpeed);
//       (joyY > 0) ? forward(dyn) : backward(dyn);
//   }
//   /* mostly side‑to‑side?  use gentler left/right */
//   else {
//       (joyX > 0) ? right() : left();   // ← now honours turnScale
//   }
// }