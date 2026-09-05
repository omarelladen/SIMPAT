# Sistema Inteligente de Monitoramento Patrimonial (SIMPAT)

## Website
[GitHub Page](https://omarelladen.github.io/InventoryTracker/)


## Firmware (ESP32 using the Arduino framework)

### Install requirements (Debian)
```sh
sudo apt install arduino
```
Add URL:
```
https://espressif.github.io/arduino-esp32/package_esp32_index.json
```
### Upload
```sh
./scripts/upload.sh
```


## Server (FastAPI)

### Install requirements (Debian)
```sh
sudo apt install python3-fastapi sqlite3
```

### Run server (local)

#### Setup database
```sh
./scripts/setup_db.sh
```

#### Start
```sh
cd server
python3 main.py
```

### Run server (Docker)

#### Install requirements (Debian)
```sh
sudo apt install docker.io docker-compose
```

#### Create
```sh
./scripts/docker/build.sh
./scripts/docker/create.sh
```

#### Start
```sh
./scripts/docker/start.sh
```

## License
[GPLv2](./LICENSE)

Copyright 2026 Omar Zagonel El Laden
