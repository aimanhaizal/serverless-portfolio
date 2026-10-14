import json

from backend.app import handler


def make_event(method="GET", path="/health"):
    return {
        "rawPath": path,
        "requestContext": {
            "http": {
                "method": method,
            }
        },
    }


def test_health_endpoint_returns_ok():
    result = handler(make_event())

    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"status": "ok"}


def test_unknown_path_returns_not_found():
    result = handler(make_event(path="/unknown"))

    assert result["statusCode"] == 404
    assert json.loads(result["body"]) == {"error": "Not found"}


def test_health_endpoint_rejects_post():
    result = handler(make_event(method="POST"))

    assert result["statusCode"] == 404
