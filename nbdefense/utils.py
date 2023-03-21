import logging
import os
import re
import socketserver
import threading
import time
import webbrowser
from datetime import datetime
from http.server import SimpleHTTPRequestHandler
from pathlib import Path
from typing import Any, Optional

import click

logger = logging.getLogger(__name__)


def serve_report_and_launch_url(report: str) -> None:
    """
    Create a HTTP server at a random port that servers the html passed as string

    :param report: The string that will be send back as response

    :return: TCPServer that can be launched with serve_forever()
    """
    encoded_report = report.encode("utf-8")

    class SimpleHTTPReportServer(SimpleHTTPRequestHandler):
        def do_GET(self) -> None:
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()

            self.wfile.write(encoded_report)

    handler = SimpleHTTPReportServer
    server = socketserver.TCPServer(("localhost", 0), handler)
    port = server.server_address[1]
    url = f"http://127.0.0.1:{port}/"
    click.echo(f"Report can be viewed at {url}")

    def start_server(server: Any) -> None:
        with server:
            server.serve_forever()

    server_thread = threading.Thread(target=start_server, args=(server,))
    server_thread.setDaemon(True)
    server_thread.start()

    webbrowser.open_new(url)

    should_run = True

    while should_run:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            should_run = False


def write_output_file(report: str, output_format: str, output_file: str) -> Path:
    if output_file:
        output_file_path = Path(output_file)
        if output_file_path.parent and not output_file_path.parent.exists():
            os.makedirs(output_file_path.parent, exist_ok=True)
    else:
        # Pick file extension
        output_extension = None
        if output_format == "html":
            output_extension = ".html"
        elif output_format == "json":
            output_extension = ".json"
        else:
            raise NotImplementedError

        # Create file path
        now = datetime.now()
        date_time_str = now.strftime("%m%d-%H%M")
        file_name = "nbdefense" + date_time_str + output_extension
        output_file_path = Path(os.getcwd()) / file_name

    with open(output_file_path, "w", encoding="utf-8") as f:
        click.echo(report, file=f)

    return output_file_path


def scrub_html(code_snippet: Optional[str]) -> str:
    if code_snippet:
        allowed_html_tags = ["table", "thead", "tbody", "tr", "th", "td"]

        new_code_snippet = code_snippet
        new_code_snippet = re.sub("<", "&lt;", new_code_snippet)
        new_code_snippet = re.sub(">", "&gt;", new_code_snippet)

        for allowed_html_tag in allowed_html_tags:
            # Tags without style information converted back to html tags
            new_code_snippet = re.sub(
                f"&lt;{allowed_html_tag}&gt;", f"<{allowed_html_tag}>", new_code_snippet
            )
            # Tags with style information converted back to html tags
            new_code_snippet = re.sub(
                f"&lt;{allowed_html_tag}(.*)&gt;",
                f"<{allowed_html_tag}\g<1>>",
                new_code_snippet,
            )
            new_code_snippet = re.sub(
                f"&lt;/{allowed_html_tag}&gt;",
                f"</{allowed_html_tag}>",
                new_code_snippet,
            )

        return new_code_snippet
    else:
        return ""
