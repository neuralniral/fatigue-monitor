const int VRX_PIN = A0; // X-axis
const int VRY_PIN = A1; // Y-axis
const int SW_PIN  = 2;  // Joystick button (not used in this iteration of fatigue monitor)

// Thresholds for stickdrift and sensitivity
const int CENTER = 512;
const int THRESHOLD = 250; 

String last_direction = "CENTER";

void setup() {
  Serial.begin(9600);
  pinMode(SW_PIN, INPUT_PULLUP);
}

void loop() {
  int xVal = analogRead(VRX_PIN);
  int yVal = analogRead(VRY_PIN);

  // Determine current direction based on stick displacement
  String current_direction = "CENTER";

  if (yVal < (CENTER - THRESHOLD)) {
    current_direction = "UP";
  } else if (yVal > (CENTER + THRESHOLD)) {
    current_direction = "DOWN";
  } else if (xVal < (CENTER - THRESHOLD)) {
    current_direction = "LEFT";
  } else if (xVal > (CENTER + THRESHOLD)) {
    current_direction = "RIGHT";
  }

  if (current_direction != last_direction) {
    if (current_direction != "CENTER") {
      Serial.println(current_direction);
    }
    last_direction = current_direction;
    delay(50); // Small debounce delay
  }
}