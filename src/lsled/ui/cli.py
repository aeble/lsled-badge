"""Command line: lsled scan | fonts | import-figlet | preview | send | web."""
import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

from ..app import compose, scan, transport
from ..core.figlet import convert_flf
from ..core.fonts import FONT_DIR, available_fonts, load_font
from ..core.i18n import LocalizedError, t
from ..drivers import ALL_MODES, DEFAULT_DRIVER, DRIVERS
from ..transport import usb
from . import server
from .preview import format_preview

# The tallest display any driver supports limits imported fonts
MAX_FONT_HEIGHT = max(driver.display.height for driver in DRIVERS.values())


def add_render_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("text", help=t("opt.text"))
    parser.add_argument("-d", "--driver", choices=DRIVERS, default=DEFAULT_DRIVER, help=t("opt.driver"))
    parser.add_argument("-f", "--font", default="5x9", help=t("opt.font"))
    parser.add_argument("--bold", action="store_true", help=t("opt.bold"))
    parser.add_argument("-m", "--mode", choices=ALL_MODES, default="static", help=t("opt.mode"))
    overflow = parser.add_mutually_exclusive_group()
    overflow.add_argument("--autoscroll", action="store_true", help=t("opt.autoscroll"))
    overflow.add_argument("--pages", action="store_true", help=t("opt.pages"))


def build_parser() -> argparse.ArgumentParser:
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
    send_parser.add_argument("-a", "--address", help=t("opt.address"))
    send_parser.add_argument(
        "-b", "--brightness", type=int, choices=range(1, 101), default=25, metavar="1-100", help=t("opt.brightness")
    )
    send_parser.add_argument(
        "-s", "--speed", type=int, choices=range(1, 9), default=5, metavar="1-8", help=t("opt.speed")
    )

    web_parser = commands.add_parser("web", help=t("cmd.web"))
    web_parser.add_argument("-p", "--port", type=int, default=8044, help=t("opt.port"))
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.command == "scan":
            found = asyncio.run(scan(args.timeout))
            if not found:
                print(t("msg.no_badge"))
            for badge in found:
                signal = "USB" if badge.rssi is None else f"RSSI {badge.rssi}"
                print(f"{badge.address}  {badge.name}  {signal}  [{badge.driver}]")
        elif args.command == "fonts":
            names = available_fonts()
            width = max(map(len, names))
            for name in names:
                print(f"{name:{width}}  {load_font(name).description}")
        elif args.command == "import-figlet":
            name = args.name or args.file.stem
            font = convert_flf(args.file, MAX_FONT_HEIGHT)
            target = FONT_DIR / f"{name}.json"
            target.write_text(json.dumps(font, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            print(t("msg.imported", name=name, glyphs=len(font["glyphs"]), height=font["height"], path=target))
        elif args.command == "web":
            server.serve(args.port)
        else:
            driver = DRIVERS[args.driver]
            overflow = "scroll" if args.autoscroll else "pages" if args.pages else "error"
            result = compose(args.text, args.font, args.bold, args.mode, overflow, driver)
            if result.autoscrolled:
                print(t("msg.autoscroll"))
            if len(result.pages) > 1:
                print(t("msg.paged", count=len(result.pages)))
            print("\n".join(format_preview(canvas) for canvas in result.pages))
            if args.command == "send":
                address = args.address
                # LSLED_ADDR holds a Bluetooth address; without --address USB takes the first badge
                if driver.transport == "usb":
                    address = address or asyncio.run(usb.first_address(driver))
                else:
                    address = address or os.environ.get("LSLED_ADDR")
                if not address:
                    parser.error(t("err.no_address"))
                writes = driver.build_writes(result.pages, result.mode, args.speed, args.brightness)
                asyncio.run(transport(driver).execute(address, driver, writes))
                print(t("msg.sent", count=len(writes), address=address))
    except LocalizedError as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
