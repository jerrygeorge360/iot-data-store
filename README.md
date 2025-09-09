# IoT Data Store

**IoT Data Store** is a backend service designed to collect, store, and monitor real-time sensor data from IoT devices. It leverages FastAPI for the API layer, PostgreSQL for persistent storage, MQTT for real-time messaging, and Prometheus + Grafana for monitoring.

## Features

* Receive sensor data from IoT devices via MQTT in real-time.
* Store sensor readings in a PostgreSQL database.
* Expose a REST API to query recent sensor data.
* Provide system metrics for Prometheus monitoring.
* Visualize metrics and sensor data using Grafana dashboards.

## Architecture

```
[IoT Device] --> MQTT Broker --> FastAPI Backend --> PostgreSQL
                                   |
                                   v
                               Prometheus --> Grafana
```

## Getting Started

### Prerequisites

* Docker & Docker Compose
* Arduino or other IoT devices with MQTT capability

### Environment Variables

Create a `.env` file with the following:

```env
# MQTT
MQTT_BROKER=mosquitto
MQTT_PORT=1883

# PostgreSQL
POSTGRESQL_USERNAME=
POSTGRESQL_PASSWORD=
POSTGRESQL_HOST=
POSTGRESQL_PORT=''
POSTGRESQL_DB=''
```

### Running with Docker Compose

```bash
docker-compose up --build
```

* FastAPI: `http://localhost:8000`
* Prometheus: `http://localhost:9090`
* Grafana: `http://localhost:3000` (default admin/admin)

### MQTT Usage

IoT devices can publish sensor data to the topic `sensors/data` with a JSON payload:

```json
{
    "temperature": 25.6,
    "light_intensity": 450.0,
    "time_stamp": "2025-09-08T18:15:30Z"
}
```

### API Endpoints

* `GET /data?limit=50` – Retrieve last 50 sensor readings.
* `POST /publish/` – Submit sensor data directly (bypasses MQTT).
* `GET /status/` – Check system health.
* `GET /metrics` – Prometheus metrics endpoint.

### Grafana

* Add Prometheus as a data source (`http://prometheus:9090`)
* Create dashboards to visualize MQTT messages, DB writes, or sensor data trends.

## Sample Timestamp Format

ISO 8601 string:

```text
2025-09-08T18:15:30Z
```


## License

MIT License
