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


def test_visitors_endpoint_increments_counter(monkeypatch):
    class FakeTable:
        def update_item(self, **kwargs):
            assert kwargs["Key"] == {"counter_id": "portfolio"}
            assert kwargs["ReturnValues"] == "UPDATED_NEW"
            return {"Attributes": {"visit_count": 12}}

    class FakeDynamoDB:
        def Table(self, table_name):
            assert table_name == "test-visitor-table"
            return FakeTable()

    monkeypatch.setenv("VISITOR_TABLE_NAME", "test-visitor-table")

    import boto3

    monkeypatch.setattr(
        boto3,
        "resource",
        lambda service_name: FakeDynamoDB(),
    )

    result = handler(make_event(path="/visitors"))

    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"visitors": 12}


def test_visitors_endpoint_requires_configuration(monkeypatch):
    monkeypatch.delenv("VISITOR_TABLE_NAME", raising=False)

    result = handler(make_event(path="/visitors"))

    assert result["statusCode"] == 500
    assert json.loads(result["body"]) == {
        "error": "Visitor counter is not configured"
    }


def test_visitors_endpoint_handles_dynamodb_error(monkeypatch):
    import boto3
    from botocore.exceptions import ClientError

    class FakeTable:
        def update_item(self, **kwargs):
            raise ClientError(
                {
                    "Error": {
                        "Code": "InternalServerError",
                        "Message": "Simulated failure",
                    }
                },
                "UpdateItem",
            )

    class FakeDynamoDB:
        def Table(self, table_name):
            return FakeTable()

    monkeypatch.setenv("VISITOR_TABLE_NAME", "test-visitor-table")
    monkeypatch.setattr(
        boto3,
        "resource",
        lambda service_name: FakeDynamoDB(),
    )

    result = handler(make_event(path="/visitors"))

    assert result["statusCode"] == 500
    assert json.loads(result["body"]) == {
        "error": "Unable to update visitor counter"
    }