/*
 * SG90 Servo Motor Standalone Test Firmware (Phase 2)
 * Project: SG90 Servo Motor Condition Monitoring and Anomaly Detection System
 * Target: Arduino Uno
 *
 * Description:
 *   Validates basic SG90 servo control using the Arduino Servo library on Pin D9.
 *   Smoothly sequences the servo arm across 3 predefined target angles:
 *   30 degrees -> 90 degrees -> 150 degrees -> 90 degrees -> repeat.
 *
 *   Outputs structured serial telemetry so that the Raspberry Pi 5 receiver
 *   can parse the commanded angle and timestamp.
 *
 * Safety & Hardware Notice:
 *   - Signal wire (Orange/Yellow) -> Arduino Pin D9
 *   - Ground wire (Brown/Black)   -> External 5V Supply Ground AND Arduino GND (Common Ground)
 *   - Power wire (Red)            -> External 5V Power Supply Positive (+5V)
 *   - DO NOT connect the servo red wire to the Arduino 5V pin!
 */

#include <Servo.h>

// ---------------------- Pin and Constant Definitions ----------------------
const uint8_t SERVO_PIN = 9;         // Digital pin connected to SG90 PWM signal wire
const unsigned long SERIAL_BAUD = 115200; // Standard fast serial communication baud rate

// Movement sequence angles (in degrees)
const int TARGET_ANGLES[] = {30, 90, 150, 90};
const uint8_t NUM_TARGETS = sizeof(TARGET_ANGLES) / sizeof(TARGET_ANGLES[0]);

// Configurable timing constants (in milliseconds)
const unsigned long DWELL_TIME_MS = 1000;    // Pause time at each target position
const unsigned long STEP_INTERVAL_MS = 15;  // Delay between incremental steps for smooth motion

// ---------------------- Global Variables ----------------------
Servo sg90;
int currentAngle = 90;               // Start position
uint8_t targetIndex = 0;             // Index in TARGET_ANGLES sequence
unsigned long lastStepTime = 0;
unsigned long dwellStartTime = 0;
bool isDwelling = false;

// ---------------------- Setup Function ----------------------
void setup() {
  // Initialize serial communication
  Serial.begin(SERIAL_BAUD);
  while (!Serial && millis() < 3000) {
    // Wait for serial port to open (up to 3 seconds)
  }

  // Print startup identification header
  Serial.println(F("# SYSTEM: SG90 Servo Motor Test Initialized"));
  Serial.println(F("# FORMAT: timestamp_ms,commanded_angle,status"));

  // Attach servo to control pin and move to initial position
  sg90.attach(SERVO_PIN);
  sg90.write(currentAngle);
  
  // Give servo mechanical time to reach home position
  delay(500);

  dwellStartTime = millis();
  isDwelling = true;

  // Print initial state
  reportTelemetry(currentAngle, F("HOME"));
}

// ---------------------- Main Loop ----------------------
void loop() {
  unsigned long now = millis();
  int targetAngle = TARGET_ANGLES[targetIndex];

  if (isDwelling) {
    // We have arrived at a target angle and are pausing (dwelling)
    if (now - dwellStartTime >= DWELL_TIME_MS) {
      // Dwell period finished; advance to next target
      isDwelling = false;
      targetIndex = (targetIndex + 1) % NUM_TARGETS;
    }
  } else {
    // Non-blocking smooth step movement towards targetAngle
    if (now - lastStepTime >= STEP_INTERVAL_MS) {
      lastStepTime = now;

      if (currentAngle < targetAngle) {
        currentAngle++;
        sg90.write(currentAngle);
        reportTelemetry(currentAngle, F("MOVING_CW"));
      } else if (currentAngle > targetAngle) {
        currentAngle--;
        sg90.write(currentAngle);
        reportTelemetry(currentAngle, F("MOVING_CCW"));
      } else {
        // Reached target position! Enter dwell mode.
        isDwelling = true;
        dwellStartTime = now;
        reportTelemetry(currentAngle, F("HOLD"));
      }
    }
  }
}

// ---------------------- Helper: Report Telemetry ----------------------
void reportTelemetry(int angle, const __FlashStringHelper* statusStr) {
  Serial.print(millis());
  Serial.print(F(","));
  Serial.print(angle);
  Serial.print(F(","));
  Serial.println(statusStr);
}
