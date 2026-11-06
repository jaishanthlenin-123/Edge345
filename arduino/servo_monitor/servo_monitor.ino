/*
 * ==============================================================================
 * Project: SG90 Servo Motor Condition Monitoring and Anomaly Detection System
 * Target: Arduino Uno R3
 * Firmware: Phase 2 Modular Telemetry Engine (servo_monitor.ino)
 * ==============================================================================
 *
 * Telemetry Stream (10-Field CSV at 115200 Baud):
 *   timestamp_ms,sequence,servo_angle,voltage_v,current_a,accel_x,accel_y,accel_z,sound_rms,sound_p2p
 */

#include <Servo.h>
#include "config.h"
#include "calibration.h"

// Define external calibration global
float acsZeroVoltage = 2.50;

// ==============================================================================
// GLOBAL STATE
// ==============================================================================
Servo motorServo;
uint8_t seqIndex = 0;
int currentServoAngle = 90;
unsigned long sequenceCounter = 0;

unsigned long lastServoMoveTime = 0;
unsigned long lastTelemetryTime = 0;

// ==============================================================================
// ANALOG SENSOR SAMPLING UTILITIES
// ==============================================================================

/**
 * Discards the first conversion and averages multiple samples to prevent
 * sample-and-hold capacitor crosstalk when switching ADC multiplexer channels.
 */
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

/**
 * Rapid burst microphone acquisition (~3.5 ms total execution time).
 * Samples 32 consecutive audio values, subtracts the DC bias mean,
 * and calculates true RMS energy and Peak-to-Peak amplitude.
 */
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

/**
 * Steps the servo to the next angle in the sequence.
 */
void stepServoSequence() {
  currentServoAngle = SERVO_SEQUENCE[seqIndex];
  motorServo.write(currentServoAngle);

  seqIndex++;
  if (seqIndex >= SERVO_SEQ_COUNT) {
    seqIndex = 0;
  }
}

// ==============================================================================
// ARDUINO SETUP
// ==============================================================================
void setup() {
  // Initialize Serial at 115200 baud
  Serial.begin(SERIAL_BAUD_RATE);
  while (!Serial && millis() < 2500) {
    // Wait for USB connection
  }

  // Attach servo on D9 and center
  motorServo.attach(PIN_SERVO);
  motorServo.write(90);
  delay(600); // Allow mechanical settling before zero-current calibration

  // Calibrate ACS712 quiescent zero-current voltage
  calibrateZeroCurrent(PIN_ACS712, 50);

  // Emit Standardized CSV Header
  Serial.println(F("timestamp_ms,sequence,servo_angle,voltage_v,current_a,accel_x,accel_y,accel_z,sound_rms,sound_p2p"));

  stepServoSequence();
  lastServoMoveTime = millis();
  lastTelemetryTime = millis();
}

// ==============================================================================
// MAIN ARDUINO EXECUTION LOOP
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
      currentA = 0.0; // Filter ADC quiescent flicker
    }

    // 3. Voltage Sensor (0–25V module on A1)
    int voltRaw = readSettledADC(PIN_VOLTAGE);
    float adcPinVoltage = voltRaw * (ADC_VOLTAGE_REF / 1023.0);
    float voltageV = adcPinVoltage * VOLT_DIVIDER_RATIO * VOLT_CAL_SCALE;
    if (voltageV < 0.05) {
      voltageV = 0.0; // Filter disconnected/floating ADC rail
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
