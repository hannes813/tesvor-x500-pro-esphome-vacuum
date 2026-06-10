# Installation

## 1. Original-Firmware sichern

Vor dem ersten Flashen ein vollständiges Backup erstellen:

```powershell
python -m esptool --port COM8 --baud 115200 read-flash 0x00000 0x400000 tesvor_x500_original_4mb.bin
```

## 2. ESPHome vorbereiten

```bash
cp secrets.yaml.example secrets.yaml
```

`secrets.yaml` anpassen.

## 3. Kompilieren und flashen

Seriell:

```powershell
python -m esphome upload x500.yaml --device COM8
```

OTA:

```powershell
python -m esphome upload x500.yaml --device 192.168.178.108
```

## 4. Map Writer auf Synology

Empfohlener Pfad:

```text
/volume2/docker/tesvor-map
```

Dateien dorthin kopieren:

```bash
mkdir -p /volume2/docker/tesvor-map
cp tesvor_map_writer.py /volume2/docker/tesvor-map/
cp web/map.html /volume2/docker/tesvor-map/map.html
cp requirements.txt /volume2/docker/tesvor-map/
```

Python-Abhängigkeit:

```bash
python3 -m pip install -r /volume2/docker/tesvor-map/requirements.txt
```

Writer starten:

```bash
TESVOR_MQTT_HOST=192.xxx.xxx.xx TESVOR_MQTT_USER='DEIN_USER' TESVOR_MQTT_PASSWORD='DEIN_PASSWORT' python3 /volume2/docker/tesvor-map/tesvor_map_writer.py
```

## 5. DSM Aufgabenplaner

Als Benutzer `root`:

```bash
/volume2/docker/tesvor-map/start_writer.sh
```

Optional HTTP-Server:

```bash
/volume2/docker/tesvor-map/start_http.sh
```

## 6. Home Assistant iframe

Bei direktem HTTP-Server:

```yaml
type: iframe
url: http://192.xxx.xxx.xx:xxxx/map.html
aspect_ratio: 100%
```

Für Mobile App besser über `/local`:

```yaml
type: iframe
url: /local/tesvor-map/map.html
aspect_ratio: 100%
```
