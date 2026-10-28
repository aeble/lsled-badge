# lsled-badge

Text auf LED-Namensbadges vom Typ LSLED schicken, mit Vorschau im Terminal und im Browser.

Gemeint sind die Badges, die sich per BLE als `LSLED` melden und den Service `fee0` mit der Characteristic `fee1` anbieten (dieselben, die die Badge-Magic-App steuert). Das Protokoll schickt Klartext-Pakete mit dem Header `wang`. Getestet mit einem Badge mit 44×11 Pixeln.

## Installation

```bash
uv pip install -e ~/Documents/lsled-badge
```

Python 3.10 oder neuer, einzige Abhängigkeit ist `bleak`.

## Benutzung

```bash
lsled scan                                  # Badges in Reichweite mit Adresse
export LSLED_ADDR=<Adresse aus lsled scan>

lsled preview Balrog                        # nur Vorschau
lsled send Balrog                           # Vorschau zeigen und senden
lsled send -f helv --bold -b 50 Balrog      # anderer Font, fett, 50 % Helligkeit
lsled send -m left -s 3 "Ein langer Text"   # durchlaufen lassen, Geschwindigkeit 3
lsled send --autoscroll "Text"              # statisch, wenn er passt, sonst durchlaufen
lsled fonts                                 # vorhandene Fonts
lsled web                                   # Weboberfläche auf http://localhost:8044/
```

| Option | Werte | Standard |
|:---|:---|:---|
| `-d`, `--driver` | Badge-Typ, siehe Abschnitt Treiber | `lsled` |
| `-f`, `--font` | siehe `lsled fonts` | `5x9` |
| `--bold` | jede Glyphe eine Spalte breiter | aus |
| `--autoscroll` | bei `static` nach links laufen, wenn der Text nicht passt | aus |
| `-m`, `--mode` | `static`, `left`, `right`, `up`, `down`, `animation`, `snowflake`, `picture`, `laser` | `static` |
| `-b`, `--brightness` | 1–100 (Prozent; LSLED kennt nur 25/50/75/100 und nimmt die nächste Stufe) | 25 |
| `-s`, `--speed` | 1–8 | 5 |
| `-a`, `--address` | BLE-Adresse (macOS: UUID) | `$LSLED_ADDR` |

Im statischen Modus wird der Text zentriert. Ist er zu breit, bricht `lsled` vor dem Senden ab, mit `--autoscroll` läuft er stattdessen nach links durch. In der Weboberfläche heißt der Schalter „durchlaufen, wenn zu breit“.

## Weboberfläche

`lsled web` startet einen lokalen Server und öffnet die Seite. Text, Font, Modus und Helligkeit lassen sich dort einstellen, die Vorschau folgt sofort. Senden geht nur in Chrome oder Edge, weil Safari und Firefox kein Web Bluetooth können. Die Seite holt Fonts und Displaykonstanten unter `/config.json` vom Server, beide Oberflächen nutzen also dieselben Fontdateien.

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

Der Import schneidet leere Ränder ab und macht aus Festbreiten- Proportionalfonts. Brauchbar sind nur Fonts, die Pixel mit einem Füllzeichen zeichnen. Die üblichen figlet-Fonts wie `standard` oder `big` sind Strichzeichnungen und ergeben auf dem Display nichts Lesbares. In `bdffonts` haben nur `5x7`, `6x10` und die Helvetica-/Courier-Varianten Umlaute, `5x8.flf` hat einen fehlerhaften Kopf und lässt sich nicht einlesen.

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
  drivers/     base.py, lsled.py                         Pixel -> Schreibvorgänge je Badge-Typ, ohne I/O
  transport/   ble.py                                    bleak: Scan, Schreibvorgänge ausführen
  app.py                                                 gemeinsamer Ablauf für CLI und Server
  ui/          cli.py, preview.py, server.py             Kommandozeile, Terminal-Vorschau, HTTP-API
  web/         index.html                                Darstellung, Bedienung, Web Bluetooth
  fonts/, locales/                                       Daten
```

Abhängigkeiten zeigen nur nach unten: `ui` → `app` → `drivers`/`transport` → `core`. Die Webseite rechnet nichts selbst: Sie schickt ihre Einstellungen an `POST /render` und bekommt Pixelfläche, verwendeten Modus und die fertige Liste der Schreibvorgänge zurück, die sie per Web Bluetooth ausführt.

## Treiber

Ein Treiber (`drivers/base.py`) beschreibt Displaygröße, Modi, Erkennung beim Scan und die Characteristics, deren Benachrichtigungen vor dem Schreiben eingeschaltet sein müssen. `build_writes()` macht aus Pixelfläche, Modus, Geschwindigkeit (1–8) und Helligkeit (Prozent) eine Liste von Schreibvorgängen (Characteristic, Bytes, mit/ohne Antwort, Pause danach). Neue Badge-Typen sind eine neue Datei in `drivers/` plus Eintrag in `drivers/__init__.py`.

| Treiber | Badge | Display |
|:---|:---|:---|
| `lsled` | LSLED, Service `fee0`, Klartextprotokoll „wang“ | 44×11, gemessen |

## LSLED-Protokoll

Ein Datensatz besteht aus 64 Byte Kopf und der Bitmap, aufgefüllt auf ein Vielfaches von 16 und in 16-Byte-Paketen auf `fee1` geschrieben (mit Antwort).

| Byte | Inhalt |
|:---|:---|
| 0–3 | `wang` |
| 5 | Helligkeit: `0x00` 100 %, `0x10` 75 %, `0x20` 50 %, `0x40` 25 % |
| 8 | Nachricht 1: Geschwindigkeit (0–7) im oberen, Modus im unteren Halbbyte |
| 16–17 | Länge von Nachricht 1 in Kacheln, Big Endian |
| 38–43 | Zeitstempel: Jahr (zweistellig), Monat, Tag, Stunde, Minute, Sekunde |

Die Bitmap besteht aus Kacheln zu 8 Spalten × 11 Zeilen, ein Byte pro Zeile, höchstwertiges Bit links.

⚠ Im statischen Modus zeigt das Badge Bitmap-Spalte n auf Displayspalte n+2 (gemessen). Der Treiber gleicht das aus (`static_x_shift` in `drivers/lsled.py`). Die Displayspalten 0 und 1 sind statisch nicht erreichbar, nutzbar sind 42 Spalten.
