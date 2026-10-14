import json


def response(status_code: int, body: dict) -> dict:
    """Build a JSON response for a Lambda Function URL."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Cache-Control": "no-store",
        },
        "body": json.dumps(body),
    }


def handler(event, context=None):
    """Handle HTTP requests from a Lambda Function URL."""
    request_context = event.get("requestContext") or {}
    http_context = request_context.get("http") or {}

    method = http_context.get("method", "GET").upper()
    path = event.get("rawPath", "/")

    if path != "/health":
        return response(404, {"error": "Not found"})

    if method != "GET":
        return response(405, {"error": "Method not allowed"})

    return response(200, {"status": "ok"})
