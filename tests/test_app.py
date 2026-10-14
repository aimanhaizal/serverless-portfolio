import json

from backend.app import handler


def make_event(method="GET", path="/health"):
    return {
        "rawPath": path,
        "requestContext": {
            "http": {"method": method},
        },
    }


def test_health_endpoint_returns_ok():
    result = handler(make_event())

    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"status": "ok"}
    assert result["headers"]["Content-Type"] == "application/json"
    assert result["headers"]["Cache-Control"] == "no-store"


def test_unknown_path_returns_not_found():
    result = handler(make_event(path="/unknown"))

    assert result["statusCode"] == 404
    assert json.loads(result["body"]) == {"error": "Not found"}


def test_health_endpoint_rejects_post():
    result = handler(make_event(method="POST"))

    assert result["statusCode"] == 405
    assert json.loads(result["body"]) == {
        "error": "Method not allowed"
    }


def test_method_is_case_insensitive():
    result = handler(make_event(method="get"))

    assert result["statusCode"] == 200


def test_missing_request_context_is_handled():
    result = handler({"rawPath": "/health"})

    assert result["statusCode"] == 200
