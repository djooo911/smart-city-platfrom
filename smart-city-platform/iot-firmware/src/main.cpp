/*
 * Smart City Lamp Node — ESP32 Firmware (Wokwi simulation)
 *
 * MILESTONE 0 PLACEHOLDER — intentionally empty of sensor/actuator logic.
 *
 * Per project decisions, this firmware will (starting in its own
 * implementation milestone):
 *   - Read the potentiometer (LDR proxy for ambient light)
 *   - Read the PIR sensor (pedestrian detection)
 *   - Read the HC-SR04 ultrasonic sensor (vehicle detection / distance)
 *   - Drive the LED via PWM to represent street light brightness
 *   - Send an HTTP POST request with telemetry to the FastAPI backend
 *     (no MQTT — per project decision, ESP32 <-> backend is plain HTTP REST)
 *
 * This file exists now only so the project folder structure and Wokwi
 * project files (diagram.json, wokwi.toml) are in place and openable.
 */

#include <Arduino.h>

void setup() {
  Serial.begin(115200);
  Serial.println("Smart City Lamp Node - firmware scaffold. No logic yet.");
}

void loop() {
  // Sensor reading, lighting control, and HTTP telemetry submission
  // will be implemented in a later milestone.
}
