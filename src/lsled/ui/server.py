"""Local HTTP server for the web interface: serves the page, the config and rendering."""
import json
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from ..app import compose
from ..core.fonts import available_fonts, load_font
from ..core.i18n import FALLBACK, LocalizedError, available_languages, load_messages, t
from ..drivers import DEFAULT_DRIVER, DRIVERS

WEB_DIR = Path(__file__).parent.parent / "web"
# Errors whose wording differs on the web page (it names the toggle instead of the option)
WEB_KEYS = {"err.too_wide": "web.too_wide"}


def web_config() -> dict:
    return {
        "defaultDriver": DEFAULT_DRIVER,
        "drivers": {
            name: {
                "display": {
                    "width": driver.display.width,
                    "height": driver.display.height,
                    "staticWidth": driver.display.static_width,
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


def render(request: dict) -> dict:
    language = request.get("language")
    messages = load_messages(language if language in available_languages() else FALLBACK)
    driver = DRIVERS[request["driver"]]
    try:
        result = compose(
            request["text"], request["font"], request["bold"], request["mode"], request["autoscroll"], driver
        )
    except LocalizedError as error:
        return {"error": error.translate(messages, WEB_KEYS.get(error.key))}
    writes = driver.build_writes(result.canvas, result.mode, request["speed"], request["brightness"])
    return {
        "canvas": result.canvas,
        "mode": result.mode,
        "textWidth": result.text_width,
        "autoscrolled": result.autoscrolled,
        "writes": [
            {"characteristic": w.characteristic, "data": w.data.hex(), "response": w.response, "pause": w.pause}
            for w in writes
        ],
    }


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
        if self.path == "/config.json":
            return self.send_json(web_config())
        return super().do_GET()

    def do_POST(self):
        if self.path != "/render":
            return self.send_error(404)
        request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        self.send_json(render(request))

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
