# Offene Protokoll-Punkte & Leads für Contributors

Dieses Dokument sammelt **bestätigte, aber noch nicht zugeordnete** Teile des UART-Protokolls
sowie offene Fragen. Ziel: dem nächsten Bastler einen Startpunkt geben und PRs einladen.

**Konvention:** ✅ bestätigt (gemessen/validiert) · ❓ Hypothese (plausibel, ungetestet) · ⚠️ Vorsicht beim Testen.

---

## Bestätigte Basis (Kurzfassung)

- **UART:** 115200 Baud, 8N1, Pegel 3.3 V.
- **Frame:** `AA | LEN | PAYLOAD | CHECKSUM`, Gesamtlänge = `LEN + 3`.
- **Checksum:** additive Summe der PAYLOAD-Bytes mod 256 (`bytes[2 .. 2+LEN-1]`), abgelegt in `bytes[2+LEN]`.
  ✅ Verifiziert über Kommando- **und** Status-Frames (69/69 Status-Frames eines Live-Mitschnitts). Kein CRC8.
- **Frame-Kategorie** (`PAYLOAD[0]`): `0x02` Kommando (ESP→MCU) · `0x03` Map (MCU→ESP) · `0x06` Status (MCU→ESP).
- **Status-Frame** `AA 1C 06 …` (31 Byte): `state = byte6`, `error = byte28`, `battery = byte29`, `checksum = byte30`.

**State-Bytes (byte6):**
`00` Edge · `01` Spot · `02` Smart-Clean · `03` Returning · `04` Idle · `05` Hibernated ·
`06` Charging · `08` Docked · `09` Error · `0A` Unknown/setting-like · `0B` Zmode.

Notes:
- `0x0B` is confirmed by live testing: sending Zmode command `AA 03 02 22 04 28` causes state `0x0B` and continuous map/path frames.
- `0x0A` was observed in setting/timer-like contexts but is not yet as strongly validated as a named mode.

**Bestätigte Kommandos** (`AA 03 02 <cmd> <param> <cks>`):

| Opcode | Params | Funktion |
| ------ | ------ | -------- |
| `0x21` | 00–04 | Richtung (04 = Stop/Keepalive) |
| `0x22` | 00–05 | Mode: 00 Edge · 01 Spot · 02 Smart · 03 Charge · 04 Zmode · 05 Mop candidate |
| `0x24` | 00–03 | Water flow / mop intensity: 00 Low ✅ · 01 Default ❓ · 02 High ✅ · 03 Off ❓ |
| `0x25` | 01–04 | Fan/suction command: 01 Normal · 02 Strong · 03 Pause · 04 Quiet |
| `0x26` | 00 | Stop |

---

## Lead 1 — Unzugeordnete Kommando-Opcodes

Die folgenden Opcodes sind als gültige Kommando-Templates im originalen 4-MB-Dump enthalten:
**prüfsummen-gültig und in beiden OTA-App-Slots** vorhanden (= echte Tabelleneinträge, kein Rauschen).
Ihre **Funktion ist nicht bestätigt**.

| Opcode | Params | Status | Hypothese |
| ------ | ------ | ------ | --------- |
| `0x10` | 01 | ✅ existiert · ❓ Funktion | System/Handshake („app online"/Request) |
| `0x28` | 00 / 01 | ✅ · ❓ | Boolean-Toggle — evtl. Voice an/aus (`voice_switch`) |
| `0x32` | 00 / 01 | ✅ · ❓ | Boolean-Toggle — DND / Carpet-Boost? |
| `0x33` | 00 / 01 / 02 | ✅ · ❓ | 3-stufige Einstellung (unbekannt) |
| `0x41` | 00 | ✅ · ❓ ⚠️ | Single-Shot-Trigger — Locate? oder Reset/Kalibrierung |
| `0x43` | 00 / 01 | ✅ · ❓ | Boolean-Toggle (unbekannt) |
| `0x45` | 00 / 01 | ✅ · ❓ | Boolean-Toggle (unbekannt) |

Vollständiger statischer Opcode-Satz im Dump: `10, 21, 22, 24, 25, 26, 28, 32, 33, 41, 43, 45`.

---

## Lead 2 — Zeit & Zeitplan (dynamische Mehrbyte-Kommandos)

Die Fernbedienung setzt Uhrzeit (Uhr-Taste) und geplante Reinigung (Kalender-Taste).
Diese Kommandos sind **mehrbyte und werden zur Laufzeit aus den aktuellen Werten gebaut** —
sie stehen daher **nicht** als statische Templates im Dump (bestätigt: 0 Mehrbyte-`0x02`-Templates gefunden).
Format nur per **Live-Mitschnitt** zu ermitteln.
Hinweis: Der ESP-seitige Zeit-Sync der Original-Firmware hing an der inzwischen toten WeBack-Cloud.

---

## Lead 3 — Telemetrie: water_level / fan_status / clean_time

Die Original-Cloud kannte `water_level`, `left_water`, `fan_status`, `clean_time_s` (Shadow-Datapoints).
In einem **Trocken-Reinigungslauf** waren die Status-Bytes 7 und 9–27 jedoch durchgehend `0x00` —
diese Werte stecken also **nicht** im Status-Frame eines Trockenlaufs.

- `clean_time`: wird vom MCU **nicht** gemeldet → ESP-seitig zählen (so macht es dieses Projekt).
- `water_level`: vermutlich nur bei eingesetztem Wassertank aktiv.
  **Test:** Tank (Wasser + Tuch) einsetzen, Reinigung starten, UART-Log beobachten — wird dann ein Byte/Frame ≠ 0?
- `fan_status`: im Trockenlauf nicht im Status-Frame erkennbar; am einfachsten ESP-seitig aus dem
  zuletzt gesendeten `0x25` spiegeln.

---

## Lead 4 — Frame-Kategorie 0x05 / Map-Marker `03 05`

- Im Live-Mitschnitt tauchte ein Mini-Frame `AA 02 03 05 08` auf (Kategorie `0x03`, Subtyp `05`) —
  vermutlich ein **Map-Session-Marker** (Start/Ende Map-Transfer).
- Der statische Firmware-Scan zeigte zusätzlich eine mögliche Kategorie `0x05`
  (schwaches Signal, im Live-Mitschnitt nicht beobachtet). Beim Sniffen darauf achten.

---

## Lead 5 — Status-Frame Byte 7 / Byte 8

Bytes 7 and 8 are not fully understood.

Observed:
- Smart cleaning status frames often look like `... state=0x02 byte7=0x00 byte8=0x00 ...`.
- Idle/charging frames often show `byte8=0x02`.
- Zmode/wet-mopping captures showed combinations like `state=0x0B byte7=0x02 byte8=0x02`.

Meaning unconfirmed. Keep both bytes as diagnostic raw values when investigating water tank, fan mode, sub-mode or activity phase.

---

## Kontext — Capabilities laut Original-Cloud (Shadow-Datapoints)

Hilfreich zum Zuordnen der offenen Opcodes:

`voice_switch`, `voice_pack_id`, `Voicebox_Source`, `local_voice_pack_list` ·
`weekday`, `clean_timer`, `timestamp` / `timestamp_ms` ·
`AutoClean`, `final_edge` · `device_2_app_proto_version` ·
Faults: `BrushTangled`, `RollingBrushWinded`, `NoWaterBox`, `NoWaterMop`, `WaterBoxEmpty`, `WaterPumpError`.

---

## Sicheres Vorgehen beim Testen unbekannter Opcodes

1. **Bench-Setup**, Roboter von der Ladestation, nichts Zerbrechliches in Reichweite.
2. Ein **einzelnes** Kommando aus ESPHome senden, Reaktion + Status-Frame-Änderungen im UART-Debug-Log beobachten.
3. Mit den Boolean-Toggles beginnen (`0x28`, `0x32`, `0x33`, `0x43`, `0x45`).
4. ⚠️ Single-Shots (`0x41`, `0x10`) **zuletzt** — ein unbekannter Trigger kann Werksreset,
   Kalibrierung oder Motor-Selbsttest auslösen.
5. Vollständiges 4-MB-Backup der Original-Firmware bereithalten.
