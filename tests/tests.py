import http.client
import importlib
import sys
import pytest
from sdembeddingssync.cli import main
from sdembeddingssync.sdsync import RepoStatus, SettingsManager, RepoFileManager, RepoManager
from sdembeddingssync.httpnano import http_get


class HTTPMockResponse:
    def __init__(self, status, data=None):
        self.status = status
        self.reason = "mock reason"
        self.data = data

    def read(self):
        return self.data


class MockHTTPSConnection:
    def __init__(self, host):
        self.host = host
        self.response = None

    def request(self, method, path_and_query):
        assert self.response is None
        target = f"{method} https://{self.host}{path_and_query}"
        if target == "GET https://localhost/mock/200":
            self.response = HTTPMockResponse(200, b"mock123")
        elif target == "GET https://localhost/mock/400":
            self.response = HTTPMockResponse(400)
        # elif target == "GET https://localhost/mock/pickle/benign":
        #    self.response = HTTPResponse(200, pickle.dumps({"a": 0, "b": 1, "c": 2}))
        # elif target == "GET https://localhost/mock/pickle/malicious":
        #    self.response = HTTPResponse(200, pickle.dumps(Malicious2()))
        # elif target == "GET https://localhost/mock/zip/benign":
        #    buffer = io.BytesIO()
        #    with zipfile.ZipFile(buffer, "w") as zip:
        #        zip.writestr("data.pkl", pickle.dumps({"a": 0, "b": 1, "c": 2}))
        #    self.response = HTTPResponse(200, buffer.getbuffer())
        # elif target == "GET https://localhost/mock/zip/malicious":
        #    buffer = io.BytesIO()
        #    with zipfile.ZipFile(buffer, "w") as zip:
        #        zip.writestr("data.pkl", pickle.dumps(Malicious1()))
        #    self.response = HTTPResponse(200, buffer.getbuffer())
        # elif (
        #    target
        #    == "GET https://huggingface.co/api/models/ykilcher/totally-harmless-model"
        # ):
        #    self.response = HTTPResponse(
        #        200, b'{"siblings": [{"rfilename": "pytorch_model.bin"}]}'
        #    )
        # elif (
        #    target
        #    == "GET https://huggingface.co/ykilcher/totally-harmless-model/resolve/main/#pytorch_model.bin"
        # ):
        #    buffer = io.BytesIO()
        #    with zipfile.ZipFile(buffer, "w") as zip:
        #        zip.writestr("archive/data.pkl", pickle.dumps(Malicious1()))
        #    self.response = HTTPResponse(200, buffer.getbuffer())
        else:
            raise ValueError(f"No mock for request '{target}'")

    def getresponse(self):
        response = self.response
        self.response = None
        return response

    def close(self):
        pass


http.client.HTTPSConnection = MockHTTPSConnection


def test_http_get():
    assert http_get("https://localhost/mock/200", raise_error=True) == b"mock123"

    with pytest.raises(RuntimeError):
        http_get("https://localhost/mock/400")


def test_SettingsManager_instanced():
    assert SettingsManager() is not None


def test_RepoFileManager_instanced():
    assert RepoFileManager() is not None


def test_RepoManager_instanced():
    assert RepoManager() is not None


def test_RepoStatus_instanced():
    assert RepoStatus() is not None


def test_main_helpScreen():
    argv = sys.argv
    try:
        sys.argv = ["sdembeddingsync", "--help"]
        assert main() == 0
        importlib.import_module("picklescan.__main__")
    finally:
        sys.argv = argv


def test_main_defaultArgs():
    argv = sys.argv
    try:
        sys.argv = ["sdembeddingsync"]
        assert main() == 0
        importlib.import_module("picklescan.__main__")
    finally:
        sys.argv = argv
