#include <WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>
#include "RTClib.h"

// WiFi & MQTT Settings
const char* WIFI_SSID     = "Bionic";
const char* WIFI_PASSWORD = NULL;

const char* MQTT_BROKER   = "10.62.118.234";
const int   MQTT_PORT     = 1884;
const char* MQTT_TOPIC    = "sensors/data";
const char* CLIENT_ID     = "ESP32_Client_1";

// Objects
WiFiClient espClient;
PubSubClient client(espClient);
RTC_DS3231 rtc;

// Function Prototypes
void connectWiFi();
void connectMQTT();
void publishSensorData();

// Setup
void setup() {
  Serial.begin(115200);
  delay(100);
  // Serial.println("Couldn't find RTC, check wiring!");


  // // RTC init
  // if (!rtc.begin()) {
  //   Serial.println("Couldn't find RTC, check wiring!");
  //   while (1);
  // }
  // if (rtc.lostPower()) {
  //   Serial.println("RTC lost power, setting to compile time");
  //   rtc.adjust(DateTime(F(__DATE__), F(__TIME__)));
  // }

  connectWiFi();
  client.setServer(MQTT_BROKER, MQTT_PORT);
}

// Loop
void loop() {
  if (!client.connected()) {
    connectMQTT();
  }
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
  }

  client.loop();  // keep MQTT connection alive

  static unsigned long lastMsg = 0;
  unsigned long now = millis();

  if (now - lastMsg > 60000) { // every 60 seconds
    lastMsg = now;
    publishSensorData();
  }
}

// Connect to WiFi
void connectWiFi() {
  Serial.print("Connecting to WiFi: ");
  Serial.println(WIFI_SSID);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int retries = 0;
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    retries++;
    if (retries > 30) { // ~15s timeout
      Serial.println(" Restarting ESP32 due to WiFi failure...");
      ESP.restart();
    }
  }
  Serial.println("\nWiFi connected, IP: " + WiFi.localIP().toString());
}

// Connect to MQTT Broker
void connectMQTT() {
  Serial.print("Connecting to MQTT Broker: ");
  Serial.println(MQTT_BROKER);

  while (!client.connected()) {
    if (client.connect(CLIENT_ID)) {
      Serial.println("Connected to MQTT!");
    } else {
      Serial.print("Failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 3s");
      delay(3000);
    }
  }
}

// Publish Data
void publishSensorData() {
  // Fake data for demo (replace with actual sensor readings)
  float temperature = random(200, 300) / 10.0; // fake (20.0 - 30.0)
  float light_intensity = random(100, 500) / 1.0; // fake lux

  char timestamp[25] = "2025-09-08T18:15:30Z";
  // Get RTC timestamp
  // DateTime now = rtc.now();

  // char timestamp[25];
  // snprintf(timestamp, sizeof(timestamp),
  //          "%04d-%02d-%02d %02d:%02d:%02d",
  //          now.year(), now.month(), now.day(),
  //          now.hour(), now.minute(), now.second());

  // JSON payload (matching backend column names)
  String payload = "{\"temperature\":" + String(temperature) +
                   ", \"light_intensity\":" + String(light_intensity) +
                   ", \"time_stamp\":\"" + String(timestamp) + "\"}";

  if (client.publish(MQTT_TOPIC, payload.c_str())) {
    Serial.println("Published: " + payload);
  } else {
    Serial.println("Publish failed, will retry...");
  }
}