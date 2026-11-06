#ifndef CONFIG_H
#define CONFIG_H

#include <Arduino.h>

// ==============================================================================
// HARDWARE PIN ASSIGNMENTS (Audited & Confirmed)
// ==============================================================================
const uint8_t PIN_SERVO      = 9;   // SG90 PWM control signal (Timer1)
const uint8_t PIN_ACS712     = A0;  // Current sensor analog output
const uint8_t PIN_VOLTAGE    = A1;  // 0-25V voltage divider module output (S)
const uint8_t PIN_MIC        = A2;  // MAX9814 microphone analog output
const uint8_t PIN_ACCEL_X    = A3;  // 3-axis analog accelerometer X_OUT
const uint8_t PIN_ACCEL_Y    = A4;  // 3-axis analog accelerometer Y_OUT
const uint8_t PIN_ACCEL_Z    = A5;  // 3-axis analog accelerometer Z_OUT

// ==============================================================================
// SERIAL & TELEMETRY TIMING
// ==============================================================================
const unsigned long SERIAL_BAUD_RATE    = 115200;
const unsigned long TELEMETRY_INTERVAL_MS = 100;   // 10 Hz telemetry stream
const unsigned long SERVO_STEP_INTERVAL_MS = 1500; // 1.5s dwell per target angle

// Servo target sequence
const int SERVO_SEQUENCE[] = {30, 90, 150, 90};
const uint8_t SERVO_SEQ_COUNT = sizeof(SERVO_SEQUENCE) / sizeof(SERVO_SEQUENCE[0]);

// High-frequency microphone burst samples (rapid non-blocking 3.5ms acquisition)
const uint8_t MIC_BURST_COUNT = 32;

#endif // CONFIG_H
