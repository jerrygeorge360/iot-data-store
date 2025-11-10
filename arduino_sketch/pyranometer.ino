/*
 * Unified Solar Still Monitoring & Control System
 *
 * Features:
 * - Supports BOTH conventional (manual) and automated (pump) systems
 * - Mode selection via #define at compile time
 * - 5 Thermistors (T1-T5) with 10-second averaging
 * - DS1307 RTC for timestamping
 * - Water Level Sensor with visual monitoring
 * - WiFi + MQTT for cloud data upload (10-minute intervals)
 * - Optional pump control for automated systems
 *
 * Usage:
 * - Set SYSTEM_MODE to either CONVENTIONAL or AUTOMATED
 * - Configure WiFi and MQTT broker credentials
 * - Adjust pump thresholds if using automated mode
 */

#include <Wire.h>
#include <RTClib.h>
#include <math.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// ===== SYSTEM MODE CONFIGURATION =====
#define CONVENTIONAL 0
#define AUTOMATED 1
#define SYSTEM_MODE AUTOMATED  // Change to CONVENTIONAL for manual systems

// ===== PIN DEFINITIONS =====
// Thermistors
#define T1_PIN 32
#define T2_PIN 33
#define T3_PIN 27
#define T4_PIN 35
#define T5_PIN 25

// Water Level Sensor
#define WATER_LEVEL 34

// Pump Control (only used in AUTOMATED mode)
#define PUMP_PIN 26

// RTC I2C Pins
#define SDA_PIN 21
#define SCL_PIN 22

// ===== WATER LEVEL CONFIGURATION =====
#if SYSTEM_MODE == AUTOMATED
  #define WATER_OFF_LEVEL 3500   // 3.5cm - pump turns OFF
  #define WATER_ON_LEVEL  1000   // 1.0cm - pump turns ON
#else
  #define WATER_ALERT_LEVEL 1000 // 1.0cm - manual top-up alert
#endif

// Water Level Reading Parameters
#define READ_INTERVAL 100      // every 100ms
#define AVG_COUNT 10           // number of readings to average
#define SCALE_MIN 0
#define SCALE_MAX 4000         // 4cm full scale (1000 units = 1cm)

// ===== THERMISTOR CONFIGURATION =====
const float THERMISTOR_NOMINAL = 10000.0;
const float TEMP_NOMINAL = 25.0;
const float B_COEFFICIENT = 2850.0;
const float SERIES_RESISTOR = 56000.0;

const int SAMPLE_COUNT = 8;           // per reading
const int AVERAGE_WINDOW = 10;        // 10-second averaging
const int THERM_READ_INTERVAL = 1000; // 1s per reading
const int CLOUD_UPLOAD_INTERVAL = 600000; // 10 minutes

// Thermistor calibration offsets
float offsets[5] = {-13.0, -13.0, 38.0, -10.2, 37.0};

// ===== WIFI & MQTT CONFIGURATION =====
const char* WIFI_SSID = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char* MQTT_BROKER = "localhost";  // Change to your broker address
const int MQTT_PORT = 1883;
const char* MQTT_TOPIC = "sensors/data";
const char* MQTT_CLIENT_ID = "solar_still_esp32";

// ===== SYSTEM VARIABLES =====
RTC_DS1307 rtc;
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);

// Water Level Variables
int rawReadings[AVG_COUNT];
int rawIndex = 0;
unsigned long lastReadTime = 0;
int readingCount = 0;
int minRaw = 4095, maxRaw = 0;
int minScaled = SCALE_MAX, maxScaled = SCALE_MIN;
bool pumpState = false;
float currentWaterLevel = 0.0;
int currentRawADC = 0;

// Thermistor Variables
float tempBuffer[5][AVERAGE_WINDOW];
int tempBufferIndex = 0;
unsigned long lastThermReadTime = 0;
unsigned long lastCloudUploadTime = 0;
int thermReadingCount = 0;

// MQTT reconnection
unsigned long lastMqttReconnect = 0;
const long mqttReconnectInterval = 5000;

void setup() {
  Serial.begin(115200);
  delay(1000);

  printSystemHeader();

  // Initialize I/O Pins
  pinMode(WATER_LEVEL, INPUT);

#if SYSTEM_MODE == AUTOMATED
  pinMode(PUMP_PIN, OUTPUT);
  digitalWrite(PUMP_PIN, LOW); // Start with pump OFF
#endif

  // Initialize Thermistor Pins
  analogReadResolution(12);
  analogSetPinAttenuation(T1_PIN, ADC_11db);
  analogSetPinAttenuation(T2_PIN, ADC_11db);
  analogSetPinAttenuation(T3_PIN, ADC_11db);
  analogSetPinAttenuation(T4_PIN, ADC_11db);
  analogSetPinAttenuation(T5_PIN, ADC_11db);

  // Initialize RTC
  setupRTC();

  // Initialize WiFi and MQTT
  setupWiFi();
  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);

  // Initialize water level reading array
  for (int i = 0; i < AVG_COUNT; i++) {
    rawReadings[i] = analogRead(WATER_LEVEL);
  }

  printSystemConfig();

  lastCloudUploadTime = millis();
}

void loop() {
  unsigned long currentMillis = millis();

  // Maintain MQTT connection
  if (!mqttClient.connected()) {
    if (currentMillis - lastMqttReconnect > mqttReconnectInterval) {
      reconnectMQTT();
      lastMqttReconnect = currentMillis;
    }
  }
  mqttClient.loop();

  // Water Level Monitoring
  if (currentMillis - lastReadTime >= READ_INTERVAL) {
    processWaterLevel();
    lastReadTime = currentMillis;
  }

  // Thermistor Readings
  if (currentMillis - lastThermReadTime >= THERM_READ_INTERVAL) {
    processThermistors();
    lastThermReadTime = currentMillis;
    thermReadingCount++;
  }

  // Cloud Upload via MQTT
  if (currentMillis - lastCloudUploadTime >= CLOUD_UPLOAD_INTERVAL) {
    uploadToCloud();
    lastCloudUploadTime = currentMillis;
  }
}

void printSystemHeader() {
  Serial.println("\n\n╔══════════════════════════════════════════════════╗");
#if SYSTEM_MODE == AUTOMATED
  Serial.println("║   AUTOMATED SOLAR STILL MONITORING SYSTEM       ║");
#else
  Serial.println("║   CONVENTIONAL SOLAR STILL MONITORING SYSTEM    ║");
#endif
  Serial.println("╚══════════════════════════════════════════════════╝");
}

void printSystemConfig() {
  Serial.println("\n══════════════════════════════════════════════════");
  Serial.println("SYSTEM CONFIGURATION:");
  Serial.println("══════════════════════════════════════════════════");
#if SYSTEM_MODE == AUTOMATED
  Serial.println("Mode: AUTOMATED (Pump Control Enabled)");
  Serial.print("Pump ON Threshold: ");
  Serial.print(WATER_ON_LEVEL / 1000.0, 1);
  Serial.println(" cm");
  Serial.print("Pump OFF Threshold: ");
  Serial.print(WATER_OFF_LEVEL / 1000.0, 1);
  Serial.println(" cm");
#else
  Serial.println("Mode: CONVENTIONAL (Manual Top-up)");
  Serial.print("Low Water Alert: ");
  Serial.print(WATER_ALERT_LEVEL / 1000.0, 1);
  Serial.println(" cm");
#endif
  Serial.println("Data Upload: Every 10 minutes via MQTT");
  Serial.print("MQTT Broker: ");
  Serial.print(MQTT_BROKER);
  Serial.print(":");
  Serial.println(MQTT_PORT);
  Serial.println("══════════════════════════════════════════════════\n");
}

void processWaterLevel() {
  int raw = analogRead(WATER_LEVEL);
  rawReadings[rawIndex++] = raw;
  if (rawIndex >= AVG_COUNT) rawIndex = 0;
  readingCount++;

  if (readingCount >= AVG_COUNT) {
    long sum = 0;
    for (int i = 0; i < AVG_COUNT; i++) sum += rawReadings[i];
    int avgRaw = sum / AVG_COUNT;

    if (avgRaw < minRaw) minRaw = avgRaw;
    if (avgRaw > maxRaw) maxRaw = avgRaw;

    int scaled = map(avgRaw, minRaw, maxRaw, SCALE_MIN, SCALE_MAX);
    scaled = constrain(scaled, SCALE_MIN, SCALE_MAX);

    if (scaled < minScaled) minScaled = scaled;
    if (scaled > maxScaled) maxScaled = scaled;

    currentWaterLevel = scaled / 1000.0;
    currentRawADC = avgRaw;

    displayWaterLevel(avgRaw, scaled);

#if SYSTEM_MODE == AUTOMATED
    controlPump(scaled);
#else
    checkWaterLevelAlert(scaled);
#endif
  }
}

void displayWaterLevel(int raw, int scaled) {
  DateTime now = rtc.now();

  Serial.print("WATER [");
  Serial.print(now.hour()); Serial.print(":");
  if (now.minute() < 10) Serial.print("0");
  Serial.print(now.minute()); Serial.print(":");
  if (now.second() < 10) Serial.print("0");
  Serial.print(now.second());
  Serial.print("] ");

  Serial.print("Raw:"); Serial.print(raw);
  Serial.print(" Depth:"); Serial.print(scaled / 1000.0, 2); Serial.print("cm");

#if SYSTEM_MODE == AUTOMATED
  Serial.print(" Pump:"); Serial.print(pumpState ? "ON " : "OFF");
#endif

  Serial.print(" [");

  int barLength = 20;
  int filled = map(scaled, SCALE_MIN, SCALE_MAX, 0, barLength);
  filled = constrain(filled, 0, barLength);

  for (int i = 0; i < barLength; i++) {
    if (i < filled) Serial.print("█");
    else Serial.print("░");
  }
  Serial.println("]");
}

#if SYSTEM_MODE == AUTOMATED
void controlPump(int currentLevel) {
  bool previousState = pumpState;

  if (currentLevel <= WATER_ON_LEVEL && !pumpState) {
    pumpState = true;
    digitalWrite(PUMP_PIN, HIGH);
  }
  else if (currentLevel >= WATER_OFF_LEVEL && pumpState) {
    pumpState = false;
    digitalWrite(PUMP_PIN, LOW);
  }

  if (previousState != pumpState) {
    Serial.println("══════════════════════════════════════════════════");
    Serial.print("PUMP STATUS: ");
    Serial.println(pumpState ? "TURNED ON" : "TURNED OFF");
    Serial.print("Water level: ");
    Serial.print(currentLevel / 1000.0, 2);
    Serial.println(" cm");
    Serial.println("══════════════════════════════════════════════════");
  }
}
#else
void checkWaterLevelAlert(int currentLevel) {
  static unsigned long lastAlertTime = 0;
  static bool alertShown = false;

  if (currentLevel < WATER_ALERT_LEVEL) {
    unsigned long currentTime = millis();

    if (currentTime - lastAlertTime >= 30000 || !alertShown) {
      Serial.println("══════════════════════════════════════════════════");
      Serial.println("⚠️  ALERT: Water level is LOW!");
      Serial.print("Current level: ");
      Serial.print(currentLevel / 1000.0, 2);
      Serial.println(" cm");
      Serial.println("Manual top-up required!");
      Serial.println("══════════════════════════════════════════════════");
      lastAlertTime = currentTime;
      alertShown = true;
    }
  } else {
    alertShown = false;
  }
}
#endif

void processThermistors() {
  tempBuffer[0][tempBufferIndex] = readThermistor(T1_PIN, offsets[0]);
  tempBuffer[1][tempBufferIndex] = readThermistor(T2_PIN, offsets[1]);
  tempBuffer[2][tempBufferIndex] = readThermistor(T3_PIN, offsets[2]);
  tempBuffer[3][tempBufferIndex] = readThermistor(T4_PIN, offsets[3]);
  tempBuffer[4][tempBufferIndex] = readThermistor(T5_PIN, offsets[4]);

  tempBufferIndex++;

  if (tempBufferIndex >= AVERAGE_WINDOW) {
    displayAveragedTemperatures();
    tempBufferIndex = 0;
  }
}

void displayAveragedTemperatures() {
  DateTime now = rtc.now();

  Serial.println("\n=== 10-SECOND AVERAGED TEMPERATURES ===");
  Serial.print("Time: ");
  Serial.print(now.hour()); Serial.print(":");
  if (now.minute() < 10) Serial.print("0");
  Serial.print(now.minute()); Serial.print(":");
  if (now.second() < 10) Serial.print("0");
  Serial.println(now.second());

  for (int i = 0; i < 5; i++) {
    float sum = 0;
    int validCount = 0;

    for (int j = 0; j < AVERAGE_WINDOW; j++) {
      if (!isnan(tempBuffer[i][j])) {
        sum += tempBuffer[i][j];
        validCount++;
      }
    }

    float avg = (validCount > 0) ? sum / validCount : NAN;

    Serial.print("T");
    Serial.print(i + 1);
    Serial.print(": ");
    if (!isnan(avg)) {
      Serial.print(avg, 2);
      Serial.println(" °C");
    } else {
      Serial.println("ERROR");
    }
  }
  Serial.println("----------------------------------------\n");
}

void uploadToCloud() {
  DateTime now = rtc.now();

  Serial.println("══════════════════════════════════════════════════");
  Serial.println("UPLOADING DATA TO CLOUD VIA MQTT...");
  Serial.println("══════════════════════════════════════════════════");

  // Calculate averaged temperatures
  float uploadTemps[5];
  float avgTemp = 0;
  int validTempCount = 0;

  for (int i = 0; i < 5; i++) {
    float sum = 0;
    int validCount = 0;

    for (int j = 0; j < AVERAGE_WINDOW; j++) {
      if (!isnan(tempBuffer[i][j])) {
        sum += tempBuffer[i][j];
        validCount++;
      }
    }

    uploadTemps[i] = (validCount > 0) ? sum / validCount : NAN;

    if (!isnan(uploadTemps[i])) {
      avgTemp += uploadTemps[i];
      validTempCount++;
    }

    Serial.print("T");
    Serial.print(i + 1);
    Serial.print(": ");
    if (!isnan(uploadTemps[i])) {
      Serial.print(uploadTemps[i], 2);
      Serial.println(" °C");
    } else {
      Serial.println("ERROR");
    }
  }

  avgTemp = (validTempCount > 0) ? avgTemp / validTempCount : 0.0;

  Serial.println("--- WATER LEVEL ---");
  Serial.print("Raw ADC: ");
  Serial.println(currentRawADC);
  Serial.print("Depth: ");
  Serial.print(currentWaterLevel, 2);
  Serial.println(" cm");

#if SYSTEM_MODE == AUTOMATED
  Serial.print("Pump: ");
  Serial.println(pumpState ? "ON" : "OFF");
#endif

  // Create and send JSON payload
  publishMQTT(uploadTemps, avgTemp, now);

  Serial.println("Data uploaded successfully!");
  Serial.println("══════════════════════════════════════════════════\n");
}
void publishMQTT(float temps[5], float avgTemp, DateTime timestamp) {
  StaticJsonDocument<512> doc;

  // System identification
#if SYSTEM_MODE == AUTOMATED
  doc["system_type"] = "automated";
  doc["pump_status"] = pumpState ? "ON" : "OFF";
#else
  doc["system_type"] = "conventional";
#endif

  // Timestamp
  char timeStr[32];
  snprintf(timeStr, sizeof(timeStr), "%04d-%02d-%02d %02d:%02d:%02d",
           timestamp.year(), timestamp.month(), timestamp.day(),
           timestamp.hour(), timestamp.minute(), timestamp.second());
  doc["time_stamp"] = timeStr;

  // Average temperature
  doc["temperature"] = avgTemp;

  // Helper lambda to reduce repetition
  auto addTemp = [&](const char* key, float value) {
    if (!isnan(value))
      doc[key] = value;
    else
      doc[key] = nullptr;  // JSON null if sensor failed
  };

  // Add thermistor readings
  addTemp("temp1", temps[0]);
  addTemp("temp2", temps[1]);
  addTemp("temp3", temps[2]);
  addTemp("temp4", temps[3]);
  addTemp("temp5", temps[4]);

  // Water level data
  JsonObject water = doc.createNestedObject("water_level");
  water["raw_adc"] = currentRawADC;
  water["depth_cm"] = currentWaterLevel;

  // Serialize and publish
  char buffer[512];
  serializeJson(doc, buffer);

  Serial.print("MQTT Payload: ");
  Serial.println(buffer);

  if (mqttClient.connected()) {
    if (mqttClient.publish(MQTT_TOPIC, buffer)) {
      Serial.println("✓ MQTT publish successful");
    } else {
      Serial.println("✗ MQTT publish failed");
    }
  } else {
    Serial.println("✗ MQTT not connected");
  }
}

float readThermistor(int pin, float offset) {
  long sum = 0;
  for (int i = 0; i < SAMPLE_COUNT; i++) {
    sum += analogRead(pin);
    delay(5);
  }
  float adc = (float)sum / SAMPLE_COUNT;

  if (adc < 10.0 || adc > 5200.0) return NAN;

  float vRatio = (4095.0 / adc) - 1.0;
  if (vRatio <= 0.0) return NAN;

  float Rth = SERIES_RESISTOR / vRatio;
  float steinhart = log(Rth / THERMISTOR_NOMINAL) / B_COEFFICIENT;
  steinhart += 1.0 / (TEMP_NOMINAL + 273.15);
  steinhart = 1.0 / steinhart;
  float tempC = steinhart - 273.15;

  return tempC + offset;
}

void setupRTC() {
  Serial.println("Initializing RTC...");

  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.setClock(100000);

  if (!rtc.begin()) {
    Serial.println("ERROR: RTC not found!");
    Serial.println("Check wiring: SDA=21, SCL=22, VCC=5V");
    while (1) delay(1000);
  }

  Serial.println("✓ RTC found!");

  if (!rtc.isrunning()) {
    Serial.println("RTC not running, setting time...");
    rtc.adjust(DateTime(__DATE__, __TIME__));
  }

  DateTime now = rtc.now();
  Serial.print("RTC Time: ");
  Serial.print(now.year()); Serial.print("-");
  Serial.print(now.month()); Serial.print("-");
  Serial.print(now.day()); Serial.print(" ");
  Serial.print(now.hour()); Serial.print(":");
  Serial.print(now.minute()); Serial.print(":");
  Serial.println(now.second());
}

void setupWiFi() {
  Serial.println("Connecting to WiFi...");
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✓ WiFi connected!");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n✗ WiFi connection failed!");
  }
}

void reconnectMQTT() {
  if (!mqttClient.connected()) {
    Serial.print("Connecting to MQTT broker...");

    if (mqttClient.connect(MQTT_CLIENT_ID)) {
      Serial.println(" ✓ Connected!");
    } else {
      Serial.print(" ✗ Failed, rc=");
      Serial.println(mqttClient.state());
    }
  }
}