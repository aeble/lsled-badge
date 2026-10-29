# lsled-badge

**English** · [Deutsch](README.de.md)

Send text to LSLED name badges over Bluetooth LE or USB, with a preview in the terminal and in the browser.

This targets the badges that advertise as `LSLED` and offer service `fee0` with characteristic `fee1` (the ones the Badge Magic app controls). The protocol sends plaintext packets with the header `wang`. Tested with a 44×11 pixel badge.

On USB, the same badges (chip CH583) appear as HID device `0416:5020`, the ID of the older LS32 badges, and take the same record.

## Installation

```bash
uv tool install git+https://github.com/aeble/lsled-badge
```

Python 3.10 or newer; dependencies are `bleak`, `hidapi` (USB) and `pycryptodome` (for the `timhodson` driver).

On Linux the user needs access to the HID device, for example with a udev rule in `/etc/udev/rules.d/70-lsled.rules` (untested):

```
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="0416", ATTRS{idProduct}=="5020", TAG+="uaccess"
```

## Usage

```bash
lsled scan                                  # badges plugged in or in range, with address (switch the badge to Bluetooth mode first)
export LSLED_ADDR=<address from lsled scan>

lsled preview Balrog                        # preview only
lsled send Balrog                           # show the preview and send
lsled send -f helv --bold -b 50 Balrog      # other font, bold, 50 % brightness
lsled send -m left -s 3 "A longer text"     # scroll, speed 3
lsled send --autoscroll "Text"              # static if it fits, otherwise scroll
lsled send --pages -m up "A longer text"    # too wide: one page per screen, shown in turn
lsled send -d lsled-usb Balrog              # via USB, to the first badge plugged in
lsled fonts                                 # available fonts
lsled web                                   # web interface on http://localhost:8044/
```

| Option | Values | Default |
|:---|:---|:---|
| `-d`, `--driver` | badge type, see Drivers | `lsled` |
| `-f`, `--font` | see `lsled fonts` | `5x9` |
| `--bold` | every glyph one column wider | off |
| `--autoscroll` | scroll left if the text does not fit on the display | off |
| `--pages` | split text that does not fit at spaces into pages shown in turn (LSLED: up to 8) | off |
| `-m`, `--mode` | `static`, `left`, `right`, `up`, `down`, `animation`, `snowflake`, `picture`, `laser` | `static` |
| `-b`, `--brightness` | 1–100 (percent; LSLED only knows 25/50/75/100 and takes the nearest step) | 25 |
| `-s`, `--speed` | 1–8 | 5 |
| `-a`, `--address` | BLE address (macOS: UUID) or USB path from `lsled scan` | `$LSLED_ADDR`; USB: first badge plugged in |

In `left` and `right` the badge scrolls the text, whatever its width. All other modes show one screen: the text is centered and must fit. If it is too wide, `lsled` stops before sending; with `--autoscroll` it scrolls left instead, and with `--pages` it is split at spaces into pages that the badge shows one after another in the chosen mode, all on a common baseline. The web interface offers the same choice under “If too wide”.

## Web interface

`lsled web` starts a local server and opens the page. Text, font, mode and brightness can be set there, and the preview follows immediately.

There are two ways to send:

- **Through the server** (any browser): “Search” lists the badges in range (badge type `lsled-usb`: plugged in), “Send” transmits via Bluetooth or USB of the machine running `lsled web`.
- **Through the browser** (Chrome, Edge and other Chromium browsers): “Connect badge” uses Web Bluetooth. The button only appears if the browser supports it (Firefox and Safari do not) and for Bluetooth badge types.

With a browser connection, “Send” goes there; otherwise it goes to the selected badge through the server. The page fetches fonts and display constants from `/config.json`, so both interfaces use the same font files.

## Fonts

Fonts are JSON files in `src/lsled/fonts/`. Each glyph is a list of rows made of `#` (pixel on) and `.` (off), all rows of a glyph equally wide. Glyphs may differ in width; the renderer puts one empty column between characters. If a font lacks a lower-case letter, the capital is used.

```json
"l": ["##.", ".#.", ".#.", ".#.", ".#.", ".#.", "###", "...", "..."]
```

| Font | Height | Style |
|:---|:---|:---|
| `5x9` | 9 | default, upper and lower case with descenders, umlauts, ♥ |
| `5x9-mono` | 9 | `5x9` with a fixed width of 5 pixels |
| `5x9-italic` | 9 | `5x9` slanted, one column per three rows |
| `3x5` | 5 | small, capitals and digits only |
| `block` | 10 | `3x5` with 2×2 pixels, heavy and readable from afar |
| `space` | 11 | sci-fi capitals with chamfered corners, umlauts, ★ ♥ 🚀; made for scrolling |

`--bold` works with every font. `5x9`, `3x5` and `space` are hand-drawn; `5x9-mono`, `5x9-italic` and `block` are derived from them. The others come from the pixel fonts that figlet ships in `share/figlet/fonts/bdffonts` (X11 Misc-Fixed, Schumacher Clean, Adobe Helvetica). More can be imported:

```bash
lsled import-figlet "$(brew --prefix)/share/figlet/fonts/bdffonts/clr6x8.flf"
```

The import strips empty borders and turns fixed-width fonts into proportional ones. It copies the comment block of the `.flf` file, which holds copyright and license, into the `notice` field; the licenses of the X11 fonts require that this text is distributed with them. Only fonts that draw pixels with a fill character are useful. The usual figlet fonts such as `standard` or `big` are line drawings and come out unreadable on the display. In `bdffonts`, only `5x7`, `6x10` and the Helvetica/Courier variants have umlauts; `5x8.flf` has a broken header and cannot be read.

## Languages

English, German, French, Spanish, Portuguese, Finnish, Estonian, Latvian, Lithuanian, Swedish, Norwegian (Bokmål), Danish, Dutch, Ukrainian, Simplified Chinese, Japanese and Korean. The catalogs are JSON files in `src/lsled/locales/`; the command line and the web interface read the same files. A key missing from a catalog falls back to the English text.

The command line takes the first matching language from `LANGUAGE`, `LC_ALL`, `LC_MESSAGES` and `LANG` (like gettext), and on macOS without any of them set, `AppleLocale`. The web interface uses the browser languages. `no` and `nn` count as Bokmål, `zh-CN`/`zh-SG`/`zh-Hans` as Simplified Chinese; Traditional Chinese and anything unknown fall back to English.

```bash
LANG=ja_JP.UTF-8 lsled --help
```

The fixed texts of argparse (`usage:`, `options:`, `show this help message and exit`) stay English.

## Structure

```
src/lsled/
  core/        fonts.py, figlet.py, render.py, i18n.py        text -> pixels, layout, translations
  drivers/     base.py, lsled.py, lsled_usb.py, timhodson.py  pixels -> writes per badge type, no I/O
  transport/   ble.py, usb.py                                 bleak / hidapi: scan, execute writes
  app.py                                                      shared flow for command line and server
  ui/          cli.py, preview.py, server.py                  command line, terminal preview, HTTP API
  web/         index.html                                     display, controls, optional Web Bluetooth
  fonts/, locales/                                            data
```

Dependencies only point downwards: `ui` → `app` → `drivers`/`transport` → `core`. The web page computes nothing itself: it posts its settings to `POST /render` and gets back the canvas, the mode actually used and the finished list of writes. It executes them via Web Bluetooth, or has the server send them via `POST /send`.

## Drivers

A driver (`drivers/base.py`) describes the display size, modes (which of them scroll, and the measured shift of the others), how a scan recognizes the badge, and the characteristics whose notifications must be enabled before writing. `transport` names the module in `transport/` that reaches the badge (`ble` or `usb`; `usb_id` holds vendor and product id). `build_writes()` turns canvas, mode, speed (1–8) and brightness (percent) into a list of writes (characteristic, bytes, with or without response, pause afterwards; over USB every write is one HID report). A new badge type is a new file in `drivers/` plus an entry in `drivers/__init__.py`.

| Driver | Badge | Display |
|:---|:---|:---|
| `lsled` | LSLED, service `fee0`, plaintext protocol “wang” | 44×11, measured |
| `lsled-usb` | USB HID `0416:5020` (LSLED with CH583, LS32), record as `lsled` | 44×11 |
| `timhodson` | service `fee9`, AES-encrypted commands | 48×12 per type string `STYPE12X48N` |

⚠ `timhodson` is untested on hardware. Protocol, key and cell encoding come from [timhodson/ble-led-badge](https://github.com/timhodson/ble-led-badge). Verified: commands, data packets and the encoding of all 150 glyph segments of its font are byte-identical with that code. Open: the offset in static mode, the direction of the speed value (1–8 is spread over 0–255), and whether the fixed pause after `DATS` can replace waiting for `DATSOK`.

## LSLED protocol

A record consists of a 64-byte header and the bitmap, padded to a multiple of 16 and written to `fee1` in 16-byte packets (with response).

| Byte | Content |
|:---|:---|
| 0–3 | `wang` |
| 5 | brightness: `0x00` 100 %, `0x10` 75 %, `0x20` 50 %, `0x40` 25 % |
| 8–15 | messages 1–8: speed (0–7) in the upper, mode in the lower nibble |
| 16–31 | lengths of messages 1–8 in tiles, big endian, two bytes each |
| 38–43 | timestamp: year (two digits), month, day, hour, minute, second |

The bitmaps of all messages follow one after another. A bitmap consists of tiles of 8 columns × 11 rows, one byte per row, most significant bit on the left. The badge shows the messages in turn by itself (tested with three). In `animation` mode, a bitmap of several 48-column frames plays as an animation (tested with three).

⚠ In `static` mode the firmware places the content by a rule of its own (measured: shifts of one and two columns, depending on the content). All other modes show the bitmap exactly as sent, and an `animation` with a single frame stands still. The driver therefore sends `static` as a single-frame `animation` (`WIRE_MODES` in `drivers/lsled.py`). One-screen modes thus use all 44 columns; wider content is cut off by the badge. With `--pages`, the speed sets how fast static pages change.

The badge leaves Bluetooth mode after receiving data; switch it back on before the next transmission.

Over USB the driver `lsled-usb` pads the same record to a multiple of 64 and writes it in HID reports of 64 bytes (report ID 0 in front), with 0.1 s pause after each, as [led-name-badge-ls32](https://github.com/jnweiger/led-name-badge-ls32) does. While plugged in, the badge shows its battery level and a steaming coffee cup. After receiving it shows the reset screen (M1-8) and briefly the first page; the full content only plays once the badge is unplugged.

## Credits and licenses

lsled-badge, including the hand-drawn fonts `5x9`, `3x5`, `space` and the fonts derived from them, is released under the MIT license, see [LICENSE](LICENSE).

- The `timhodson` driver is based on the protocol analysis in [timhodson/ble-led-badge](https://github.com/timhodson/ble-led-badge) by Tim Hodson: commands, AES key and cell encoding. The code here is written anew. That project declares the MIT license in its `pyproject.toml` but has no license file.
- USB ID, report size and pause of the `lsled-usb` driver come from [jnweiger/led-name-badge-ls32](https://github.com/jnweiger/led-name-badge-ls32) by Jürgen Weigert. The code here is written anew.
- The fonts imported from figlet's `bdffonts` keep their own licenses: X Consortium (`5x7`, `6x9`), Schumacher (`clr4x6`, `clr5x8`), Adobe/Digital (`helv`, `helvb`), public domain (`6x10`). The full copyright and license text is in the `notice` field of each font file.
