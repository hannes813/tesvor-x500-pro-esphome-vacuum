# Aktuelle Erkenntnisse

## Mop Cleaning vs. Zmode

`Mop Cleaning` (`AA 03 02 22 05 29`) wird vom Roboter zwar mit ACK bestätigt, startet aber auf dem getesteten Gerät nicht zuverlässig als eigenständiger Reinigungsmodus.

`Zickzack / Wischen` (`AA 03 02 22 04 28`) ist dagegen funktional bestätigt und führt zu Status `0x0B`.

Praktische Interpretation:

```text
Wischen = Wassertank/Tuch eingesetzt + Zickzack/Bahnenmodus oder Smart Cleaning
```

## Wischintensität

Low und High wurden im Lauf getestet und mit ACK quittiert. Default und Off folgen dem bestätigten Byte-Muster.

## Fan / Saugstärke

Die Original-Firmware enthält die Fan-Kommandos:

```text
Normal, Strong, Pause, Quiet
```

Die UART-Befehle werden mit ACK bestätigt. In den sichtbaren Statusframes wird die geänderte Lüfterstufe aktuell aber nicht zuverlässig zurückgemeldet. Deshalb bleibt die Entität im Projekt bewusst als `Saugstärke Test experimentell`.

## Reinigungsdauer

Die MCU liefert keine saubere Laufzeit. Die Reinigungsdauer wird daher ESP-seitig gezählt, sobald ein Reinigungsstatus aktiv ist:

```text
0x00 edge cleaning
0x01 spot cleaning
0x02 cleaning
0x0B zmode cleaning
```

## Karte

Der Roboter liefert keine LiDAR-Karte, sondern Pfad-/Gyro-Punkte. Das Projekt visualisiert diese Punkte als einfache Route.
