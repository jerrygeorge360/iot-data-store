[//]: # (# Unified Solar Still Monitoring System)

[//]: # ()
[//]: # ([![License: MIT]&#40;https://img.shields.io/badge/License-MIT-yellow.svg&#41;]&#40;https://opensource.org/licenses/MIT&#41;)

[//]: # ([![Platform: ESP32]&#40;https://img.shields.io/badge/Platform-ESP32-blue.svg&#41;]&#40;https://www.espressif.com/en/products/socs/esp32&#41;)

[//]: # ([![Python: 3.8+]&#40;https://img.shields.io/badge/Python-3.8+-green.svg&#41;]&#40;https://www.python.org/&#41;)

[//]: # ([![FastAPI]&#40;https://img.shields.io/badge/FastAPI-0.100+-009688.svg&#41;]&#40;https://fastapi.tiangolo.com/&#41;)

[//]: # ()
[//]: # (A comprehensive IoT monitoring and control system for solar still desalination units. Supports both **conventional &#40;manual&#41;** and **automated &#40;pump-controlled&#41;** systems with real-time data collection, cloud storage, and analytics.)

[//]: # ()
[//]: # (---)

[//]: # ()
[//]: # (## 📋 Table of Contents)

[//]: # ()
[//]: # (- [Features]&#40;#-features&#41;)

[//]: # (- [System Architecture]&#40;#-system-architecture&#41;)

[//]: # (- [Hardware Requirements]&#40;#-hardware-requirements&#41;)

[//]: # (- [Software Requirements]&#40;#-software-requirements&#41;)

[//]: # (- [Installation]&#40;#-installation&#41;)

[//]: # (- [Configuration]&#40;#-configuration&#41;)

[//]: # (- [Usage]&#40;#-usage&#41;)

[//]: # (- [API Documentation]&#40;#-api-documentation&#41;)

[//]: # (- [Data Structure]&#40;#-data-structure&#41;)

[//]: # (- [Troubleshooting]&#40;#-troubleshooting&#41;)

[//]: # (- [Contributing]&#40;#-contributing&#41;)

[//]: # (- [License]&#40;#-license&#41;)

[//]: # ()
[//]: # (---)

[//]: # ()
[//]: # (## 🌟 Features)

[//]: # ()
[//]: # (### Hardware &#40;ESP32&#41;)

[//]: # (- ✅ **Dual Mode Support**: Conventional &#40;manual&#41; and Automated &#40;pump control&#41;)

[//]: # (- 🌡️ **5 Thermistors**: High-precision temperature monitoring &#40;T1-T5&#41;)

[//]: # (- 💧 **Water Level Sensing**: Real-time depth monitoring with visual indicators)

[//]: # (- ⏰ **RTC Integration**: Accurate timestamping with DS1307)

[//]: # (- 📡 **MQTT Communication**: Reliable cloud data upload every 10 minutes)

[//]: # (- 🔄 **Auto-Reconnection**: Robust WiFi and MQTT reconnection logic)

[//]: # (- 📊 **Data Averaging**: 10-second temperature averaging for stability)

[//]: # (- 🚨 **Smart Alerts**: Low water alerts &#40;conventional&#41; or automatic pump control &#40;automated&#41;)

[//]: # ()
[//]: # (### Backend &#40;FastAPI&#41;)

[//]: # (- 🗄️ **PostgreSQL Database**: Robust data storage with full history)

[//]: # (- 📈 **RESTful API**: Comprehensive endpoints for data access)

[//]: # (- 📊 **Real-time Statistics**: System performance analytics)

[//]: # (- 🔍 **Advanced Filtering**: Query by system type, time range, etc.)

[//]: # (- 📡 **MQTT Integration**: Automatic data ingestion from devices)

[//]: # (- 📉 **Prometheus Metrics**: Complete observability and monitoring)

[//]: # (- 🔐 **Environment-based Config**: Secure credential management)

[//]: # (- 🚀 **High Performance**: Async operations with FastAPI)

[//]: # ()
[//]: # (---)

[//]: # ()
[//]: # (## 🏗️ System Architecture)

[//]: # ()
[//]: # (```)

[//]: # (┌─────────────────────────────────────────────────────────────┐)

[//]: # (│                        ESP32 Device                         │)

[//]: # (│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │)

[//]: # (│  │   T1-T5  │  │  Water   │  │   RTC    │  │   Pump   │   │)

[//]: # (│  │Thermistors│ │  Level   │  │ DS1307   │  │&#40;Optional&#41;│   │)

[//]: # (│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │)

[//]: # (│       │             │              │             │          │)

[//]: # (│       └─────────────┴──────────────┴─────────────┘          │)

[//]: # (│                         │                                    │)

[//]: # (│                    ESP32 Main                                │)

[//]: # (│                         │                                    │)

[//]: # (└─────────────────────────┼────────────────────────────────────┘)

[//]: # (                          │)

[//]: # (                          │ WiFi + MQTT)

[//]: # (                          │)

[//]: # (                          ▼)

[//]: # (              ┌───────────────────────┐)

[//]: # (              │    MQTT Broker        │)

[//]: # (              │   &#40;Mosquitto/HiveMQ&#41;  │)

[//]: # (              └───────────┬───────────┘)

[//]: # (                          │)

[//]: # (                          ▼)

[//]: # (              ┌───────────────────────┐)

[//]: # (              │   FastAPI Backend     │)

[//]: # (              │   - REST API          │)

[//]: # (              │   - MQTT Subscriber   │)

[//]: # (              │   - Data Processing   │)

[//]: # (              └───────────┬───────────┘)

[//]: # (                          │)

[//]: # (                          ▼)

[//]: # (              ┌───────────────────────┐)

[//]: # (              │  PostgreSQL Database  │)

[//]: # (              │  - solar_still_data   │)

[//]: # (              │  - Time-series data   │)

[//]: # (              └───────────────────────┘)

[//]: # (                          │)

[//]: # (                          ▼)

[//]: # (              ┌───────────────────────┐)

[//]: # (              │   Monitoring Tools    │)

[//]: # (              │   - Grafana           │)

[//]: # (              │   - Prometheus        │)

[//]: # (              │   - Custom Dashboard  │)

[//]: # (              └───────────────────────┘)

[//]: # (```)

[//]: # ()
[//]: # (---)

[//]: # ()
[//]: # (## 🔧 Hardware Requirements)

[//]: # ()
[//]: # (### Essential Components)

[//]: # (| Component | Specification | Quantity |)

[//]: # (|-----------|--------------|----------|)

[//]: # (| **Microcontroller** | ESP32 DevKit v1 | 1 |)

[//]: # (| **Thermistors** | NTC 10kΩ @ 25°C, B=3950 | 5 |)

[//]: # (| **Resistors** | 56kΩ &#40;for thermistor voltage divider&#41; | 5 |)

[//]: # (| **Water Level Sensor** | Analog/Digital &#40;0-5cm range&#41; | 1 |)

[//]: # (| **RTC Module** | DS1307 with battery backup | 1 |)

[//]: # (| **Power Supply** | 5V 2A &#40;USB or adapter&#41; | 1 |)

[//]: # ()
[//]: # (### Additional &#40;For Automated Mode&#41;)

[//]: # (| Component | Specification | Quantity |)

[//]: # (|-----------|--------------|----------|)

[//]: # (| **Water Pump** | 5V DC submersible pump | 1 |)

[//]: # (| **Relay Module** | 5V single-channel relay | 1 |)

[//]: # (| **Power Supply** | Additional 12V for pump &#40;if needed&#41; | 1 |)

[//]: # ()
[//]: # (### Wiring Diagram)

[//]: # ()
[//]: # (```)

[//]: # (ESP32 Pin Connections:)

[//]: # (├── GPIO 32  → Thermistor 1 &#40;T1&#41;)

[//]: # (├── GPIO 33  → Thermistor 2 &#40;T2&#41;)

[//]: # (├── GPIO 27  → Thermistor 3 &#40;T3&#41;)

[//]: # (├── GPIO 35  → Thermistor 4 &#40;T4&#41;)

[//]: # (├── GPIO 25  → Thermistor 5 &#40;T5&#41;)

[//]: # (├── GPIO 34  → Water Level Sensor)

[//]: # (├── GPIO 26  → Pump Relay &#40;Automated mode only&#41;)

[//]: # (├── GPIO 21  → RTC SDA)

[//]: # (├── GPIO 22  → RTC SCL)

[//]: # (├── 3.3V     → Sensors VCC)

[//]: # (└── GND      → Common Ground)

[//]: # ()
[//]: # (Thermistor Wiring &#40;each&#41;:)

[//]: # (3.3V ─── 56kΩ ─── GPIO Pin ─── Thermistor ─── GND)

[//]: # (```)

[//]: # ()
[//]: # (---)

[//]: # ()
[//]: # (## 💻 Software Requirements)

[//]: # ()
[//]: # (### Arduino/ESP32)

[//]: # (- **Arduino IDE** 1.8.19+ or **PlatformIO**)

[//]: # (- **ESP32 Board Support** &#40;via Board Manager&#41;)

[//]: # (- **Required Libraries**:)

[//]: # (  ```)

[//]: # (  - RTClib &#40;Adafruit&#41;)

[//]: # (  - WiFi &#40;Built-in&#41;)

[//]: # (  - PubSubClient &#40;MQTT&#41;)

[//]: # (  - ArduinoJson &#40;6.x&#41;)

[//]: # (  - Wire &#40;Built-in&#41;)

[//]: # (  ```)

[//]: # ()
[//]: # (### Backend Server)

[//]: # (- **Python** 3.8+)

[//]: # (- **PostgreSQL** 12+)

[//]: # (- **MQTT Broker** &#40;Mosquitto, HiveMQ, or AWS IoT&#41;)

[//]: # (- **Python Packages**:)

[//]: # (  ```)

[//]: # (  - fastapi)

[//]: # (  - uvicorn)

[//]: # (  - sqlalchemy)

[//]: # (  - psycopg2-binary)

[//]: # (  - paho-mqtt)

[//]: # (  - pydantic)

[//]: # (  - pydantic-settings)

[//]: # (  - prometheus-client)

[//]: # (  ```)

[//]: # ()
[//]: # (---)

[//]: # ()
[//]: # (## 📦 Installation)

[//]: # ()
[//]: # (### 1. Clone the Repository)

[//]: # ()
[//]: # (```bash)

[//]: # (git clone https://github.com/yourusername/solar-still-monitoring.git)

[//]: # (cd solar-still-monitoring)

[//]: # (```)

[//]: # ()
[//]: # (### 2. Arduino Setup)

[//]: # ()
[//]: # (#### Install Required Libraries)

[//]: # (```bash)

[//]: # (# Using Arduino IDE:)

[//]: # (# Sketch → Include Library → Manage Libraries)

[//]: # (# Search and install:)

[//]: # (# - RTClib by Adafruit)

[//]: # (# - PubSubClient by Nick O'Leary)

[//]: # (# - ArduinoJson by Benoit Blanchon)

[//]: # ()
[//]: # (# OR using PlatformIO:)

[//]: # (pio lib install "Adafruit RTClib" "PubSubClient" "ArduinoJson")

[//]: # (```)

[//]: # ()
[//]: # (#### Configure the Code)

[//]: # (```cpp)

[//]: # (// Open: arduino/unified_solar_still/unified_solar_still.ino)

[//]: # ()
[//]: # (// 1. Set system mode &#40;line 19&#41;)

[//]: # (#define SYSTEM_MODE AUTOMATED  // or CONVENTIONAL)

[//]: # ()
[//]: # (// 2. Configure WiFi &#40;lines 65-66&#41;)

[//]: # (const char* WIFI_SSID = "YourWiFiSSID";)

[//]: # (const char* WIFI_PASSWORD = "YourWiFiPassword";)

[//]: # ()
[//]: # (// 3. Configure MQTT &#40;lines 67-70&#41;)

[//]: # (const char* MQTT_BROKER = "192.168.1.100";  // Your broker IP)

[//]: # (const int MQTT_PORT = 1883;)

[//]: # (const char* MQTT_TOPIC = "sensors/data";)

[//]: # (const char* MQTT_CLIENT_ID = "solar_still_esp32";)

[//]: # ()
[//]: # (// 4. Adjust thresholds if needed &#40;lines 39-45&#41;)

[//]: # (// For AUTOMATED mode:)

[//]: # (#define WATER_OFF_LEVEL 3500   // Pump turns OFF at 3.5cm)

[//]: # (#define WATER_ON_LEVEL  1000   // Pump turns ON at 1.0cm)

[//]: # ()
[//]: # (// For CONVENTIONAL mode:)

[//]: # (#define WATER_ALERT_LEVEL 1000 // Alert at 1.0cm)

[//]: # (```)

[//]: # ()
[//]: # (#### Upload to ESP32)

[//]: # (```bash)

[//]: # (# 1. Connect ESP32 via USB)

[//]: # (# 2. Select correct board: Tools → Board → ESP32 Dev Module)

[//]: # (# 3. Select correct port: Tools → Port → /dev/ttyUSB0 &#40;Linux&#41; or COM3 &#40;Windows&#41;)

[//]: # (# 4. Upload: Sketch → Upload &#40;or Ctrl+U&#41;)

[//]: # (```)

[//]: # ()
[//]: # (### 3. Backend Setup)

[//]: # ()
[//]: # (#### Install PostgreSQL)

[//]: # (```bash)

[//]: # (# Ubuntu/Debian)

[//]: # (sudo apt update)

[//]: # (sudo apt install postgresql postgresql-contrib)

[//]: # ()
[//]: # (# Start PostgreSQL service)

[//]: # (sudo systemctl start postgresql)

[//]: # (sudo systemctl enable postgresql)

[//]: # ()
[//]: # (# Create database and user)

[//]: # (sudo -u postgres psql)

[//]: # (```)

[//]: # ()
[//]: # (```sql)

[//]: # (CREATE DATABASE solar_still_db;)

[//]: # (CREATE USER solar_user WITH PASSWORD 'your_secure_password';)

[//]: # (GRANT ALL PRIVILEGES ON DATABASE solar_still_db TO solar_user;)

[//]: # (\q)

[//]: # (```)

[//]: # ()
[//]: # (#### Install MQTT Broker &#40;Mosquitto&#41;)

[//]: # (```bash)

[//]: # (# Ubuntu/Debian)

[//]: # (sudo apt install mosquitto mosquitto-clients)

[//]: # ()
[//]: # (# Start Mosquitto)

[//]: # (sudo systemctl start mosquitto)

[//]: # (sudo systemctl enable mosquitto)

[//]: # ()
[//]: # (# Test MQTT &#40;optional&#41;)

[//]: # (mosquitto_sub -h localhost -t "sensors/data")

[//]: # (```)

[//]: # ()
[//]: # (#### Install Python Dependencies)

[//]: # (```bash)

[//]: # (cd backend)

[//]: # ()
[//]: # (# Create virtual environment)

[//]: # (python3 -m venv venv)

[//]: # (source venv/bin/activate  # On Windows: venv\Scripts\activate)

[//]: # ()
[//]: # (# Install packages)

[//]: # (pip install -r requirements.txt)

[//]: # (```)

[//]: # ()
[//]: # (#### Create `requirements.txt`)

[//]: # (```txt)

[//]: # (fastapi==0.104.1)

[//]: # (uvicorn[standard]==0.24.0)

[//]: # (sqlalchemy==2.0.23)

[//]: # (psycopg2-binary==2.9.9)

[//]: # (paho-mqtt==1.6.1)

[//]: # (pydantic==2.5.0)

[//]: # (pydantic-settings==2.1.0)

[//]: # (prometheus-client==0.19.0)

[//]: # (python-dotenv==1.0.0)

[//]: # (```)

[//]: # ()
[//]: # (#### Configure Environment Variables)

[//]: # (```bash)

[//]: # (# Create .env file)

[//]: # (cp .env.example .env)

[//]: # (nano .env)

[//]: # (```)

[//]: # ()
[//]: # (```env)

[//]: # (# .env file)

[//]: # (POSTGRESQL_HOST=localhost)

[//]: # (POSTGRESQL_PORT=5432)

[//]: # (POSTGRESQL_USER=solar_user)

[//]: # (POSTGRESQL_PASSWORD=your_secure_password)

[//]: # (POSTGRESQL_DBNAME=solar_still_db)

[//]: # ()
[//]: # (MQTT_BROKER=localhost)

[//]: # (MQTT_PORT=1883)

[//]: # (```)

[//]: # ()
[//]: # (#### Create `.env.example` &#40;for version control&#41;)

[//]: # (```env)

[//]: # (POSTGRESQL_HOST=localhost)

[//]: # (POSTGRESQL_PORT=5432)

[//]: # (POSTGRESQL_USER=your_db_user)

[//]: # (POSTGRESQL_PASSWORD=your_db_password)

[//]: # (POSTGRESQL_DBNAME=solar_still_db)

[//]: # ()
[//]: # (MQTT_BROKER=localhost)

[//]: # (MQTT_PORT=1883)

[//]: # (```)

[//]: # ()
[//]: # (---)

[//]: # ()
[//]: # (## 🚀 Usage)

[//]: # ()
[//]: # (### Starting the Backend)

[//]: # ()
[//]: # (```bash)

[//]: # (cd backend)

[//]: # (source venv/bin/activate)

[//]: # ()
[//]: # (# Development mode &#40;with auto-reload&#41;)

[//]: # (uvicorn unified_backend:app --reload --host 0.0.0.0 --port 8000)

[//]: # ()
[//]: # (# Production mode)

[//]: # (uvicorn unified_backend:app --host 0.0.0.0 --port 8000 --workers 4)

[//]: # (```)

[//]: # ()
[//]: # (### Testing the System)

[//]: # ()
[//]: # (#### 1. Check Backend Status)

[//]: # (```bash)

[//]: # (curl http://localhost:8000/status)

[//]: # (```)

[//]: # ()
[//]: # (#### 2. Monitor Serial Output &#40;ESP32&#41;)

[//]: # (```bash)

[//]: # (# Arduino IDE: Tools → Serial Monitor &#40;115200 baud&#41;)

[//]: # (# OR using screen:)

[//]: # (screen /dev/ttyUSB0 115200)

[//]: # (```)

[//]: # ()
[//]: # (#### 3. Subscribe to MQTT Topic)

[//]: # (```bash)

[//]: # (mosquitto_sub -h localhost -t "sensors/data" -v)

[//]: # (```)

[//]: # ()
[//]: # (#### 4. View Recent Data)

[//]: # (```bash)

[//]: # (curl http://localhost:8000/data/latest)

[//]: # (```)

[//]: # ()
[//]: # (### System Startup Sequence)

[//]: # ()
[//]: # (1. **Backend**: Start the FastAPI server first)

[//]: # (2. **MQTT Broker**: Ensure Mosquitto is running)

[//]: # (3. **ESP32**: Power on the device)

[//]: # (4. **Monitor**: Watch serial output for connection status)

[//]: # ()
[//]: # (Expected output:)

[//]: # (```)

[//]: # (╔══════════════════════════════════════════════════╗)

[//]: # (║   AUTOMATED SOLAR STILL MONITORING SYSTEM       ║)

[//]: # (╚══════════════════════════════════════════════════╝)

[//]: # ()
[//]: # (Initializing RTC...)

[//]: # (✓ RTC found!)

[//]: # (RTC Time: 2025-11-10 14:30:00)

[//]: # ()
[//]: # (Connecting to WiFi...)

[//]: # (✓ WiFi connected!)

[//]: # (IP Address: 192.168.1.150)

[//]: # ()
[//]: # (Connecting to MQTT broker... ✓ Connected!)

[//]: # ()
[//]: # (══════════════════════════════════════════════════)

[//]: # (SYSTEM CONFIGURATION:)

[//]: # (Mode: AUTOMATED &#40;Pump Control Enabled&#41;)

[//]: # (Pump ON Threshold: 1.0 cm)

[//]: # (Pump OFF Threshold: 3.5 cm)

[//]: # (Data Upload: Every 10 minutes via MQTT)

[//]: # (MQTT Broker: 192.168.1.100:1883)

[//]: # (══════════════════════════════════════════════════)

[//]: # (```)

[//]: # ()
[//]: # (---)

[//]: # ()
[//]: # (## 📡 API Documentation)

[//]: # ()
[//]: # (### Base URL)

[//]: # (```)

[//]: # (http://localhost:8000)

[//]: # (```)

[//]: # ()
[//]: # (### Endpoints)

[//]: # ()
[//]: # (#### **Health & Status**)

[//]: # ()
[//]: # (**GET /** - API Information)

[//]: # (```bash)

[//]: # (curl http://localhost:8000/)

[//]: # (```)

[//]: # ()
[//]: # (**GET /status** - System Health Check)

[//]: # (```bash)

[//]: # (curl http://localhost:8000/status)

[//]: # (```)

[//]: # ()
[//]: # (Response:)

[//]: # (```json)

[//]: # ({)

[//]: # (  "fastapi_status": "online",)

[//]: # (  "mqtt_status": "connected",)

[//]: # (  "mqtt_broker": "localhost:1883",)

[//]: # (  "mqtt_last_message": "15s ago",)

[//]: # (  "database_status": "ok",)

[//]: # (  "last_data": { ... })

[//]: # (})

[//]: # (```)

[//]: # ()
[//]: # (#### **Data Retrieval**)

[//]: # ()
[//]: # (**GET /data** - Get Recent Data)

[//]: # (```bash)

[//]: # (# Get last 50 records)

[//]: # (curl http://localhost:8000/data)

[//]: # ()
[//]: # (# Get last 100 records)

[//]: # (curl http://localhost:8000/data?limit=100)

[//]: # ()
[//]: # (# Filter by system type)

[//]: # (curl http://localhost:8000/data?system_type=automated)

[//]: # ()
[//]: # (# Combine filters)

[//]: # (curl http://localhost:8000/data?limit=20&system_type=conventional)

[//]: # (```)

[//]: # ()
[//]: # (**GET /data/latest** - Get Most Recent Reading)

[//]: # (```bash)

[//]: # (# Latest from all systems)

[//]: # (curl http://localhost:8000/data/latest)

[//]: # ()
[//]: # (# Latest from automated systems only)

[//]: # (curl http://localhost:8000/data/latest?system_type=automated)

[//]: # (```)

[//]: # ()
[//]: # (**GET /data/system/{type}** - Get Data by System Type)

[//]: # (```bash)

[//]: # (# Get automated system data)

[//]: # (curl http://localhost:8000/data/system/automated)

[//]: # ()
[//]: # (# Get conventional system data)

[//]: # (curl http://localhost:8000/data/system/conventional?limit=30)

[//]: # (```)

[//]: # ()
[//]: # (**GET /data/range** - Get Data in Time Range)

[//]: # (```bash)

[//]: # (curl "http://localhost:8000/data/range?start=2025-11-10T00:00:00Z&end=2025-11-10T23:59:59Z")

[//]: # ()
[//]: # (# With system filter)

[//]: # (curl "http://localhost:8000/data/range?start=2025-11-10T00:00:00Z&end=2025-11-10T23:59:59Z&system_type=automated")

[//]: # (```)

[//]: # ()
[//]: # (#### **Statistics**)

[//]: # ()
[//]: # (**GET /stats** - Overall Statistics)

[//]: # (```bash)

[//]: # (curl http://localhost:8000/stats)

[//]: # (```)

[//]: # ()
[//]: # (Response:)

[//]: # (```json)

[//]: # ({)

[//]: # (  "total_records": 1250,)

[//]: # (  "system_breakdown": {)

[//]: # (    "conventional": 500,)

[//]: # (    "automated": 750)

[//]: # (  },)

[//]: # (  "temperature": {)

[//]: # (    "average": 32.5,)

[//]: # (    "min": 18.2,)

[//]: # (    "max": 65.3,)

[//]: # (    "unit": "°C")

[//]: # (  },)

[//]: # (  "water_level": {)

[//]: # (    "average": 2.8,)

[//]: # (    "min": 0.5,)

[//]: # (    "max": 4.0,)

[//]: # (    "unit": "cm")

[//]: # (  })

[//]: # (})

[//]: # (```)

[//]: # ()
[//]: # (**GET /stats/system/{type}** - System-Specific Statistics)

[//]: # (```bash)

[//]: # (curl http://localhost:8000/stats/system/automated)

[//]: # (```)

[//]: # ()
[//]: # (Response &#40;for automated&#41;:)

[//]: # (```json)

[//]: # ({)

[//]: # (  "system_type": "automated",)

[//]: # (  "total_records": 750,)

[//]: # (  "temperature": { ... },)

[//]: # (  "water_level": { ... },)

[//]: # (  "pump_statistics": {)

[//]: # (    "on_count": 450,)

[//]: # (    "off_count": 300,)

[//]: # (    "on_percentage": 60.0)

[//]: # (  })

[//]: # (})

[//]: # (```)

[//]: # ()
[//]: # (#### **Data Management**)

[//]: # ()
[//]: # (**POST /publish** - Manually Publish Data)

[//]: # (```bash)

[//]: # (curl -X POST http://localhost:8000/publish \)

[//]: # (  -H "Content-Type: application/json" \)

[//]: # (  -d '{)

[//]: # (    "system_type": "automated",)

[//]: # (    "temperature": 35.5,)

[//]: # (    "temp1": 34.2,)

[//]: # (    "temp2": 35.8,)

[//]: # (    "temp3": 36.1,)

[//]: # (    "temp4": 35.0,)

[//]: # (    "temp5": 36.4,)

[//]: # (    "water_level": {)

[//]: # (      "raw_adc": 2456,)

[//]: # (      "depth_cm": 2.45)

[//]: # (    },)

[//]: # (    "pump_status": "OFF",)

[//]: # (    "time_stamp": "2025-11-10 14:30:00")

[//]: # (  }')

[//]: # (```)

[//]: # ()
[//]: # (**DELETE /data/{id}** - Delete Record)

[//]: # (```bash)

[//]: # (curl -X DELETE http://localhost:8000/data/123)

[//]: # (```)

[//]: # ()
[//]: # (#### **Monitoring**)

[//]: # ()
[//]: # (**GET /metrics** - Prometheus Metrics)

[//]: # (```bash)

[//]: # (curl http://localhost:8000/metrics)

[//]: # (```)

[//]: # ()
[//]: # (### Interactive API Documentation)

[//]: # ()
[//]: # (FastAPI provides automatic interactive documentation:)

[//]: # ()
[//]: # (- **Swagger UI**: http://localhost:8000/docs)

[//]: # (- **ReDoc**: http://localhost:8000/redoc)

[//]: # ()
[//]: # (---)

[//]: # ()
[//]: # (## 📊 Data Structure)

[//]: # ()
[//]: # (### MQTT Payload &#40;ESP32 → Backend&#41;)

[//]: # ()
[//]: # (```json)

[//]: # ({)

[//]: # (  "system_type": "automated",)

[//]: # (  "time_stamp": "2025-11-10 14:30:00",)

[//]: # (  "temperature": 35.5,)

[//]: # (  "temp1": 34.2,)

[//]: # (  "temp2": 35.8,)

[//]: # (  "temp3": 36.1,)

[//]: # (  "temp4": 35.0,)

[//]: # (  "temp5": 36.4,)

[//]: # (  "water_level": {)

[//]: # (    "raw_adc": 2456,)

[//]: # (    "depth_cm": 2.45)

[//]: # (  },)

[//]: # (  "pump_status": "OFF")

[//]: # (})

[//]: # (```)

[//]: # ()
[//]: # (### Database Schema)

[//]: # ()
[//]: # (```sql)

[//]: # (CREATE TABLE solar_still_data &#40;)

[//]: # (    id BIGSERIAL PRIMARY KEY,)

[//]: # (    system_type VARCHAR NOT NULL,)

[//]: # (    temperature FLOAT NOT NULL,)

[//]: # (    temp1 FLOAT,)

[//]: # (    temp2 FLOAT,)

[//]: # (    temp3 FLOAT,)

[//]: # (    temp4 FLOAT,)

[//]: # (    temp5 FLOAT,)

[//]: # (    water_depth_cm FLOAT NOT NULL,)

[//]: # (    water_raw_adc INTEGER,)

[//]: # (    pump_status VARCHAR,)

[//]: # (    time_stamp VARCHAR,)

[//]: # (    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)

[//]: # (&#41;;)

[//]: # ()
[//]: # (CREATE INDEX idx_system_type ON solar_still_data&#40;system_type&#41;;)

[//]: # (CREATE INDEX idx_created_at ON solar_still_data&#40;created_at&#41;;)

[//]: # (```)

[//]: # ()
[//]: # (---)

[//]: # ()
[//]: # (## 🔍 Troubleshooting)

[//]: # ()
[//]: # (### ESP32 Issues)

[//]: # ()
[//]: # (#### WiFi Not Connecting)

[//]: # (```)

[//]: # (Symptoms: Continuous "Connecting to WiFi..." dots)

[//]: # (Solutions:)

[//]: # (- Check SSID and password spelling)

[//]: # (- Ensure 2.4GHz WiFi &#40;ESP32 doesn't support 5GHz&#41;)

[//]: # (- Check WiFi signal strength)

[//]: # (- Try static IP configuration)

[//]: # (```)

[//]: # ()
[//]: # (#### MQTT Connection Failed)

[//]: # (```)

[//]: # (Symptoms: "MQTT Connection failed, rc=X")

[//]: # (Error Codes:)

[//]: # (- rc=-4: Timeout &#40;broker unreachable&#41;)

[//]: # (- rc=-2: Network connection failed)

[//]: # (- rc=1: Protocol version mismatch)

[//]: # (- rc=2: Client ID rejected)

[//]: # (- rc=3: Server unavailable)

[//]: # (- rc=4: Bad credentials)

[//]: # (- rc=5: Not authorized)

[//]: # ()
[//]: # (Solutions:)

[//]: # (- Verify broker IP address)

[//]: # (- Check broker is running: systemctl status mosquitto)

[//]: # (- Test with mosquitto_sub: mosquitto_sub -h <broker_ip> -t "test")

[//]: # (- Check firewall rules)

[//]: # (```)

[//]: # ()
[//]: # (#### RTC Not Found)

[//]: # (```)

[//]: # (Symptoms: "ERROR: RTC not found!")

[//]: # (Solutions:)

[//]: # (- Check I2C wiring &#40;SDA=21, SCL=22&#41;)

[//]: # (- Verify RTC module has power &#40;5V and GND&#41;)

[//]: # (- Test I2C: Use I2C scanner sketch)

[//]: # (- Replace CR2032 battery if needed)

[//]: # (```)

[//]: # ()
[//]: # (#### Thermistor Errors)

[//]: # (```)

[//]: # (Symptoms: Temperature shows "ERROR" or "NAN")

[//]: # (Solutions:)

[//]: # (- Check thermistor wiring)

[//]: # (- Verify 56kΩ resistor value)

[//]: # (- Test with multimeter &#40;should read ~10kΩ at 25°C&#41;)

[//]: # (- Adjust offsets in code &#40;line 62&#41;)

[//]: # (```)

[//]: # ()
[//]: # (### Backend Issues)

[//]: # ()
[//]: # (#### Database Connection Failed)

[//]: # (```bash)

[//]: # (# Check PostgreSQL is running)

[//]: # (sudo systemctl status postgresql)

[//]: # ()
[//]: # (# Test connection)

[//]: # (psql -h localhost -U solar_user -d solar_still_db)

[//]: # ()
[//]: # (# Check credentials in .env file)

[//]: # (cat .env)

[//]: # ()
[//]: # (# View PostgreSQL logs)

[//]: # (sudo tail -f /var/log/postgresql/postgresql-*.log)

[//]: # (```)

[//]: # ()
[//]: # (#### MQTT Broker Not Receiving)

[//]: # (```bash)

[//]: # (# Check Mosquitto is running)

[//]: # (sudo systemctl status mosquitto)

[//]: # ()
[//]: # (# Test subscription)

[//]: # (mosquitto_sub -h localhost -t "sensors/data" -v)

[//]: # ()
[//]: # (# View Mosquitto logs)

[//]: # (sudo tail -f /var/log/mosquitto/mosquitto.log)

[//]: # ()
[//]: # (# Check MQTT configuration)

[//]: # (cat /etc/mosquitto/mosquitto.conf)

[//]: # (```)

[//]: # ()
[//]: # (#### Port Already in Use)

[//]: # (```bash)

[//]: # (# Error: "Address already in use")

[//]: # (# Find process using port 8000)

[//]: # (sudo lsof -i :8000)

[//]: # ()
[//]: # (# Kill process)

[//]: # (sudo kill -9 <PID>)

[//]: # ()
[//]: # (# Or use different port)

[//]: # (uvicorn unified_backend:app --port 8001)

[//]: # (```)

[//]: # ()
[//]: # (### Common Error Messages)

[//]: # ()
[//]: # (| Error | Cause | Solution |)

[//]: # (|-------|-------|----------|)

[//]: # (| `ImportError: No module named 'paho'` | Missing MQTT library | `pip install paho-mqtt` |)

[//]: # (| `sqlalchemy.exc.OperationalError` | Database connection failed | Check PostgreSQL credentials |)

[//]: # (| `WiFi.status&#40;&#41; = 6` | Wrong password | Verify WiFi credentials |)

[//]: # (| `Connection refused` | MQTT broker not running | Start Mosquitto service |)

[//]: # ()
[//]: # (---)

[//]: # ()
[//]: # (## 🎯 Best Practices)

[//]: # ()
[//]: # (### Security)

[//]: # (- ✅ Use strong database passwords)

[//]: # (- ✅ Enable MQTT authentication)

[//]: # (- ✅ Use SSL/TLS for production)

[//]: # (- ✅ Don't commit `.env` files to Git)

[//]: # (- ✅ Regularly update firmware and packages)

[//]: # (- ✅ Use firewall rules to restrict access)

[//]: # ()
[//]: # (### Performance)

[//]: # (- ✅ Set appropriate upload intervals &#40;10 min default&#41;)

[//]: # (- ✅ Use connection pooling for database)

[//]: # (- ✅ Monitor system resources)

[//]: # (- ✅ Archive old data periodically)

[//]: # (- ✅ Use indexes on frequently queried columns)

[//]: # ()
[//]: # (### Maintenance)

[//]: # (- ✅ Regular RTC battery replacement &#40;1-2 years&#41;)

[//]: # (- ✅ Clean sensors monthly)

[//]: # (- ✅ Check wiring connections quarterly)

[//]: # (- ✅ Monitor logs for errors)

[//]: # (- ✅ Backup database regularly)

[//]: # (- ✅ Test pump operation monthly &#40;automated systems&#41;)

[//]: # ()
[//]: # (---)

[//]: # ()
[//]: # (## 📈 Monitoring & Visualization)

[//]: # ()
[//]: # (### Grafana Dashboard Setup)

[//]: # ()
[//]: # (```bash)

[//]: # (# Install Grafana)

[//]: # (sudo apt install grafana)

[//]: # ()
[//]: # (# Start Grafana)

[//]: # (sudo systemctl start grafana-server)

[//]: # (sudo systemctl enable grafana-server)

[//]: # ()
[//]: # (# Access: http://localhost:3000)

[//]: # (# Default credentials: admin/admin)

[//]: # (```)

[//]: # ()
[//]: # (### Prometheus Configuration)

[//]: # ()
[//]: # (```yaml)

[//]: # (# prometheus.yml)

[//]: # (scrape_configs:)

[//]: # (  - job_name: 'solar_still')

[//]: # (    static_configs:)

[//]: # (      - targets: ['localhost:8000'])

[//]: # (    metrics_path: '/metrics')

[//]: # (    scrape_interval: 30s)

[//]: # (```)

[//]: # ()
[//]: # (---)

[//]: # ()
[//]: # (## 🤝 Contributing)

[//]: # ()
[//]: # (We welcome contributions! Please follow these steps:)

[//]: # ()
[//]: # (1. **Fork the repository**)

[//]: # (2. **Create a feature branch**: `git checkout -b feature/amazing-feature`)

[//]: # (3. **Commit your changes**: `git commit -m 'Add amazing feature'`)

[//]: # (4. **Push to branch**: `git push origin feature/amazing-feature`)

[//]: # (5. **Open a Pull Request**)

[//]: # ()
[//]: # (### Code Style)

[//]: # (- **Arduino**: Follow Arduino style guide)

[//]: # (- **Python**: Follow PEP 8)

[//]: # (- **Comments**: Document complex logic)

[//]: # (- **Commit Messages**: Use conventional commits)

[//]: # ()
[//]: # (---)

[//]: # ()
[//]: # (## 📄 License)

[//]: # ()
[//]: # (This project is licensed under the MIT License - see the [LICENSE]&#40;LICENSE&#41; file for details.)

[//]: # ()
[//]: # (---)

[//]: # ()
[//]: # (## 👥 Authors)

[//]: # ()
[//]: # (- **Jerry George** - *Initial work* - [YourGitHub]&#40;https://github.com/jerrygithub360&#41;)

[//]: # ()
[//]: # (---)

[//]: # ()
[//]: # (## 🙏 Acknowledgments)

[//]: # ()
[//]: # (- Adafruit for RTClib library)

[//]: # (- Nick O'Leary for PubSubClient)

[//]: # (- FastAPI team for excellent framework)

[//]: # (- ESP32 community for support and examples)

[//]: # ()
[//]: # (---)

[//]: # ()
[//]: # (## 📞 Support)

[//]: # ()
[//]: # (- **Issues**: [GitHub Issues]&#40;https://github.com/jerrygithub360/solar-still-monitoring/issues&#41;)

[//]: # (- **Discussions**: [GitHub Discussions]&#40;https://github.com/jerrygithub360/solar-still-monitoring/discussions&#41;)

[//]: # (- **Email**: jerrygithub360)

[//]: # ()
[//]: # (---)

[//]: # ()
[//]: # (## 🗺️ Roadmap)

[//]: # ()
[//]: # (- [ ] Add SMS/Email alerts for critical events)

[//]: # (- [ ] Implement mobile app for remote monitoring)

[//]: # (- [ ] Add machine learning for predictive maintenance)

[//]: # (- [ ] Support for additional sensors &#40;pH, TDS, etc.&#41;)

[//]: # (- [ ] Multi-site deployment support)

[//]: # (- [ ] Custom web dashboard)

[//]: # (- [ ] Data export to CSV/Excel)

[//]: # (- [ ] Historical trend analysis)

[//]: # ()
[//]: # (---)

[//]: # ()
[//]: # (## 📊 Project Status)

[//]: # ()
[//]: # (**Current Version**: 2.0.0  )

[//]: # (**Status**: Active Development  )

[//]: # (**Last Updated**: November 2025)

[//]: # ()
[//]: # (---)

[//]: # ()
[//]: # (**Made with ❤️ for sustainable water solutions**)