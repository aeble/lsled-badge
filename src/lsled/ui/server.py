"""Local HTTP server for the web interface: page, config, rendering and sending via local Bluetooth."""
import asyncio
import json
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from bleak.exc import BleakError

from ..app import compose
from ..core.fonts import available_fonts, load_font
from ..core.i18n import FALLBACK, LocalizedError, available_languages, load_messages, t
from ..drivers import DEFAULT_DRIVER, DRIVERS
from ..transport import ble

WEB_DIR = Path(__file__).parent.parent / "web"
# Errors whose wording differs on the web page (it names the toggle instead of the option)
WEB_KEYS = {"err.too_wide": "web.too_wide"}
SCAN_TIMEOUT = 5.0
# One Bluetooth operation at a time; requests arrive on parallel threads
BLE_LOCK = threading.Lock()


def web_config() -> dict:
    return {
        "defaultDriver": DEFAULT_DRIVER,
        "drivers": {
            name: {
                "display": {
                    "width": driver.display.width,
                    "height": driver.display.height,
                },
                "modes": list(driver.modes),
                "serviceUuid": driver.service_uuid,
                "namePrefixes": list(driver.name_prefixes),
                "notifyCharacteristics": list(driver.notify_characteristics),
            }
            for name, driver in DRIVERS.items()
        },
        "fonts": {name: load_font(name).description for name in available_fonts()},
        "messages": {language: load_messages(language) for language in available_languages()},
    }


def messages_for(request: dict) -> dict[str, str]:
    language = request.get("language")
    return load_messages(language if language in available_languages() else FALLBACK)


def prepare(request: dict):
    driver = DRIVERS[request["driver"]]
    result = compose(request["text"], request["font"], request["bold"], request["mode"], request["autoscroll"], driver)
    writes = driver.build_writes(result.canvas, result.mode, request["speed"], request["brightness"])
    return driver, result, writes


def render(request: dict) -> dict:
    try:
        _driver, result, writes = prepare(request)
    except LocalizedError as error:
        return {"error": error.translate(messages_for(request), WEB_KEYS.get(error.key))}
    return {
        "canvas": result.canvas,
        "mode": result.mode,
        "textWidth": result.text_width,
        "autoscrolled": result.autoscrolled,
        "usableWidth": result.usable_width,
        "writes": [
            {"characteristic": w.characteristic, "data": w.data.hex(), "response": w.response, "pause": w.pause}
            for w in writes
        ],
    }


def find_devices(driver: str) -> dict:
    with BLE_LOCK:
        found = asyncio.run(ble.scan(SCAN_TIMEOUT))
    return {"devices": [{"address": f.address, "name": f.name, "rssi": f.rssi} for f in found if f.driver == driver]}


def send(request: dict) -> dict:
    """Render again and send through this machine's Bluetooth, for browsers without Web Bluetooth."""
    messages = messages_for(request)
    try:
        driver, _result, writes = prepare(request)
        with BLE_LOCK:
            asyncio.run(ble.execute(request["address"], driver, writes))
    except LocalizedError as error:
        return {"error": error.translate(messages, WEB_KEYS.get(error.key))}
    except BleakError as error:
        return {"error": messages["web.send_failed"].format(error=error)}
    return {"count": len(writes)}


class WebHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def send_json(self, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/config.json":
            return self.send_json(web_config())
        if url.path == "/devices":
            return self.send_json(find_devices(parse_qs(url.query)["driver"][0]))
        return super().do_GET()

    def do_POST(self):
        handlers = {"/render": render, "/send": send}
        if self.path not in handlers:
            return self.send_error(404)
        request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        self.send_json(handlers[self.path](request))

    def log_message(self, format, *args):
        # The page renders on every keystroke; request logging would flood the terminal
        pass


def serve(port: int) -> None:
    # Web Bluetooth needs a secure context; localhost counts as secure
    server = ThreadingHTTPServer(("127.0.0.1", port), WebHandler)
    url = f"http://localhost:{port}/"
    print(t("msg.web_url", url=url))
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
