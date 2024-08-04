import argparse
import dataclasses
import http.server
import json
import time
import typing


@dataclasses.dataclass
class ResponseConfig:
    status: int
    headers: dict[str, str] = dataclasses.field(default_factory=dict)
    body: dict[str, typing.Any] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class RouteConfig:
    url: str
    method: str
    response: ResponseConfig
    delay: int = 0


@dataclasses.dataclass
class Config:
    routes: list[RouteConfig]


class MockHandler(http.server.BaseHTTPRequestHandler):
    mock_server_config: Config

    def do_request(self) -> None:
        found = False
        for route in self.mock_server_config.routes:
            if self.path == route.url and self.command == route.method:
                found = True
                delay = route.delay / 1000.0
                time.sleep(delay)
                expected_response = route.response
                self.send_response(expected_response.status)
                for header, value in expected_response.headers.items():
                    self.send_header(header, value)
                self.end_headers()
                if expected_response.body:
                    self.wfile.write(json.dumps(expected_response.body).encode())
                    return
        if not found:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'{"error": "Not found"}')

    def do_GET(self) -> None:
        self.do_request()

    def do_POST(self) -> None:
        self.do_request()

    def do_PUT(self) -> None:
        self.do_request()

    def do_DELETE(self) -> None:
        self.do_request()


class MockServer:
    def __init__(self, config: Config, port: int = 8080):
        self.config = config
        self.port = port

    def start(self) -> None:
        MockHandler.mock_server_config = self.config
        self.server = http.server.HTTPServer(('', self.port), MockHandler)
        print(f'Starting server on port {self.port}')
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self.shutdown()

    def shutdown(self):
        if self.server:
            print("Shutting down server...")
            self.server.shutdown()
            self.server.server_close()


def load_config(config_path: str) -> Config:
    config_data = None
    with open(config_path, 'r') as f:
        config_data = json.load(f)
    routes = [RouteConfig(url=route_data['url'], method=route_data['method'], response=ResponseConfig(**route_data['response']), delay=route_data.get('delay', 0)) for route_data in config_data]
    return Config(routes=routes)


def main() -> None:
    parser = argparse.ArgumentParser(description='Run a mock API server.')
    parser.add_argument('--config', type=str, required=True, help='Path to the JSON config file.')
    parser.add_argument('--port', type=int, default=8080, help='Port number to run the server on.')
    args = parser.parse_args()

    config = load_config(args.config)
    server = MockServer(config, port=args.port)
    server.start()


if __name__ == '__main__':
    main()
