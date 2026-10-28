# lsled-badge

[English](README.md) · **Deutsch**

Text auf LED-Namensbadges vom Typ LSLED schicken, mit Vorschau im Terminal und im Browser.

Gemeint sind die Badges, die sich per BLE als `LSLED` melden und den Service `fee0` mit der Characteristic `fee1` anbieten (dieselben, die die Badge-Magic-App steuert). Das Protokoll schickt Klartext-Pakete mit dem Header `wang`. Getestet mit einem Badge mit 44×11 Pixeln.

## Installation

```bash
uv tool install git+https://github.com/aeble/lsled-badge
```

Python 3.10 oder neuer, Abhängigkeiten `bleak` und `pycryptodome` (für den Treiber `timhodson`).

## Benutzung

```bash
lsled scan                                  # Badges in Reichweite mit Adresse (vorher am Badge den Bluetooth-Modus einschalten)
export LSLED_ADDR=<Adresse aus lsled scan>

lsled preview Balrog                        # nur Vorschau
lsled send Balrog                           # Vorschau zeigen und senden
lsled send -f helv --bold -b 50 Balrog      # anderer Font, fett, 50 % Helligkeit
lsled send -m left -s 3 "Ein langer Text"   # durchlaufen lassen, Geschwindigkeit 3
lsled send --autoscroll "Text"              # statisch, wenn er passt, sonst durchlaufen
lsled send --pages -m up "Ein langer Text"  # zu breit: eine Seite pro Bildschirm, nacheinander
lsled fonts                                 # vorhandene Fonts
lsled web                                   # Weboberfläche auf http://localhost:8044/
```

| Option | Werte | Standard |
|:---|:---|:---|
| `-d`, `--driver` | Badge-Typ, siehe Abschnitt Treiber | `lsled` |
| `-f`, `--font` | siehe `lsled fonts` | `5x9` |
| `--bold` | jede Glyphe eine Spalte breiter | aus |
| `--autoscroll` | nach links laufen, wenn der Text nicht aufs Display passt | aus |
| `--pages` | Text, der nicht passt, an Leerzeichen auf nacheinander gezeigte Seiten verteilen (LSLED: bis 8) | aus |
| `-m`, `--mode` | `static`, `left`, `right`, `up`, `down`, `animation`, `snowflake`, `picture`, `laser` | `static` |
| `-b`, `--brightness` | 1–100 (Prozent; LSLED kennt nur 25/50/75/100 und nimmt die nächste Stufe) | 25 |
| `-s`, `--speed` | 1–8 | 5 |
| `-a`, `--address` | BLE-Adresse (macOS: UUID) | `$LSLED_ADDR` |

Bei `left` und `right` lässt das Badge den Text durchlaufen, egal wie breit er ist. Alle anderen Modi zeigen einen Bildschirm: Der Text wird zentriert und muss aufs Display passen. Ist er zu breit, bricht `lsled` vor dem Senden ab. Mit `--autoscroll` läuft er stattdessen nach links durch, mit `--pages` wird er an Leerzeichen auf Seiten verteilt, die das Badge im gewählten Modus nacheinander zeigt, alle auf derselben Grundlinie. Die Weboberfläche bietet dieselbe Wahl unter „Wenn zu breit“.

## Weboberfläche

`lsled web` startet einen lokalen Server und öffnet die Seite. Text, Font, Modus und Helligkeit lassen sich dort einstellen, die Vorschau folgt sofort.

Gesendet wird auf einem von zwei Wegen:

- **Über den Server** (jeder Browser): „Suchen“ listet die Badges in Reichweite, „Senden“ schickt über das Bluetooth des Rechners, auf dem `lsled web` läuft.
- **Über den Browser** (Chrome, Edge und andere Chromium-Browser): „Badge verbinden“ nutzt Web Bluetooth. Der Knopf erscheint nur, wenn der Browser das kann; Firefox und Safari können es nicht.

Besteht eine Browser-Verbindung, geht „Senden“ dorthin, sonst an das ausgewählte Badge über den Server. Die Seite holt Fonts und Displaykonstanten unter `/config.json` vom Server, beide Oberflächen nutzen also dieselben Fontdateien.

## Fonts

Fonts liegen als JSON in `src/lsled/fonts/`. Jede Glyphe ist eine Liste von Zeilen aus `#` (Pixel an) und `.` (aus), alle Zeilen einer Glyphe gleich breit. Glyphen dürfen unterschiedlich breit sein; zwischen zwei Zeichen setzt der Renderer eine leere Spalte. Fehlt einem Font ein Kleinbuchstabe, nimmt er den Großbuchstaben.

```json
"l": ["##.", ".#.", ".#.", ".#.", ".#.", ".#.", "###", "...", "..."]
```

| Font | Höhe | Art |
|:---|:---|:---|
| `5x9` | 9 | Standard, Groß- und Kleinbuchstaben mit Unterlängen, Umlaute, ♥ |
| `5x9-mono` | 9 | `5x9` mit fester Breite von 5 Pixeln |
| `5x9-italic` | 9 | `5x9` schräg, alle drei Zeilen eine Spalte |
| `3x5` | 5 | klein, nur Großbuchstaben und Ziffern |
| `block` | 10 | `3x5` mit 2×2-Pixeln, schwer und gut lesbar aus der Ferne |
| `space` | 11 | Sci-Fi-Großbuchstaben mit abgeschrägten Ecken, Umlaute, ★ ♥ 🚀; zum Durchlaufen gedacht |

`--bold` funktioniert mit jedem Font. `5x9`, `3x5` und `space` sind von Hand gezeichnet, `5x9-mono`, `5x9-italic` und `block` daraus abgeleitet. Die übrigen stammen aus den Pixelfonts, die figlet unter `share/figlet/fonts/bdffonts` mitliefert (X11 Misc-Fixed, Schumacher Clean, Adobe Helvetica). Weitere lassen sich übernehmen:

```bash
lsled import-figlet "$(brew --prefix)/share/figlet/fonts/bdffonts/clr6x8.flf"
```

Der Import schneidet leere Ränder ab und macht aus Festbreiten- Proportionalfonts. Den Kommentarblock der `.flf`-Datei mit Copyright und Lizenz übernimmt er in das Feld `notice`; die Lizenzen der X11-Fonts verlangen, dass dieser Text mitgeliefert wird. Brauchbar sind nur Fonts, die Pixel mit einem Füllzeichen zeichnen. Die üblichen figlet-Fonts wie `standard` oder `big` sind Strichzeichnungen und ergeben auf dem Display nichts Lesbares. In `bdffonts` haben nur `5x7`, `6x10` und die Helvetica-/Courier-Varianten Umlaute, `5x8.flf` hat einen fehlerhaften Kopf und lässt sich nicht einlesen.

## Sprachen

Englisch, Deutsch, Französisch, Spanisch, Portugiesisch, Finnisch, Estnisch, Lettisch, Litauisch, Schwedisch, Norwegisch (Bokmål), Dänisch, Niederländisch, Ukrainisch, vereinfachtes Chinesisch, Japanisch und Koreanisch. Die Kataloge liegen als JSON in `src/lsled/locales/`, CLI und Weboberfläche lesen dieselben Dateien. Fehlt in einem Katalog ein Schlüssel, steht der englische Text da.

Die CLI nimmt die erste passende Sprache aus `LANGUAGE`, `LC_ALL`, `LC_MESSAGES` und `LANG` (wie gettext), unter macOS ohne gesetzte Variablen `AppleLocale`. Die Weboberfläche nimmt die Browsersprachen. `no` und `nn` gelten als Bokmål, `zh-CN`/`zh-SG`/`zh-Hans` als vereinfachtes Chinesisch; traditionelles Chinesisch und alles Unbekannte fällt auf Englisch.

```bash
LANG=ja_JP.UTF-8 lsled --help
```

Die festen Texte von argparse (`usage:`, `options:`, `show this help message and exit`) bleiben englisch.

## Aufbau

```
src/lsled/
  core/        fonts.py, figlet.py, render.py, i18n.py   Text -> Pixel, Layout, Übersetzungen
  drivers/     base.py, lsled.py, timhodson.py           Pixel -> Schreibvorgänge je Badge-Typ, ohne I/O
  transport/   ble.py                                    bleak: Scan, Schreibvorgänge ausführen
  app.py                                                 gemeinsamer Ablauf für CLI und Server
  ui/          cli.py, preview.py, server.py             Kommandozeile, Terminal-Vorschau, HTTP-API
  web/         index.html                                Darstellung, Bedienung, optional Web Bluetooth
  fonts/, locales/                                       Daten
```

Abhängigkeiten zeigen nur nach unten: `ui` → `app` → `drivers`/`transport` → `core`. Die Webseite rechnet nichts selbst: Sie schickt ihre Einstellungen an `POST /render` und bekommt Pixelfläche, verwendeten Modus und die fertige Liste der Schreibvorgänge zurück. Diese führt sie per Web Bluetooth aus, oder sie lässt den Server über `POST /send` senden.

## Treiber

Ein Treiber (`drivers/base.py`) beschreibt Displaygröße, Modi (welche durchlaufen und wie weit die übrigen verschieben), Erkennung beim Scan und die Characteristics, deren Benachrichtigungen vor dem Schreiben eingeschaltet sein müssen. `build_writes()` macht aus Pixelfläche, Modus, Geschwindigkeit (1–8) und Helligkeit (Prozent) eine Liste von Schreibvorgängen (Characteristic, Bytes, mit/ohne Antwort, Pause danach). Neue Badge-Typen sind eine neue Datei in `drivers/` plus Eintrag in `drivers/__init__.py`.

| Treiber | Badge | Display |
|:---|:---|:---|
| `lsled` | LSLED, Service `fee0`, Klartextprotokoll „wang“ | 44×11, gemessen |
| `timhodson` | Service `fee9`, AES-verschlüsselte Befehle | 48×12 laut Typkennung `STYPE12X48N` |

⚠ `timhodson` ist am Gerät nicht getestet. Protokoll, Schlüssel und Zellkodierung stammen aus [timhodson/ble-led-badge](https://github.com/timhodson/ble-led-badge). Geprüft ist, dass Befehle, Datenpakete und die Kodierung aller 150 Zeichensegmente seines Fonts byte-gleich mit seinem Code sind. Offen sind die Verschiebung im statischen Modus, die Richtung der Geschwindigkeit (1–8 wird auf 0–255 verteilt) und ob die feste Pause nach `DATS` statt des Wartens auf `DATSOK` reicht.

## LSLED-Protokoll

Ein Datensatz besteht aus 64 Byte Kopf und der Bitmap, aufgefüllt auf ein Vielfaches von 16 und in 16-Byte-Paketen auf `fee1` geschrieben (mit Antwort).

| Byte | Inhalt |
|:---|:---|
| 0–3 | `wang` |
| 5 | Helligkeit: `0x00` 100 %, `0x10` 75 %, `0x20` 50 %, `0x40` 25 % |
| 8–15 | Nachricht 1–8: Geschwindigkeit (0–7) im oberen, Modus im unteren Halbbyte |
| 16–31 | Länge von Nachricht 1–8 in Kacheln, Big Endian, je zwei Byte |
| 38–43 | Zeitstempel: Jahr (zweistellig), Monat, Tag, Stunde, Minute, Sekunde |

Die Bitmaps aller Nachrichten folgen direkt aufeinander. Eine Bitmap besteht aus Kacheln zu 8 Spalten × 11 Zeilen, ein Byte pro Zeile, höchstwertiges Bit links. Das Badge zeigt die Nachrichten von selbst nacheinander (getestet mit drei). Im Modus `animation` spielt eine Bitmap aus mehreren Bildern zu 48 Spalten als Animation ab (getestet mit drei).

⚠ Im Modus `static` setzt die Firmware den Inhalt nach einer eigenen Regel (gemessen: je nach Inhalt um eine oder zwei Spalten verschoben). Alle anderen Modi zeigen die Bitmap genau wie gesendet, und eine `animation` aus einem einzigen Bild steht still. Der Treiber schickt `static` deshalb als einbildige `animation` (`WIRE_MODES` in `drivers/lsled.py`). Bildschirm-Modi nutzen damit alle 44 Spalten; was breiter ist, schneidet das Badge ab. Mit `--pages` bestimmt die Geschwindigkeit, wie schnell statische Seiten wechseln.

Nach dem Empfang verlässt das Badge den Bluetooth-Modus; vor der nächsten Übertragung muss er wieder eingeschaltet werden.

## Herkunft und Lizenzen

lsled-badge steht einschließlich der von Hand gezeichneten Fonts `5x9`, `3x5`, `space` und der daraus abgeleiteten unter der MIT-Lizenz, siehe [LICENSE](LICENSE).

- Der Treiber `timhodson` beruht auf der Protokollanalyse in [timhodson/ble-led-badge](https://github.com/timhodson/ble-led-badge) von Tim Hodson: Befehle, AES-Schlüssel und Zellkodierung. Der Code hier ist neu geschrieben. Das Projekt gibt in seiner `pyproject.toml` die MIT-Lizenz an, hat aber keine Lizenzdatei.
- Die aus figlets `bdffonts` importierten Fonts behalten ihre eigenen Lizenzen: X Consortium (`5x7`, `6x9`), Schumacher (`clr4x6`, `clr5x8`), Adobe/Digital (`helv`, `helvb`), Public Domain (`6x10`). Der vollständige Copyright- und Lizenztext steht im Feld `notice` der jeweiligen Font-Datei.
