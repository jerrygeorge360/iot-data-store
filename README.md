# IoT Data Store

IoT Data Store is a complete backend service designed to collect, store, and monitor real-time sensor data from IoT devices like the ESP32. It uses FastAPI for the API layer, PostgreSQL for persistent storage, MQTT for real-time messaging, and Prometheus with Grafana for monitoring and visualization.

## What It Does

The system receives sensor data from ESP32 devices via MQTT in real-time and stores the readings (temperature, light intensity) in a PostgreSQL database. You can query and analyze this data through a RESTful API, monitor system metrics with Prometheus, and visualize everything using Grafana dashboards. It also includes health checks, status monitoring, and statistical analysis tools.

## How It Works

The architecture is straightforward: ESP32 devices with sensors send data over MQTT to a Mosquitto broker. The FastAPI backend subscribes to this broker, processes incoming messages, and stores them in PostgreSQL. Prometheus scrapes metrics from the API, and Grafana visualizes both metrics and sensor data.

```
[ESP32 Device] --MQTT--> Mosquitto Broker --> FastAPI Backend --> PostgreSQL
  (Sensors)                                         |
                                                    v
                                               Prometheus --> Grafana
```

## Supported Sensors

The system works with three types of sensors:
- DS1307 RTC for accurate timestamps
- BH1750 for measuring light intensity in lux
- Two 10kΩ NTC thermistors for temperature readings

## Getting Started

### What You'll Need

Before starting, make sure you have Docker and Docker Compose installed. You'll also need an ESP32 development board, the sensors mentioned above, and either Arduino IDE or PlatformIO for programming the ESP32.

### Installation Steps

First, clone the repository and navigate into it:
```bash
git clone https://github.com/jerrygeorge360/iot-data-store.git
cd iot-data-store
```

Create the project structure:
```bash
mkdir -p fastapi-app mosquitto prometheus
```

Create a `.env` file with your configuration:
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

Start all services:
```bash
docker-compose up -d --build
```

Check that everything is running:
```bash
docker-compose ps
curl http://localhost:8000/status
```

### Ports

The system uses these ports:

| Service | External Port | Internal Port | Access URL |
|---------|---------------|---------------|------------|
| FastAPI | 8000 | 8000 | http://localhost:8000 |
| PostgreSQL | 5434 | 5432 | localhost:5434 |
| Mosquitto MQTT | 1885 | 1883 | localhost:1885 |
| Prometheus | 9090 | 9090 | http://localhost:9090 |
| Grafana | 3000 | 3000 | http://localhost:3000 |

Note: We use ports 5434 and 1885 externally to avoid conflicts with local PostgreSQL and Mosquitto installations.

## Setting Up Your ESP32

### Hardware Connections

Connect your sensors to the ESP32 like this:

**DS1307 RTC:**
- VCC to 5V
- GND to GND
- SDA to GPIO 21
- SCL to GPIO 22

**BH1750 Light Sensor:**
- VCC to 3.3V
- GND to GND
- SDA to GPIO 21 (shared with RTC)
- SCL to GPIO 22 (shared with RTC)
- ADD to GND (sets I2C address to 0x23)

**Thermistor 1:**
- One leg to 3.3V
- Other leg to GPIO 33 and a 10kΩ resistor to GND

**Thermistor 2:**
- One leg to 3.3V
- Other leg to GPIO 32 and a 10kΩ resistor to GND

### Software Setup

Update the ESP32 code with your WiFi and MQTT details:

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

You'll need these Arduino libraries:
- WiFi (built-in)
- PubSubClient
- Wire (built-in)
- RTClib from Adafruit
- BH1750

## Data Format

The ESP32 publishes data to the `sensors/data` topic every 60 seconds in this format:

```json
{
  "voltage_difference": 0.010,
  "voltage1": 1.645,
  "voltage2": 1.655,
  "adc_raw1": 2048,
  "adc_raw2": 2056,
  "light_intensity": 245.8,
  "time_stamp": "2025-11-10 14:23:45"
}
```

The fields mean:
- `voltage_difference`: Absolute difference between voltage1 and voltage2
- `voltage1`: Voltage reading from thermistor 1 (attached to black body)
- `voltage2`: Voltage reading from thermistor 2 (air temperature)
- `adc_raw1` and `adc_raw2`: Raw ADC values (0-4095)
- `light_intensity`: Light level from BH1750 in lux
- `time_stamp`: Timestamp from the RTC

## API Endpoints

### Getting Sensor Data

- `GET /` shows API information and available endpoints
- `GET /data?limit=50` retrieves the last 50 sensor readings (you can change the limit)
- `GET /data/latest` gets the most recent reading
- `GET /data/range?start=2025-11-10T00:00:00Z&end=2025-11-10T23:59:59Z` gets data within a specific time range
- `POST /publish` lets you manually submit sensor data, bypassing MQTT

### System Information

- `GET /status` shows system health (FastAPI, MQTT, Database status)
- `GET /stats` provides database statistics like averages, minimums, and maximums
- `GET /metrics` is the Prometheus metrics endpoint

### Management

- `DELETE /data/{id}` deletes a specific record by its ID

### Example Usage

Get the latest data:
```bash
curl http://localhost:8000/data/latest
```

Get statistics:
```bash
curl http://localhost:8000/stats
```

Check system status:
```bash
curl http://localhost:8000/status
```

Query a time range:
```bash
curl "http://localhost:8000/data/range?start=2025-11-10T00:00:00Z&end=2025-11-10T23:59:59Z"
```

## Interactive Documentation

FastAPI automatically generates interactive documentation that you can access at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Monitoring and Visualization

### Prometheus

Access Prometheus at http://localhost:9090. It tracks these metrics:

- `http_requests_total`: Total HTTP requests by endpoint
- `mqtt_messages_total`: Total MQTT messages processed
- `mqtt_connected`: MQTT connection status (1 means connected, 0 means disconnected)
- `last_db_write_timestamp`: Unix timestamp of the last database write
- `current_voltage1_volts`: Current voltage1 reading
- `current_voltage2_volts`: Current voltage2 reading
- `current_light_intensity_lux`: Current light intensity reading

### Grafana

To set up Grafana:

1. Go to http://localhost:3000
2. Log in with the default credentials: username `admin`, password `admin`
3. Add Prometheus as a data source with URL `http://prometheus:9090`
4. Save and test the connection
5. Create dashboards to visualize temperature trends, light patterns, MQTT message rates, and system health

## Database Structure

The main table is called `pyranometer` and has these columns:

| Column | Type | Description |
|--------|------|-------------|
| id | BIGINT | Primary key (auto-increment) |
| voltage1 | FLOAT | Voltage from thermistor 1 |
| voltage2 | FLOAT | Voltage from thermistor 2 |
| voltage_difference | FLOAT | Absolute difference between voltages |
| adc_raw1 | INTEGER | Raw ADC value from pin 33 |
| adc_raw2 | INTEGER | Raw ADC value from pin 32 |
| light_intensity | FLOAT | Light level in lux |
| time_stamp | STRING | Timestamp from ESP32 RTC |
| created_at | DATETIME | Server timestamp (auto-generated) |
| temperature | FLOAT | Legacy field for average temperature |
| temp1 | FLOAT | Legacy field for thermistor 1 |
| temp2 | FLOAT | Legacy field for thermistor 2 |

### Accessing the Database

You can connect to PostgreSQL directly:

```bash
# Access PostgreSQL via Docker
docker-compose exec postgres psql -U iot_user -d sensor_db

# Inside psql, try these commands:
\dt                           # List tables
\d pyranometer                # Describe table structure
SELECT * FROM pyranometer LIMIT 10;
```

## Docker Commands

Here are some useful Docker commands:

Start services:
```bash
docker-compose up -d
```

Stop services:
```bash
docker-compose down
```

View logs:
```bash
docker-compose logs -f                # All services
docker-compose logs -f fastapi-app    # Specific service
```

Restart a service:
```bash
docker-compose restart fastapi-app
```

Rebuild after code changes:
```bash
docker-compose up -d --build
```

Clean everything (warning: this deletes data):
```bash
docker-compose down -v
```

## Troubleshooting

### Port Conflicts

If you get "port already in use" errors, check what's using the port:

```bash
sudo lsof -i :1885
sudo lsof -i :5434
```

Stop conflicting services:
```bash
sudo systemctl stop postgresql
sudo systemctl stop mosquitto
```

Or change the ports in docker-compose.yml.

### ESP32 Connection Issues

If your ESP32 can't connect to MQTT:

1. Make sure your firewall allows port 1885
2. Verify the ESP32 has the correct IP address
3. Test MQTT locally:
   ```bash
   docker-compose exec mosquitto mosquitto_sub -t "sensors/data" -v
   ```

### Database Problems

Check if PostgreSQL is healthy:
```bash
docker-compose ps postgres
```

View the logs:
```bash
docker-compose logs postgres
```

Restart if needed:
```bash
docker-compose restart postgres
```

### No Data Coming In

If data isn't appearing:

1. Check the ESP32 serial monitor for connection status
2. Verify MQTT messages are being sent:
   ```bash
   docker-compose logs -f mosquitto
   ```
3. Check FastAPI logs:
   ```bash
   docker-compose logs -f fastapi-app
   ```

## Cloud Deployment

To deploy on Google Cloud Platform:

1. Create a GCP VM (e2-medium is recommended)
2. Reserve a static external IP address
3. Configure firewall rules for ports 1884 and 8000
4. SSH into the VM and clone the repository
5. Run the deployment script
6. Update your ESP32 code with the VM's external IP

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

If you want to develop without Docker:

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

If you'd like to contribute:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## License

This project uses the MIT License. See the LICENSE file for details.

## Credits

This project uses FastAPI for the web framework, Mosquitto as the MQTT broker, PostgreSQL for the database, and Prometheus with Grafana for the monitoring stack. Thanks to the ESP32 community for their support and documentation.

## Support

If you have issues, questions, or want to contribute, please open an issue on GitHub.