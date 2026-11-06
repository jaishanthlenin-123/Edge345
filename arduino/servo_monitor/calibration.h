#ifndef CALIBRATION_H
#define CALIBRATION_H

#include <Arduino.h>

// ==============================================================================
// SENSOR CALIBRATION PARAMETERS
// ==============================================================================

// Microcontroller ADC Reference (Nominal 5.0V from USB/Regulator)
const float ADC_VOLTAGE_REF = 5.0;

// Voltage Divider: 30k / 7.5k resistor ratio (5:1)
// Calibrate with multimeter: MULTIMETER_READING / ARDUINO_VOLTAGE_READING
const float VOLT_DIVIDER_RATIO = 5.000;
const float VOLT_CAL_SCALE     = 1.000;

// ACS712 Current Sensor:
// Sensitivity options:
//   - 5A variant:  0.185 V/A (185 mV/A)  <-- Default for SG90
//   - 20A variant: 0.100 V/A (100 mV/A)
//   - 30A variant: 0.066 V/A (66 mV/A)
const float ACS_SENSITIVITY = 0.185; 

// Dynamic baseline zero-current voltage (measured in setup())
extern float acsZeroVoltage;

// Accelerometer stationary zero-g offsets (calibrated at rest)
const int ACCEL_X_ZERO = 350;
const int ACCEL_Y_ZERO = 350;
const int ACCEL_Z_ZERO = 350;

/**
 * Automatically calculates quiescent zero-current offset at boot while motor is idle.
 */
inline void calibrateZeroCurrent(uint8_t pin, uint8_t samples = 50) {
  long total = 0;
  for (uint8_t i = 0; i < samples; i++) {
    total += analogRead(pin);
    delay(5);
  }
  float avgRaw = (float)total / (float)samples;
  acsZeroVoltage = avgRaw * (ADC_VOLTAGE_REF / 1023.0);
}

#endif // CALIBRATION_H
