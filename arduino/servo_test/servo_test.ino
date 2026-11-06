/*
 * ==============================================================================
 * Project: SG90 Servo Motor Condition Monitoring and Anomaly Detection System
 * Target: Arduino Uno R3
 * Firmware: Phase 2 Modular Telemetry Engine (servo_test.ino)
 * ==============================================================================
 *
 * Telemetry Stream (10-Field CSV at 115200 Baud):
 *   timestamp_ms,sequence,servo_angle,voltage_v,current_a,accel_x,accel_y,accel_z,sound_rms,sound_p2p
 */

#include <Servo.h>

// ==============================================================================
// 1. HARDWARE PIN ASSIGNMENTS
// ==============================================================================
const uint8_t PIN_SERVO   = 9;   // SG90 PWM control signal
const uint8_t PIN_ACS712  = A0;  // Current sensor analog output
const uint8_t PIN_VOLTAGE = A1;  // 0-25V voltage divider module output (S)
const uint8_t PIN_MIC     = A2;  // MAX9814 microphone analog output
const uint8_t PIN_ACCEL_X = A3;  // 3-axis analog accelerometer X_OUT
const uint8_t PIN_ACCEL_Y = A4;  // 3-axis analog accelerometer Y_OUT
const uint8_t PIN_ACCEL_Z = A5;  // 3-axis analog accelerometer Z_OUT

// ==============================================================================
// 2. TIMING & SEQUENCING
// ==============================================================================
const unsigned long SERIAL_BAUD_RATE      = 115200;
const unsigned long TELEMETRY_INTERVAL_MS = 100;   // 10 Hz telemetry stream
const unsigned long SERVO_STEP_INTERVAL_MS = 1500; // 1.5s dwell per target angle

const int SERVO_SEQUENCE[] = {30, 90, 150, 90};
const uint8_t SERVO_SEQ_COUNT = sizeof(SERVO_SEQUENCE) / sizeof(SERVO_SEQUENCE[0]);
const uint8_t MIC_BURST_COUNT = 32;

// ==============================================================================
// 3. CALIBRATION CONSTANTS
// ==============================================================================
const float ADC_VOLTAGE_REF    = 5.0;
const float VOLT_DIVIDER_RATIO = 5.000;
const float VOLT_CAL_SCALE     = 1.000;
const float ACS_SENSITIVITY    = 0.185; // 0.185 V/A for 5A module (20A=0.100, 30A=0.066)

float acsZeroVoltage = 2.50;

// ==============================================================================
// 4. GLOBAL STATE
// ==============================================================================
Servo motorServo;
uint8_t seqIndex = 0;
int currentServoAngle = 90;
unsigned long sequenceCounter = 0;

unsigned long lastServoMoveTime = 0;
unsigned long lastTelemetryTime = 0;

// ==============================================================================
// 5. HELPER FUNCTIONS
// ==============================================================================
int readSettledADC(uint8_t pin, uint8_t samples = 4) {
  analogRead(pin); // Throwaway conversion to allow voltage settling
  delayMicroseconds(20);

  long sum = 0;
  for (uint8_t i = 0; i < samples; i++) {
    sum += analogRead(pin);
    delayMicroseconds(10);
  }
  return (int)(sum / samples);
}

void calibrateZeroCurrent(uint8_t pin, uint8_t samples = 50) {
  long total = 0;
  for (uint8_t i = 0; i < samples; i++) {
    total += analogRead(pin);
    delay(5);
  }
  float avgRaw = (float)total / (float)samples;
  acsZeroVoltage = avgRaw * (ADC_VOLTAGE_REF / 1023.0);
}

void sampleAudioBurst(float &rmsOut, int &p2pOut) {
  int samples[MIC_BURST_COUNT];
  long sum = 0;
  int minVal = 1023;
  int maxVal = 0;

  for (uint8_t i = 0; i < MIC_BURST_COUNT; i++) {
    int val = analogRead(PIN_MIC);
    samples[i] = val;
    sum += val;
    if (val < minVal) minVal = val;
    if (val > maxVal) maxVal = val;
  }

  p2pOut = maxVal - minVal;

  float mean = (float)sum / (float)MIC_BURST_COUNT;
  float sumSq = 0;
  for (uint8_t i = 0; i < MIC_BURST_COUNT; i++) {
    float diff = (float)samples[i] - mean;
    sumSq += diff * diff;
  }
  rmsOut = sqrt(sumSq / (float)MIC_BURST_COUNT);
}

void stepServoSequence() {
  currentServoAngle = SERVO_SEQUENCE[seqIndex];
  motorServo.write(currentServoAngle);

  seqIndex++;
  if (seqIndex >= SERVO_SEQ_COUNT) {
    seqIndex = 0;
  }
}

// ==============================================================================
// 6. SETUP
// ==============================================================================
void setup() {
  Serial.begin(SERIAL_BAUD_RATE);
  while (!Serial && millis() < 2500) {
    // Wait for USB connection
  }

  motorServo.attach(PIN_SERVO);
  motorServo.write(90);
  delay(600); // Allow mechanical settling before zero-current calibration

  calibrateZeroCurrent(PIN_ACS712, 50);

  // Emit Standardized CSV Header
  Serial.println(F("timestamp_ms,sequence,servo_angle,voltage_v,current_a,accel_x,accel_y,accel_z,sound_rms,sound_p2p"));

  stepServoSequence();
  lastServoMoveTime = millis();
  lastTelemetryTime = millis();
}

// ==============================================================================
// 7. LOOP
// ==============================================================================
void loop() {
  unsigned long now = millis();

  // Task 1: Non-blocking servo angle sequence update
  if (now - lastServoMoveTime >= SERVO_STEP_INTERVAL_MS) {
    stepServoSequence();
    lastServoMoveTime = now;
  }

  // Task 2: High-frequency telemetry acquisition & transmission (10 Hz)
  if (now - lastTelemetryTime >= TELEMETRY_INTERVAL_MS) {
    lastTelemetryTime = now;

    // 1. Accelerometer (3-Axis Analog on A3, A4, A5)
    int ax = readSettledADC(PIN_ACCEL_X);
    int ay = readSettledADC(PIN_ACCEL_Y);
    int az = readSettledADC(PIN_ACCEL_Z);

    // 2. Current Sensor (ACS712 on A0)
    int acsRaw = readSettledADC(PIN_ACS712);
    float acsVoltage = acsRaw * (ADC_VOLTAGE_REF / 1023.0);
    float currentA = (acsVoltage - acsZeroVoltage) / ACS_SENSITIVITY;
    if (abs(currentA) < 0.015) {
      currentA = 0.0;
    }

    // 3. Voltage Sensor (0–25V module on A1)
    int voltRaw = readSettledADC(PIN_VOLTAGE);
    float adcPinVoltage = voltRaw * (ADC_VOLTAGE_REF / 1023.0);
    float voltageV = adcPinVoltage * VOLT_DIVIDER_RATIO * VOLT_CAL_SCALE;
    if (voltageV < 0.05) {
      voltageV = 0.0;
    }

    // 4. Acoustic Features (MAX9814 on A2)
    float soundRMS = 0.0;
    int soundP2P = 0;
    sampleAudioBurst(soundRMS, soundP2P);

    // 5. Standardized CSV Output (10 fields)
    Serial.print(now);
    Serial.print(F(","));
    Serial.print(sequenceCounter++);
    Serial.print(F(","));
    Serial.print(currentServoAngle);
    Serial.print(F(","));
    Serial.print(voltageV, 2);
    Serial.print(F(","));
    Serial.print(currentA, 3);
    Serial.print(F(","));
    Serial.print(ax);
    Serial.print(F(","));
    Serial.print(ay);
    Serial.print(F(","));
    Serial.print(az);
    Serial.print(F(","));
    Serial.print(soundRMS, 2);
    Serial.print(F(","));
    Serial.println(soundP2P);
  }
}
