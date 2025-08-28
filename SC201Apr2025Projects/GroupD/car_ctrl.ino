// /* ------------- Motor helpers ------------------------------------ */
const float turnScale = 0.9;          
void forward(int speed) {              
  analogWrite(motorRF, 36 + speed);
  analogWrite(motorLF, 44 + speed);
  analogWrite(motorLB, 0);
  analogWrite(motorRB, 0);
}

void backward(int speed) {             
  analogWrite(motorLF, 0);
  analogWrite(motorLB, 47 + speed);
  analogWrite(motorRF, 0);
  analogWrite(motorRB, 39 + speed);
}

void left() {                         
  analogWrite(motorLF, 0);
  analogWrite(motorLB, int(55 * turnScale));
  analogWrite(motorRF, int(65 * turnScale));
  analogWrite(motorRB, 0);
}

void right() {                         
  analogWrite(motorLF, int(65 * turnScale));
  analogWrite(motorLB, 0);
  analogWrite(motorRF, 0);
  analogWrite(motorRB, int(55 * turnScale));
}

void stop() {                          
  analogWrite(motorLF, 0);
  analogWrite(motorLB, 0);
  analogWrite(motorRF, 0);
  analogWrite(motorRB, 0);
}
