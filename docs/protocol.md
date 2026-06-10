# Tesvor X500 UART-Protokoll

## Frame-Grundstruktur

Viele Befehle folgen diesem Muster:

```text
AA LEN CMD GROUP VALUE CHECKSUM
```

Die bekannten Steuerkommandos haben `LEN = 03`.

## Reinigungskommandos

| Funktion | Frame | Stand |
|---|---|---|
| Edge Cleaning | `AA 03 02 22 00 24` | bestätigt |
| Spot Cleaning | `AA 03 02 22 01 25` | bestätigt |
| Smart Cleaning | `AA 03 02 22 02 26` | bestätigt |
| Go Charge | `AA 03 02 22 03 27` | bestätigt |
| Zickzack / Wischen | `AA 03 02 22 04 28` | bestätigt, Status `0x0B` |
| Mop Cleaning Test | `AA 03 02 22 05 29` | ACK, aber nicht als zuverlässiger Startmodus bestätigt |

## Stop

| Funktion | Frame |
|---|---|
| Stop | `AA 03 02 26 00 28` |

## Richtungsbefehle

Die Richtungsbefehle senden erst die Richtung und anschließend Stop/Neutral:

| Funktion | Frame |
|---|---|
| Vorwärts | `AA 03 02 21 00 23` + `AA 03 02 21 04 27` |
| Links | `AA 03 02 21 01 24` + `AA 03 02 21 04 27` |
| Rechts | `AA 03 02 21 02 25` + `AA 03 02 21 04 27` |
| Rückwärts | `AA 03 02 21 03 26` + `AA 03 02 21 04 27` |

## Wischintensität

| Option | Frame | Stand |
|---|---|---|
| Low | `AA 03 02 24 00 26` | ACK bestätigt |
| Default | `AA 03 02 24 01 27` | Muster plausibel |
| High | `AA 03 02 24 02 28` | ACK bestätigt |
| Off | `AA 03 02 24 03 29` | Muster plausibel |

## Saugstärke / Fan

Die Original-Firmware enthält Fan-Kommandos. Die Befehle werden per UART mit ACK quittiert; eine zuverlässige Rückmeldung über den normalen Statusframe wurde bisher nicht bestätigt.

| Option | Frame | Stand |
|---|---|---|
| Normal | `AA 03 02 25 01 28` | ACK |
| Strong | `AA 03 02 25 02 29` | ACK |
| Pause | `AA 03 02 25 03 2A` | ACK |
| Quiet | `AA 03 02 25 04 2B` | ACK |

## Statusframes

Statusframes:

```text
AA 1C 06 ...
```

Checksumme: additive Summe über Payload-Bytes `bytes[2..29]`.

| Statusbyte | Bedeutung |
|---|---|
| `0x00` | edge cleaning |
| `0x01` | spot cleaning |
| `0x02` | cleaning |
| `0x03` | returning |
| `0x04` | idle |
| `0x05` | hibernated |
| `0x06` | charging |
| `0x08` | docked |
| `0x09` | error |
| `0x0A` | setting |
| `0x0B` | zmode cleaning |

## Mapframes

Mapframes beginnen mit:

```text
AA LL 03 01 40 00 00 NN
```

Danach folgen `NN` Punkte à 8 Byte:

```text
seq_hi seq_lo x_hi x_lo y_hi y_lo type reserved
```

Der ESP veröffentlicht daraus MQTT-Batches:

```json
{"p":[[seq,x,y,type]]}
```
