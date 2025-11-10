/*
ESP32 Multi-Sensor MQTT Publisher + LCD Status Display
Sensors: DS1307 RTC, BH1750 Light Sensor, 2x Thermistors
Displays WiFi/MQTT status and sensor data on a 16x2 I2C LCD
*/

#include <WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <RTClib.h>
#include <BH1750.h>
#include <LiquidCrystal_I2C.h>

// ========== WiFi & MQTT Settings ==========
const char* WIFI_SSID     = "Bionic";
const char* WIFI_PASSWORD = ""; // or NULL if open network
const char* MQTT_BROKER   = "192.168.17.234";
const int   MQTT_PORT     = 1884;
const char* MQTT_TOPIC    = "sensors/data";
const char* CLIENT_ID     = "ESP32_Client_1";

// ========== Pin Definitions ==========
#define THERMISTOR1_PIN 33
#define THERMISTOR2_PIN 32
#define SDA_PIN 21
#define SCL_PIN 22

// ========== Thermistor Configuration ==========
#define THERMISTOR_NOMINAL 10000
#define TEMPERATURE_NOMINAL 25
#define B_COEFFICIENT 3950
#define SERIES_RESISTOR 10000
#define ADC_MAX 4095

// ========== Objects ==========
WiFiClient espClient;
PubSubClient client(espClient);
RTC_DS1307 rtc;
BH1750 lightMeter;
LiquidCrystal_I2C lcd(0x27, 16, 2);  // I2C LCD (address may be 0x3F on some modules)

// ========== Function Prototypes ==========
void connectWiFi();
void connectMQTT();
void publishSensorData();
void initI2C();
void scanI2C();
float readThermistor(int pin);
void lcdStatus(const String &line1, const String &line2);

// ========== Setup ==========
void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n=== ESP32 Multi-Sensor MQTT System ===");

  // Initialize LCD
  lcd.init();
  lcd.backlight();
  lcdStatus("ESP32 Booting...", "");

  // Configure thermistor pins
  pinMode(THERMISTOR1_PIN, INPUT);
  pinMode(THERMISTOR2_PIN, INPUT);
  Serial.println("✓ Thermistor pins configured (GPIO 33, 32)");

  // Initialize I2C
  initI2C();

  // Initialize RTC
  Serial.println("\n--- Initializing DS1307 RTC ---");
  if (!rtc.begin()) {
    Serial.println("ERROR: DS1307 not found!");
    lcdStatus("RTC not found!", "");
  } else {
    Serial.println("✓ DS1307 RTC initialized");
    if (!rtc.isrunning()) {
      Serial.println("WARNING: RTC not running, setting to compile time");
      rtc.adjust(DateTime(F(__DATE__), F(__TIME__)));
    }
  }

  // Initialize BH1750
  Serial.println("\n--- Initializing BH1750 Light Sensor ---");
  if (lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE)) {
    Serial.println("✓ BH1750 initialized");
  } else {
    Serial.println("ERROR: BH1750 initialization failed!");
    lcdStatus("BH1750 Fail", "");
  }

  // Connect WiFi
  connectWiFi();

  // Setup MQTT
  client.setServer(MQTT_BROKER, MQTT_PORT);

  lcdStatus("System Ready", "Starting...");
  Serial.println("\n=== System Ready ===");
}

// ========== Main Loop ==========
void loop() {
  if (!client.connected()) connectMQTT();
  if (WiFi.status() != WL_CONNECTED) connectWiFi();
  client.loop();

  static unsigned long lastMsg = 0;
  unsigned long now = millis();

  if (now - lastMsg > 60000) {
    lastMsg = now;
    publishSensorData();
  }
}

// ========== LCD Helper ==========
void lcdStatus(const String &line1, const String &line2) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(line1);
  lcd.setCursor(0, 1);
  lcd.print(line2);
}

// ========== Initialize I2C ==========
void initI2C() {
  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.setClock(100000);
  scanI2C();
}

// ========== Scan I2C Bus ==========
void scanI2C() {
  byte error, address;
  int deviceCount = 0;
  for (address = 1; address < 127; address++) {
    Wire.beginTransmission(address);
    error = Wire.endTransmission();
    if (error == 0) deviceCount++;
  }
  Serial.print("Found "); Serial.print(deviceCount); Serial.println(" I2C devices");
}

// ========== Connect to WiFi ==========
void connectWiFi() {
  lcdStatus("Connecting WiFi", WIFI_SSID);
  Serial.print("\nConnecting to WiFi: "); Serial.println(WIFI_SSID);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  int retries = 0;

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    retries++;
    if (retries > 30) {
      lcdStatus("WiFi Failed", "Restarting...");
      ESP.restart();
    }
  }

  Serial.println();
  Serial.print("✓ WiFi connected! IP: ");
  Serial.println(WiFi.localIP());
  lcdStatus("WiFi Connected!", WiFi.localIP().toString());
  delay(1500);
}

// ========== Connect to MQTT Broker ==========
void connectMQTT() {
  lcdStatus("Connecting MQTT", MQTT_BROKER);
  Serial.print("\nConnecting to MQTT Broker: ");
  Serial.println(MQTT_BROKER);

  while (!client.connected()) {
    if (client.connect(CLIENT_ID)) {
      Serial.println("✓ Connected to MQTT!");
      lcdStatus("MQTT Connected", "");
    } else {
      Serial.print("Failed, rc=");
      Serial.print(client.state());
      Serial.println(" retrying...");
      lcdStatus("MQTT Retry", "rc=" + String(client.state()));
      delay(3000);
    }
  }
}

// ========== Read Thermistor Temperature ==========
float readThermistor(int pin) {
  int adcValue = analogRead(pin);
  if (adcValue == 0) return -999.0;

  float resistance = SERIES_RESISTOR / ((ADC_MAX / (float)adcValue) - 1.0);
  float steinhart;
  steinhart = resistance / THERMISTOR_NOMINAL;
  steinhart = log(steinhart);
  steinhart /= B_COEFFICIENT;
  steinhart += 1.0 / (TEMPERATURE_NOMINAL + 273.15);
  steinhart = 1.0 / steinhart;
  steinhart -= 273.15;
  return steinhart;
}

// ========== Publish Sensor Data ==========
void publishSensorData() {
  Serial.println("\n=== Reading Sensors ===");

  float temp1 = readThermistor(THERMISTOR1_PIN);
  float temp2 = readThermistor(THERMISTOR2_PIN);
  float avgTemp = (temp1 + temp2) / 2.0;
  float lightIntensity = lightMeter.readLightLevel();
  if (lightIntensity < 0) lightIntensity = 0;

  char timestamp[25];
  if (rtc.isrunning()) {
    DateTime now = rtc.now();
    snprintf(timestamp, sizeof(timestamp), "%04d-%02d-%02d %02d:%02d:%02d",
             now.year(), now.month(), now.day(),
             now.hour(), now.minute(), now.second());
  } else {
    snprintf(timestamp, sizeof(timestamp), "FallbackTime");
  }

  String payload = "{";
  payload += "\"temperature\":" + String(avgTemp, 2);
  payload += ",\"light_intensity\":" + String(lightIntensity, 1);
  payload += ",\"timestamp\":\"" + String(timestamp) + "\"";
  payload += "}";

  Serial.println(payload);
  lcdStatus("Publishing...", "");

  if (client.publish(MQTT_TOPIC, payload.c_str())) {
    Serial.println("✓ Published successfully!");
    lcdStatus("Data Sent ✓", "T:" + String(avgTemp, 1) + "C L:" + String(lightIntensity, 0));
  } else {
    Serial.println("✗ Publish failed!");
    lcdStatus("Publish Failed", "Retry later");
  }
  delay(1500);
}
