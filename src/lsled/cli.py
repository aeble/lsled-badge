"""Command line: lsled scan | fonts | import-figlet | preview | send | web."""
import argparse
import asyncio
import json
import os
import sys
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from bleak import BleakClient, BleakScanner

from . import protocol
from .figlet import convert_flf
from .fonts import FONT_DIR, available_fonts, load_font, read_font_file, render_text
from .i18n import available_languages, load_messages, t

WEB_DIR = Path(__file__).parent / "web"


def build_canvas(args) -> tuple[list[list[int]], str]:
    """Return the pixel canvas and the mode actually used."""
    text_rows = render_text(args.text, load_font(args.font), args.bold)
    mode = args.mode
    if args.autoscroll and mode == "static" and not protocol.fits_static(len(text_rows[0])):
        mode = "left"
        print(t("msg.autoscroll"))
    return protocol.layout(text_rows, mode), mode


async def scan(timeout: float) -> None:
    devices = await BleakScanner.discover(timeout=timeout, return_adv=True)
    badges = [
        (device, adv)
        for device, adv in devices.values()
        if (device.name or adv.local_name or "").upper().startswith("LSLED")
        or protocol.SERVICE_UUID in adv.service_uuids
    ]
    if not badges:
        print(t("msg.no_badge"))
        return
    for device, adv in badges:
        print(f"{device.address}  {device.name or adv.local_name}  RSSI {adv.rssi}")


async def send(address: str, packets: list[bytes]) -> None:
    async with BleakClient(address, timeout=20) as client:
        for packet in packets:
            await client.write_gatt_char(protocol.CHAR_UUID, packet, response=True)


def web_config() -> dict:
    return {
        "display": {
            "width": protocol.DISPLAY_WIDTH,
            "height": protocol.DISPLAY_HEIGHT,
            "staticXShift": protocol.STATIC_X_SHIFT,
        },
        "serviceUuid": protocol.SERVICE_UUID,
        "charUuid": protocol.CHAR_UUID,
        "modes": protocol.MODES,
        "brightness": protocol.BRIGHTNESS,
        "fonts": {name: read_font_file(name) for name in available_fonts()},
        "messages": {language: load_messages(language) for language in available_languages()},
    }


class WebHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def do_GET(self):
        if self.path != "/config.json":
            return super().do_GET()
        body = json.dumps(web_config()).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def serve_web(port: int) -> None:
    # Web Bluetooth needs a secure context; localhost counts as secure
    server = ThreadingHTTPServer(("127.0.0.1", port), WebHandler)
    url = f"http://localhost:{port}/"
    print(t("msg.web_url", url=url))
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


def add_render_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("text", help=t("opt.text"))
    parser.add_argument("-f", "--font", default="5x9", help=t("opt.font"))
    parser.add_argument("--bold", action="store_true", help=t("opt.bold"))
    parser.add_argument("-m", "--mode", choices=protocol.MODES, default="static", help=t("opt.mode"))
    parser.add_argument("--autoscroll", action="store_true", help=t("opt.autoscroll"))


def main() -> int:
    parser = argparse.ArgumentParser(prog="lsled", description=t("cli.description"))
    commands = parser.add_subparsers(dest="command", required=True)

    scan_parser = commands.add_parser("scan", help=t("cmd.scan"))
    scan_parser.add_argument("-t", "--timeout", type=float, default=10.0, help=t("opt.timeout"))

    commands.add_parser("fonts", help=t("cmd.fonts"))

    import_parser = commands.add_parser("import-figlet", help=t("cmd.import_figlet"))
    import_parser.add_argument("file", type=Path, help=t("opt.file"))
    import_parser.add_argument("-n", "--name", help=t("opt.name"))

    preview_parser = commands.add_parser("preview", help=t("cmd.preview"))
    add_render_options(preview_parser)

    send_parser = commands.add_parser("send", help=t("cmd.send"))
    add_render_options(send_parser)
    send_parser.add_argument(
        "-a", "--address", default=os.environ.get("LSLED_ADDR"), help=t("opt.address")
    )
    send_parser.add_argument("-b", "--brightness", type=int, choices=protocol.BRIGHTNESS, default=25, help=t("opt.brightness"))
    send_parser.add_argument("-s", "--speed", type=int, choices=protocol.SPEEDS, default=5, help=t("opt.speed"))

    web_parser = commands.add_parser("web", help=t("cmd.web"))
    web_parser.add_argument("-p", "--port", type=int, default=8044, help=t("opt.port"))

    args = parser.parse_args()

    if args.command == "scan":
        asyncio.run(scan(args.timeout))
    elif args.command == "fonts":
        names = available_fonts()
        width = max(map(len, names))
        for name in names:
            print(f"{name:{width}}  {load_font(name).description}")
    elif args.command == "import-figlet":
        name = args.name or args.file.stem
        try:
            font = convert_flf(args.file, protocol.DISPLAY_HEIGHT)
        except ValueError as error:
            print(error, file=sys.stderr)
            return 1
        target = FONT_DIR / f"{name}.json"
        target.write_text(json.dumps(font, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(t("msg.imported", name=name, glyphs=len(font["glyphs"]), height=font["height"], path=target))
    elif args.command == "web":
        serve_web(args.port)
    else:
        if not args.text:
            parser.error(t("err.empty_text"))
        try:
            canvas, mode = build_canvas(args)
        except ValueError as error:
            print(error, file=sys.stderr)
            return 1
        print(protocol.format_preview(canvas))
        if args.command == "send":
            if not args.address:
                parser.error(t("err.no_address"))
            packets = protocol.build_packets(canvas, mode, args.speed, args.brightness)
            asyncio.run(send(args.address, packets))
            print(t("msg.sent", count=len(packets), address=args.address))
    return 0


if __name__ == "__main__":
    sys.exit(main())
