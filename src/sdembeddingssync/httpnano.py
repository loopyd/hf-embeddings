import http.client
import logging
import urllib.parse
from pydantic import dataclasses

_log = logging.getLogger("sdembeddingssync")


@dataclasses.dataclass
class HTTPResponse:
    status: int = 0
    reason: str = ""
    headers: http.client.HTTPMessage = http.client.HTTPMessage()
    content: bytes = bytes()


def http_get(url: str, header_only: bool = False, fail_on_error: bool = True):
    _log.debug(f"Request: GET {url}")

    parsed_url = urllib.parse.urlparse(url)
    path_and_query = parsed_url.path + (
        "?" + parsed_url.query if len(parsed_url.query) > 0 else ""
    )

    conn = http.client.HTTPSConnection(parsed_url.netloc)
    try:
        conn.request("GET", path_and_query)
        response = conn.getresponse()
        _log.debug(f"Response: status code {response.status} reason {response.reason}")
        if response.status == 302:
            return http_get(response.headers["Location"])
        elif response.status >= 400:
            message = f"HTTP {response.status} ({response.reason}) calling GET {parsed_url.scheme}://{parsed_url.netloc}{path_and_query}"
            if fail_on_error is True:
                raise RuntimeError(message)
            else:
                _log.error(message)
        if header_only is False:
            return HTTPResponse(
                status=response.status,
                reason=response.reason,
                headers=response.headers,
                content=response.read()
            )
        else:
            return HTTPResponse(
                status=response.status,
                reason=response.reason,
                headers=response.headers
            )
    finally:
        conn.close()
