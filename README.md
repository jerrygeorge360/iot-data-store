# IoT Data Store

**IoT Data Store** is a complete backend service designed to collect, store, and monitor real-time sensor data from IoT devices (ESP32). It leverages FastAPI for the API layer, PostgreSQL for persistent storage, MQTT for real-time messaging, and Prometheus + Grafana for monitoring and visualization.

## Features

* 📡 Receive sensor data from ESP32 devices via MQTT in real-time
* 🗄️ Store sensor readings (temperature, light intensity) in PostgreSQL
* 🌐 RESTful API to query and analyze sensor data
* 📊 System metrics for Prometheus monitoring
* 📈 Visualize metrics and sensor data using Grafana dashboards
* 🔒 Health checks and status monitoring
* 📉 Statistical analysis and data aggregation

## Architecture

```
[ESP32 Device] --MQTT--> Mosquitto Broker --> FastAPI Backend --> PostgreSQL
  (Sensors)                                         |
                                                    v
                                               Prometheus --> Grafana
```

## Sensors Supported

* **DS1307 RTC** - Real-time clock for accurate timestamps
* **BH1750** - Light intensity sensor (lux)
* **2x Thermistors** - Temperature sensors (10kΩ NTC)

## Getting Started

### Prerequisites

* Docker & Docker Compose installed
* ESP32 development board
* Sensors: DS1307 RTC, BH1750, Thermistors
* Arduino IDE or PlatformIO (for ESP32 programming)

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/jerrygeorge360/iot-data-store.git
   cd iot-data-store
   ```

2. **Create project structure:**
   ```bash
   mkdir -p fastapi-app mosquitto prometheus
   ```

3. **Create `.env` file:**
   ```env
   # PostgreSQL
   POSTGRESQL_HOST=postgres
   POSTGRESQL_PORT=5432
   POSTGRESQL_USER=iot_user
   POSTGRESQL_PASSWORD=iot_password
   POSTGRESQL_DBNAME=sensor_db
   POSTGRESQL_URI=postgresql://iot_user:iot_password@postgres:5432/sensor_db

   # MQTT
   MQTT_BROKER=mosquitto
   MQTT_PORT=1883
   ```

4. **Start all services:**
   ```bash
   docker-compose up -d --build
   ```

5. **Verify services are running:**
   ```bash
   docker-compose ps
   curl http://localhost:8000/status
   ```

### Port Configuration

| Service | External Port | Internal Port | Access URL |
|---------|---------------|---------------|------------|
| FastAPI | 8000 | 8000 | http://localhost:8000 |
| PostgreSQL | 5434 | 5432 | localhost:5434 |
| Mosquitto MQTT | 1885 | 1883 | localhost:1885 |
| Prometheus | 9090 | 9090 | http://localhost:9090 |
| Grafana | 3000 | 3000 | http://localhost:3000 |

**Note:** Ports 5434 and 1885 are used to avoid conflicts with local PostgreSQL and Mosquitto installations.

## ESP32 Configuration

### Hardware Setup

**Connections:**
```
DS1307 RTC:
  - VCC → 5V
  - GND → GND
  - SDA → GPIO 21
  - SCL → GPIO 22

BH1750 Light Sensor:
  - VCC → 3.3V
  - GND → GND
  - SDA → GPIO 21 (shared)
  - SCL → GPIO 22 (shared)
  - ADD → GND (I2C address 0x23)

Thermistor 1:
  - One leg → 3.3V
  - Other leg → GPIO 33 + 10kΩ resistor to GND

Thermistor 2:
  - One leg → 3.3V
  - Other leg → GPIO 32 + 10kΩ resistor to GND
```

### Software Configuration

Update the ESP32 code with your WiFi and MQTT broker details:

```cpp
// WiFi Settings
const char* WIFI_SSID     = "Your-WiFi-SSID";
const char* WIFI_PASSWORD = "Your-WiFi-Password";

// MQTT Settings
const char* MQTT_BROKER   = "192.168.1.100";  // Your computer/server IP
const int   MQTT_PORT     = 1884;             // Use 1884 for Docker setup
const char* MQTT_TOPIC    = "sensors/data";
const char* CLIENT_ID     = "ESP32_Client_1";
```

**Required Arduino Libraries:**
* WiFi (built-in)
* PubSubClient
* Wire (built-in)
* RTClib (Adafruit)
* BH1750

## MQTT Data Format

ESP32 publishes to topic `sensors/data` with JSON payload:

```json
{
  "temperature": 24.35,
  "light_intensity": 245.8,
  "time_stamp": "2025-11-10T14:23:45Z",
  "temp1": 24.12,
  "temp2": 24.58
}
```

**Field Descriptions:**
* `temperature` - Average of both thermistors (°C)
* `light_intensity` - Light level from BH1750 (lux)
* `time_stamp` - ISO 8601 UTC timestamp from RTC
* `temp1` - Temperature from thermistor 1(black body) (°C)
* `temp2` - Temperature from thermistor 2 (°C)

**Publishing Frequency:** Every 60 seconds

## API Endpoints

### Sensor Data

* **`GET /`** - API information and available endpoints
* **`GET /data?limit=50`** - Retrieve last N sensor readings (default: 50)
* **`GET /data/latest`** - Get the most recent sensor reading
* **`GET /data/range?start=2025-11-10T00:00:00Z&end=2025-11-10T23:59:59Z`** - Get data within time range
* **`POST /publish`** - Manually submit sensor data (bypasses MQTT)

### System Status

* **`GET /status`** - System health check (FastAPI, MQTT, Database)
* **`GET /stats`** - Database statistics (avg, min, max values)
* **`GET /metrics`** - Prometheus metrics endpoint

### Management

* **`DELETE /data/{id}`** - Delete a specific record by ID

### Example Requests

**Get latest data:**
```bash
curl http://localhost:8000/data/latest
```

**Get statistics:**
```bash
curl http://localhost:8000/stats
```

**Check system status:**
```bash
curl http://localhost:8000/status
```

**Query time range:**
```bash
curl "http://localhost:8000/data/range?start=2025-11-10T00:00:00Z&end=2025-11-10T23:59:59Z"
```

## Interactive API Documentation

FastAPI provides automatic interactive documentation:

* **Swagger UI:** http://localhost:8000/docs
* **ReDoc:** http://localhost:8000/redoc

## Monitoring & Visualization

### Prometheus

Access Prometheus at http://localhost:9090

**Available Metrics:**
* `http_requests_total` - Total HTTP requests by endpoint
* `mqtt_messages_total` - Total MQTT messages processed
* `mqtt_connected` - MQTT connection status (1=connected, 0=disconnected)
* `last_db_write_timestamp` - Unix timestamp of last database write
* `current_temperature_celsius` - Current temperature reading
* `current_light_intensity_lux` - Current light intensity reading

### Grafana

1. Access Grafana at http://localhost:3000
2. Login with default credentials: `admin` / `admin`
3. Add Prometheus data source:
   - URL: `http://prometheus:9090`
   - Save & Test
4. Create dashboards to visualize:
   - Temperature trends over time
   - Light intensity patterns
   - MQTT message rates
   - System health metrics

## Database Schema

**Table:** `pyranometer`

| Column | Type | Description |
|--------|------|-------------|
| id | BIGINT | Primary key (auto-increment) |
| temperature | FLOAT | Average temperature (°C) |
| temp1 | FLOAT | Thermistor 1 temperature (°C) |
| temp2 | FLOAT | Thermistor 2 temperature (°C) |
| light_intensity | FLOAT | Light level (lux) |
| time_stamp | STRING | ISO 8601 timestamp from ESP32 |
| created_at | DATETIME | Server timestamp (auto-generated) |

### Direct Database Access

```bash
# Access PostgreSQL via Docker
docker-compose exec postgres psql -U iot_user -d sensor_db

# Inside psql:
\dt                           # List tables
\d pyranometer                # Describe table structure
SELECT * FROM pyranometer LIMIT 10;
```

## Docker Commands

**Start services:**
```bash
docker-compose up -d
```

**Stop services:**
```bash
docker-compose down
```

**View logs:**
```bash
docker-compose logs -f                # All services
docker-compose logs -f fastapi-app    # Specific service
```

**Restart a service:**
```bash
docker-compose restart fastapi-app
```

**Rebuild after code changes:**
```bash
docker-compose up -d --build
```

**Clean everything (⚠️ deletes data):**
```bash
docker-compose down -v
```

## Troubleshooting

### Port Conflicts

If you get "port already in use" errors:

```bash
# Check what's using the port
sudo lsof -i :1885
sudo lsof -i :5434

# Stop local services
sudo systemctl stop postgresql
sudo systemctl stop mosquitto

# Or change ports in docker-compose.yml
```

### ESP32 Can't Connect to MQTT

1. Check firewall allows port 1885
2. Verify ESP32 uses correct IP address
3. Test MQTT locally:
   ```bash
   docker-compose exec mosquitto mosquitto_sub -t "sensors/data" -v
   ```

### Database Connection Issues

```bash
# Check if PostgreSQL is healthy
docker-compose ps postgres

# View logs
docker-compose logs postgres

# Restart service
docker-compose restart postgres
```

### No Data Appearing

1. Check ESP32 serial monitor for connection status
2. Verify MQTT messages are being sent:
   ```bash
   docker-compose logs -f mosquitto
   ```
3. Check FastAPI logs:
   ```bash
   docker-compose logs -f fastapi-app
   ```

## GCP Deployment

For deploying to Google Cloud Platform:

1. Create a GCP VM (e2-medium recommended)
2. Reserve a static external IP
3. Configure firewall rules for ports 1884, 8000
4. SSH into VM and clone repository
5. Run deployment script
6. Update ESP32 with VM's external IP


## Development

### Project Structure

```
iot-data-store/
├── docker-compose.yml
├── .env
├── README.md
├── fastapi-app/
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
├── mosquitto/
│   └── mosquitto.conf
├── prometheus/
│   └── prometheus.yml
└── arduino_sketch/
    └── esp32_sensor_mqtt.ino
```

### Local Development

To develop without Docker:

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
cd fastapi-app
pip install -r requirements.txt

# Run FastAPI locally
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) file for details

## Acknowledgments

* FastAPI - Modern web framework
* Mosquitto - MQTT broker
* PostgreSQL - Database
* Prometheus & Grafana - Monitoring stack
* ESP32 community

## Support

For issues, questions, or contributions, please open an issue on GitHub.

---

**Made with ❤️ for IoT enthusiasts**