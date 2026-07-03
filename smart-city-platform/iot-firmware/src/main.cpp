/*
 * Smart City Lamp Node — ESP32 Firmware (Wokwi simulation), Milestone 5.
 *
 * Reads three sensors (potentiometer as an ambient-light/LDR proxy, a PIR
 * motion sensor, an HC-SR04 ultrasonic distance sensor as a vehicle-
 * proximity proxy), POSTs telemetry over HTTPS to the live deployed
 * backend's `POST /lamps/{device_id}/telemetry` endpoint (no MQTT — see
 * docker-compose.yml's own comment on this project decision), and applies
 * the brightness the backend computes back onto the LED via PWM.
 *
 * Auth: logs in once via POST /auth/login with a shared operator
 * credential (see secrets.h -- copy secrets.h.example and fill in your
 * own DEVICE_PASSWORD, matching the backend's DEVICE_SEED_PASSWORD; never
 * commit the real secrets.h, it's gitignored) and re-logs in proactively
 * before the JWT's ~60 minute expiry.
 *
 * WiFi: Wokwi's simulator provides a virtual "Wokwi-GUEST" open network
 * with real internet passthrough (HTTP/HTTPS) -- this only works inside
 * Wokwi's simulator, not on real hardware.
 *
 * HTTPS: uses WiFiClientSecure::setInsecure() to skip CA certificate
 * validation -- the standard simplification for this kind of educational
 * ESP32 prototype (mirrors this project's backend choices of stdlib
 * pbkdf2 over passlib+bcrypt, and PyJWT over python-jose: proportional
 * complexity, not maximal security engineering).
 *
 * PWM: written against the ESP32 Arduino core 2.x LEDC API
 * (ledcSetup/ledcAttachPin/ledcWrite(channel, duty)) since that's what
 * PlatformIO's unpinned "platform = espressif32" resolves to today (see
 * platformio.ini's comment). If that resolves to core 3.x in the future,
 * these calls would need updating to ledcAttach(pin, ...)/ledcWrite(pin,
 * ...).
 *
 * Timestamps: NTP-synced (UTC), formatted with no "Z"/offset suffix to
 * match this project's naive-UTC convention used throughout the backend.
 */

#include <Arduino.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <time.h>

#include "secrets.h"

// --- Configuration -------------------------------------------------------

static const char *WIFI_SSID = "Wokwi-GUEST";
static const char *BACKEND_BASE_URL = "https://smart-city-platfrom.onrender.com/api/v1";
static const char *DEVICE_ID = "lamp-001"; // matches a lamp seeded by backend/app/infrastructure/mongo/seed.py

static const int POT_PIN = 34;  // ambient light proxy (input-only, ADC1)
static const int PIR_PIN = 27;  // motion/presence proxy
static const int TRIG_PIN = 26; // HC-SR04 trigger
static const int ECHO_PIN = 25; // HC-SR04 echo
static const int LED_PIN = 32;  // street light actuator (PWM)

static const int LEDC_CHANNEL = 0;
static const int LEDC_FREQ_HZ = 5000;
static const int LEDC_RESOLUTION_BITS = 8; // duty range 0-255

static const float VEHICLE_PROXIMITY_THRESHOLD_CM = 150.0;
static const unsigned long HC_SR04_TIMEOUT_US = 30000UL; // ~5m max range

static const unsigned long TELEMETRY_INTERVAL_MS = 15000UL;
static const unsigned long TOKEN_REFRESH_INTERVAL_MS = 45UL * 60UL * 1000UL; // 45 min, tokens expire at 60

// --- State -----------------------------------------------------------------

String accessToken = "";
unsigned long loginTimeMillis = 0;
float currentBrightnessPct = 50.0; // reported actuator state, updated by applyBrightness()

// --- Setup helpers -----------------------------------------------------

void connectWiFi() {
  Serial.print("Connecting to WiFi");
  WiFi.begin(WIFI_SSID, "", 6);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println(" connected!");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

void syncTime() {
  Serial.print("Syncing time via NTP");
  configTime(0, 0, "pool.ntp.org"); // UTC, no DST -- matches backend's naive-UTC convention
  struct tm timeinfo;
  int attempts = 0;
  while (!getLocalTime(&timeinfo) && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  Serial.println(getLocalTime(&timeinfo) ? " synced!" : " failed (will retry per-cycle)");
}

// --- Sensor reads --------------------------------------------------------

float readAmbientLightPct() {
  int raw = analogRead(POT_PIN); // ESP32 ADC: 0-4095
  return (raw / 4095.0f) * 100.0f;
}

float readDistanceCm(bool &valid) {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  unsigned long duration = pulseIn(ECHO_PIN, HIGH, HC_SR04_TIMEOUT_US);
  if (duration == 0) {
    valid = false;
    return 0.0f;
  }
  valid = true;
  return duration / 58.0f; // standard HC-SR04 microseconds-to-cm conversion
}

String getIsoTimestamp() {
  struct tm timeinfo;
  if (!getLocalTime(&timeinfo)) {
    return String("1970-01-01T00:00:00"); // NTP not synced yet -- backend still accepts it
  }
  char buf[20]; // "YYYY-MM-DDTHH:MM:SS" + NUL
  strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%S", &timeinfo);
  return String(buf);
}

// --- Actuator --------------------------------------------------------------

void applyBrightness(float brightnessPct) {
  brightnessPct = constrain(brightnessPct, 0.0f, 100.0f);
  currentBrightnessPct = brightnessPct;
  int duty = (int)round(brightnessPct / 100.0f * 255.0f);
  ledcWrite(LEDC_CHANNEL, duty);
}

// --- Backend calls -----------------------------------------------------

bool login() {
  WiFiClientSecure client;
  client.setInsecure(); // documented scope cut -- see file header

  HTTPClient http;
  String url = String(BACKEND_BASE_URL) + "/auth/login";
  http.begin(client, url);
  http.addHeader("Content-Type", "application/json");

  JsonDocument doc;
  doc["username"] = DEVICE_USERNAME;
  doc["password"] = DEVICE_PASSWORD;
  String body;
  serializeJson(doc, body);

  int statusCode = http.POST(body);
  bool success = false;

  if (statusCode == 200) {
    String responseBody = http.getString();
    JsonDocument responseDoc;
    DeserializationError err = deserializeJson(responseDoc, responseBody);
    if (!err) {
      accessToken = responseDoc["data"]["access_token"].as<String>();
      loginTimeMillis = millis();
      success = true;
      Serial.println("Login successful.");
    } else {
      Serial.println("Login response JSON parse failed.");
    }
  } else {
    Serial.printf("Login failed, HTTP status=%d\n", statusCode);
  }

  http.end();
  return success;
}

void sendTelemetry() {
  float ambientPct = readAmbientLightPct();
  bool pirTriggered = digitalRead(PIR_PIN) == HIGH;

  bool distanceValid;
  float distanceCm = readDistanceCm(distanceValid);
  bool vehicleDetected = distanceValid && distanceCm < VEHICLE_PROXIMITY_THRESHOLD_CM;

  JsonDocument doc;
  doc["timestamp"] = getIsoTimestamp();
  doc["ambient_light_pct"] = ambientPct;
  doc["pir_triggered"] = pirTriggered;
  if (distanceValid) {
    doc["distance_cm"] = distanceCm;
  } else {
    doc["distance_cm"] = nullptr;
  }
  doc["vehicle_detected"] = vehicleDetected;
  doc["led_brightness_pct"] = currentBrightnessPct;

  String body;
  serializeJson(doc, body);

  WiFiClientSecure client;
  client.setInsecure(); // documented scope cut -- see file header

  HTTPClient http;
  String url = String(BACKEND_BASE_URL) + "/lamps/" + DEVICE_ID + "/telemetry";
  http.begin(client, url);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("Authorization", "Bearer " + accessToken);

  int statusCode = http.POST(body);

  if (statusCode == 200 || statusCode == 201) {
    String responseBody = http.getString();
    JsonDocument responseDoc;
    DeserializationError err = deserializeJson(responseDoc, responseBody);
    if (!err) {
      float targetBrightness = responseDoc["data"]["brightness_pct"] | currentBrightnessPct;
      applyBrightness(targetBrightness);
      Serial.printf(
          "Telemetry OK. ambient=%.1f%% pir=%d dist=%.1fcm vehicle=%d -> brightness=%.1f%%\n",
          ambientPct, pirTriggered, distanceCm, vehicleDetected, targetBrightness);
    } else {
      Serial.println("Telemetry response JSON parse failed.");
    }
  } else if (statusCode == 401) {
    Serial.println("Telemetry auth failed (401) -- forcing re-login next cycle.");
    accessToken = "";
  } else {
    Serial.printf("Telemetry POST failed, HTTP status=%d\n", statusCode);
  }

  http.end();
}

// --- Arduino entry points ------------------------------------------------

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("Smart City Lamp Node booting...");

  pinMode(PIR_PIN, INPUT);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  ledcSetup(LEDC_CHANNEL, LEDC_FREQ_HZ, LEDC_RESOLUTION_BITS);
  ledcAttachPin(LED_PIN, LEDC_CHANNEL);
  applyBrightness(currentBrightnessPct);

  connectWiFi();
  syncTime();

  if (!login()) {
    Serial.println("Initial login failed -- will keep retrying in loop().");
  }
}

void loop() {
  bool needsLogin = accessToken.length() == 0 ||
                     (millis() - loginTimeMillis) > TOKEN_REFRESH_INTERVAL_MS;
  if (needsLogin) {
    login();
  }

  if (accessToken.length() > 0) {
    sendTelemetry();
  }

  delay(TELEMETRY_INTERVAL_MS);
}
