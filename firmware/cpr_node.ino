/*
 * CPR Smart Sensor Node
 * Platform: Arduino / ESP32
 * Sensors: 
 *  - FSR402 (Force) on Pin A0
 *  - MPU6050 (Acceleration) via I2C
 */

#include <Wire.h>
#include <ArduinoJson.h> // Requires ArduinoJson library

const int FSR_PIN = A0;
const int LED_PIN = 13;

// MPU6050 Registers
const int MPU_ADDR = 0x68;

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
  
  // Init MPU6050
  Wire.begin();
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x6B); // Power management
  Wire.write(0);    // Wake up
  Wire.endTransmission(true);
}

void loop() {
  // 1. Read Force
  int fsrValue = analogRead(FSR_PIN);
  float forceN = map(fsrValue, 0, 1023, 0, 600); // Rough calib to Newtons
  
  // 2. Read Accel (Z-axis is depth)
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x3B); // Start reading accel regs
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_ADDR, 14, true);
  
  int16_t ax = Wire.read()<<8 | Wire.read();
  int16_t ay = Wire.read()<<8 | Wire.read();
  int16_t az = Wire.read()<<8 | Wire.read();
  
  // Convert to m/s^2 (assuming +/- 2g range)
  float accelZ = (az / 16384.0) * 9.81;
  // Subtract gravity (approx)
  accelZ -= 9.81;

  // 3. Create JSON Packet
  StaticJsonDocument<200> doc;
  doc["sensor_id"] = "node_01";
  doc["force_n"] = forceN;
  doc["accel_z"] = accelZ;
  doc["timestamp"] = millis();

  // 4. Send
  serializeJson(doc, Serial);
  Serial.println();

  delay(20); // ~50Hz transmission
}
