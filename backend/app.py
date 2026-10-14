import json


def response(status_code: int, body: dict) -> dict:
    """Build a JSON response suitable for a Lambda Function URL."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
        },
        "body": json.dumps(body),
    }


def handler(event, context=None):
    """Handle requests from a Lambda Function URL."""
    request_context = event.get("requestContext", {})
    http_context = request_context.get("http", {})

    method = http_context.get("method", "GET")
    path = event.get("rawPath", "/")

    if method == "GET" and path == "/health":
        return response(200, {"status": "ok"})

    return response(404, {"error": "Not found"})
