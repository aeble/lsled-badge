# lsled-badge

**English** · [Deutsch](README.de.md)

Send text to LSLED name badges over Bluetooth LE, with a preview in the terminal and in the browser.

This targets the badges that advertise as `LSLED` and offer service `fee0` with characteristic `fee1` (the ones the Badge Magic app controls). The protocol sends plaintext packets with the header `wang`. Tested with a 44×11 pixel badge.

## Installation

```bash
uv tool install git+https://github.com/aeble/lsled-badge
```

Python 3.10 or newer; dependencies are `bleak` and `pycryptodome` (for the `timhodson` driver).

## Usage

```bash
lsled scan                                  # badges in range, with address (switch the badge to Bluetooth mode first)
export LSLED_ADDR=<address from lsled scan>

lsled preview Balrog                        # preview only
lsled send Balrog                           # show the preview and send
lsled send -f helv --bold -b 50 Balrog      # other font, bold, 50 % brightness
lsled send -m left -s 3 "A longer text"     # scroll, speed 3
lsled send --autoscroll "Text"              # static if it fits, otherwise scroll
lsled fonts                                 # available fonts
lsled web                                   # web interface on http://localhost:8044/
```

| Option | Values | Default |
|:---|:---|:---|
| `-d`, `--driver` | badge type, see Drivers | `lsled` |
| `-f`, `--font` | see `lsled fonts` | `5x9` |
| `--bold` | every glyph one column wider | off |
| `--autoscroll` | scroll left if the text does not fit on the display | off |
| `-m`, `--mode` | `static`, `left`, `right`, `up`, `down`, `animation`, `snowflake`, `picture`, `laser` | `static` |
| `-b`, `--brightness` | 1–100 (percent; LSLED only knows 25/50/75/100 and takes the nearest step) | 25 |
| `-s`, `--speed` | 1–8 | 5 |
| `-a`, `--address` | BLE address (macOS: UUID) | `$LSLED_ADDR` |

In `left` and `right` the badge scrolls the text, whatever its width. All other modes show one screen: the text is centered and must fit. If it is too wide, `lsled` stops before sending; with `--autoscroll` it scrolls left instead. The web interface calls this toggle “scroll if too wide”.

## Web interface

`lsled web` starts a local server and opens the page. Text, font, mode and brightness can be set there, and the preview follows immediately.

There are two ways to send:

- **Through the server** (any browser): “Search” lists the badges in range, “Send” transmits via the Bluetooth of the machine running `lsled web`.
- **Through the browser** (Chrome, Edge and other Chromium browsers): “Connect badge” uses Web Bluetooth. The button only appears if the browser supports it; Firefox and Safari do not.

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
  core/        fonts.py, figlet.py, render.py, i18n.py   text -> pixels, layout, translations
  drivers/     base.py, lsled.py, timhodson.py           pixels -> writes per badge type, no I/O
  transport/   ble.py                                    bleak: scan, execute writes
  app.py                                                 shared flow for command line and server
  ui/          cli.py, preview.py, server.py             command line, terminal preview, HTTP API
  web/         index.html                                display, controls, optional Web Bluetooth
  fonts/, locales/                                       data
```

Dependencies only point downwards: `ui` → `app` → `drivers`/`transport` → `core`. The web page computes nothing itself: it posts its settings to `POST /render` and gets back the canvas, the mode actually used and the finished list of writes. It executes them via Web Bluetooth, or has the server send them via `POST /send`.

## Drivers

A driver (`drivers/base.py`) describes the display size, modes (which of them scroll, and the measured shift of the others), how a scan recognizes the badge, and the characteristics whose notifications must be enabled before writing. `build_writes()` turns canvas, mode, speed (1–8) and brightness (percent) into a list of writes (characteristic, bytes, with or without response, pause afterwards). A new badge type is a new file in `drivers/` plus an entry in `drivers/__init__.py`.

| Driver | Badge | Display |
|:---|:---|:---|
| `lsled` | LSLED, service `fee0`, plaintext protocol “wang” | 44×11, measured |
| `timhodson` | service `fee9`, AES-encrypted commands | 48×12 per type string `STYPE12X48N` |

⚠ `timhodson` is untested on hardware. Protocol, key and cell encoding come from [timhodson/ble-led-badge](https://github.com/timhodson/ble-led-badge). Verified: commands, data packets and the encoding of all 150 glyph segments of its font are byte-identical with that code. Open: the offset in static mode, the direction of the speed value (1–8 is spread over 0–255), and whether the fixed pause after `DATS` can replace waiting for `DATSOK`.

## LSLED protocol

A record consists of a 64-byte header and the bitmap, padded to a multiple of 16 and written to `fee1` in 16-byte packets (with response).

| Byte | Content |
|:---|:---|
| 0–3 | `wang` |
| 5 | brightness: `0x00` 100 %, `0x10` 75 %, `0x20` 50 %, `0x40` 25 % |
| 8 | message 1: speed (0–7) in the upper, mode in the lower nibble |
| 16–17 | length of message 1 in tiles, big endian |
| 38–43 | timestamp: year (two digits), month, day, hour, minute, second |

The bitmap consists of tiles of 8 columns × 11 rows, one byte per row, most significant bit on the left.

⚠ In `static` mode the badge shows bitmap column n on display column n+2 (measured). The driver compensates (`x_shift` in `drivers/lsled.py`). Display columns 0 and 1 cannot be reached in static mode; 42 columns are usable. `up`, `down`, `animation`, `snowflake`, `picture` and `laser` show the bitmap unshifted (measured), with all 44 columns usable; wider content is cut off.

The badge leaves Bluetooth mode after receiving data; switch it back on before the next transmission.

## Credits and licenses

lsled-badge, including the hand-drawn fonts `5x9`, `3x5`, `space` and the fonts derived from them, is released under the MIT license, see [LICENSE](LICENSE).

- The `timhodson` driver is based on the protocol analysis in [timhodson/ble-led-badge](https://github.com/timhodson/ble-led-badge) by Tim Hodson: commands, AES key and cell encoding. The code here is written anew. That project declares the MIT license in its `pyproject.toml` but has no license file.
- The fonts imported from figlet's `bdffonts` keep their own licenses: X Consortium (`5x7`, `6x9`), Schumacher (`clr4x6`, `clr5x8`), Adobe/Digital (`helv`, `helvb`), public domain (`6x10`). The full copyright and license text is in the `notice` field of each font file.
