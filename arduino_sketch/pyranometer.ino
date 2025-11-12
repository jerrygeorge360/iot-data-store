/*
ESP32 Thermistor - Read as Voltage Instead of Temperature
*/

#include <WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <RTClib.h>
#include <BH1750.h>
#include <LiquidCrystal_I2C.h>

// ========== WiFi & MQTT Settings ==========
const char* WIFI_SSID     = "Bionic";
const char* WIFI_PASSWORD = "12345678";
const char* MQTT_BROKER   = "134.112.56.111";
const int   MQTT_PORT     = 1884;
const char* MQTT_TOPIC    = "sensors/data";
const char* CLIENT_ID     = "ESP32_Client_1";

// ========== Pin Definitions ==========
#define THERMISTOR1_PIN 33
#define THERMISTOR2_PIN 32
#define SDA_PIN 21
#define SCL_PIN 22

// ========== ADC Configuration ==========
#define ADC_MAX 4095
#define ADC_VREF 3.3  // ESP32 reference voltage

// ========== Objects ==========
WiFiClient espClient;
PubSubClient client(espClient);
RTC_DS1307 rtc;
BH1750 lightMeter;
LiquidCrystal_I2C lcd(0x27, 16, 2);

// ========== Function Prototypes ==========
void connectWiFi();
void connectMQTT();
void publishSensorData();
void initI2C();
void scanI2C();
float readThermistorVoltage(int pin);
int readThermistorRaw(int pin);
void lcdStatus(const String &line1, const String &line2);

// ========== Setup ==========
void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n=== ESP32 Multi-Sensor MQTT System (Voltage Mode) ===");

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

  lcdStatus("System Ready", "Voltage Mode");
  Serial.println("\n=== System Ready - Voltage Mode ===");
}

// ========== Main Loop ==========
void loop() {
  if (!client.connected()) connectMQTT();
  if (WiFi.status() != WL_CONNECTED) connectWiFi();
  client.loop();

  static unsigned long lastMsg = 0;
  unsigned long now = millis();

  if (now - lastMsg > 3600000) {
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

// ========== Read Raw ADC Value ==========
int readThermistorRaw(int pin) {
  return analogRead(pin);
}

// ========== Read Thermistor Voltage ==========
float readThermistorVoltage(int pin) {
  int adcValue = analogRead(pin);
  // Convert ADC reading to voltage
  float voltage = (adcValue / (float)ADC_MAX) * ADC_VREF;
  return voltage;
}

// ========== Publish Sensor Data ==========
void publishSensorData() {
  Serial.println("\n=== Reading Sensors ===");

  // Read as voltage
  float voltage1 = readThermistorVoltage(THERMISTOR1_PIN);
  float voltage2 = readThermistorVoltage(THERMISTOR2_PIN);
  float voltageDifference = abs((voltage1 - voltage2));

  // Read raw ADC values (optional)
  int raw1 = readThermistorRaw(THERMISTOR1_PIN);
  int raw2 = readThermistorRaw(THERMISTOR2_PIN);

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

  // Build JSON payload with voltage data
  String payload = "{";
  payload += "\"voltage_difference\":" + String(voltageDifference, 3);
  payload += ",\"voltage1\":" + String(voltage1, 3);
  payload += ",\"voltage2\":" + String(voltage2, 3);
  payload += ",\"adc_raw1\":" + String(raw1);
  payload += ",\"adc_raw2\":" + String(raw2);
  payload += ",\"light_intensity\":" + String(lightIntensity, 1);
  payload += ",\"time_stamp\":\"" + String(timestamp) + "\"";
  payload += "}";

  // Print to serial for debugging
  Serial.println("--- Voltage Readings ---");
  Serial.print("Voltage 1: "); Serial.print(voltage1, 3); Serial.println(" V");
  Serial.print("Voltage 2: "); Serial.print(voltage2, 3); Serial.println(" V");
  Serial.print("ADC Raw 1: "); Serial.println(raw1);
  Serial.print("ADC Raw 2: "); Serial.println(raw2);
  Serial.println(payload);

  lcdStatus("Publishing...", "");

  if (client.publish(MQTT_TOPIC, payload.c_str())) {
    Serial.println("✓ Published successfully!");
    lcdStatus("Data Sent ✓", "V1:" + String(voltage1, 2) + " V2:" + String(voltage2, 2));
  } else {
    Serial.println("✗ Publish failed!");
    lcdStatus("Publish Failed", "Retry later");
  }
  delay(1500);
}