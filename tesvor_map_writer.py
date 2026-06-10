#!/usr/bin/env python3
"""MQTT map writer for the Tesvor X500 ESPHome reverse-engineering project.

The ESPHome firmware publishes compact point batches to:
  tesvor/x500/map/points

This writer persists the current cleaning session to current.json and archives
the final map once the robot returns to charging/docked.
"""

import json
import os
import shutil
from pathlib import Path
from datetime import datetime

import paho.mqtt.client as mqtt


MQTT_HOST = os.getenv("TESVOR_MQTT_HOST", "192.xxx.xxx.xx") 
MQTT_PORT = int(os.getenv("TESVOR_MQTT_PORT", "xxxx"))
MQTT_USER = os.getenv("TESVOR_MQTT_USER", "")
MQTT_PASSWORD = os.getenv("TESVOR_MQTT_PASSWORD", "")

BASE_DIR = Path(os.getenv("TESVOR_MAP_DIR", "/volume2/docker/tesvor-map"))
CURRENT_FILE = BASE_DIR / "current.json"
ARCHIVE_DIR = BASE_DIR / "archive"
ARCHIVE_INDEX_FILE = BASE_DIR / "archive_index.json"

POINT_TOPIC = os.getenv("TESVOR_POINT_TOPIC", "tesvor/x500/map/points")
STATE_TOPIC = os.getenv("TESVOR_STATE_TOPIC", "tesvor/x500/state")

MIN_POINTS_TO_ARCHIVE = int(os.getenv("TESVOR_MIN_POINTS_TO_ARCHIVE", "5"))

BASE_DIR.mkdir(parents=True, exist_ok=True)
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

points_by_seq = {}
session_started = None
last_state = None
archived_this_session = False


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def save_json_atomic(path: Path, payload: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    tmp.replace(path)


def current_payload() -> dict:
    ordered = [points_by_seq[k] for k in sorted(points_by_seq.keys())]
    return {
        "device": "tesvor_x500",
        "updated": now_iso(),
        "started": session_started,
        "point_count": len(ordered),
        "points": ordered,
    }


def save_current() -> None:
    save_json_atomic(CURRENT_FILE, current_payload())


def archive_index_payload() -> dict:
    files = []
    for f in sorted(ARCHIVE_DIR.glob("*.json"), reverse=True):
        try:
            stat = f.stat()
            files.append({
                "name": f.name,
                "path": f"archive/{f.name}",
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
            })
        except OSError:
            pass

    return {
        "updated": now_iso(),
        "files": files,
    }


def write_archive_index() -> None:
    save_json_atomic(ARCHIVE_INDEX_FILE, archive_index_payload())


def archive_current(reason: str) -> None:
    global archived_this_session

    if archived_this_session:
        return

    if not CURRENT_FILE.exists():
        return

    if len(points_by_seq) < MIN_POINTS_TO_ARCHIVE:
        return

    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    archive_file = ARCHIVE_DIR / f"tesvor_map_{ts}_{reason}.json"

    shutil.copy2(CURRENT_FILE, archive_file)
    archived_this_session = True
    write_archive_index()

    print(f"[ARCHIVE] {archive_file}", flush=True)


def reset_session() -> None:
    global points_by_seq, session_started, archived_this_session

    points_by_seq = {}
    session_started = now_iso()
    archived_this_session = False
    save_current()
    print("[SESSION] reset", flush=True)


def on_connect(client, userdata, flags, rc):
    print(f"[MQTT] connected rc={rc}", flush=True)
    client.subscribe(POINT_TOPIC)
    client.subscribe(STATE_TOPIC)


def on_message(client, userdata, msg):
    global session_started, last_state

    topic = msg.topic
    text = msg.payload.decode("utf-8", errors="replace").strip()

    if topic == STATE_TOPIC:
        state = text

        if state != last_state:
            print(f"[STATE] {state}", flush=True)
            last_state = state

        if state in ("cleaning", "spot_cleaning", "edge_cleaning", "zmode_cleaning"):
            if session_started is None or archived_this_session:
                reset_session()

        if state in ("charging", "docked"):
            archive_current(state)

        if session_started is not None:
            save_current()
        return

    if topic == POINT_TOPIC:
        if session_started is None:
            reset_session()

        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            print(f"[WARN] invalid json: {e}: {text}", flush=True)
            return

        added = 0

        for p in data.get("p", []):
            if not isinstance(p, list) or len(p) != 4:
                continue

            seq, x, y, kind = p
            seq = int(seq)

            if seq not in points_by_seq:
                points_by_seq[seq] = {
                    "seq": seq,
                    "x": int(x),
                    "y": int(y),
                    "type": int(kind),
                }
                added += 1

        if added:
            print(f"[POINTS] +{added}, total={len(points_by_seq)}", flush=True)
            save_current()


def main() -> None:
    client = mqtt.Client()

    if MQTT_USER:
        client.username_pw_set(MQTT_USER, MQTT_PASSWORD)

    client.on_connect = on_connect
    client.on_message = on_message

    write_archive_index()

    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.loop_forever()


if __name__ == "__main__":
    main()
