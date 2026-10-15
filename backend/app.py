import json
import os
from datetime import datetime, timezone

import boto3
from botocore.exceptions import BotoCoreError, ClientError


CANVAS_KEY = {"counter_id": "shared-canvas"}
CANVAS_PIXEL_COUNT = 256
CANVAS_COLORS = range(4)
DEFAULT_PIXELS = [0] * CANVAS_PIXEL_COUNT


def response(status_code: int, body: dict) -> dict:
    """Build a JSON response for API Gateway HTTP API."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Cache-Control": "no-store",
        },
        "body": json.dumps(body),
    }


def valid_pixels(pixels) -> bool:
    """Accept exactly 256 integer palette indexes from 0 to 3."""
    return (
        isinstance(pixels, list)
        and len(pixels) == CANVAS_PIXEL_COUNT
        and all(
            type(pixel) is int and pixel in CANVAS_COLORS
            for pixel in pixels
        )
    )


def handler(event, context=None):
    """Handle visitor counter and shared canvas HTTP requests."""
    request_context = event.get("requestContext") or {}
    http_context = request_context.get("http") or {}

    method = http_context.get("method", "GET").upper()
    path = event.get("rawPath", "/")

    allowed_paths = {
        "/health",
        "/visitors",
        "/visitors/current",
        "/canvas",
    }

    if path not in allowed_paths:
        return response(404, {"error": "Not found"})

    allowed_methods = (
        {"GET", "PUT"} if path == "/canvas" else {"GET"}
    )
    if method not in allowed_methods:
        return response(405, {"error": "Method not allowed"})

    if path == "/health":
        return response(200, {"status": "ok"})

    table_name = os.environ.get("VISITOR_TABLE_NAME")
    if not table_name:
        return response(
            500,
            {"error": "Visitor counter is not configured"},
        )

    try:
        table = boto3.resource("dynamodb").Table(table_name)

        if path == "/canvas":
            if method == "GET":
                result = table.get_item(
                    Key=CANVAS_KEY,
                    ConsistentRead=True,
                )
                item = result.get("Item")

                if item is None:
                    return response(
                        200,
                        {"pixels": DEFAULT_PIXELS, "updatedAt": None},
                    )

                stored_pixels = item.get("pixels")
                try:
                    pixels = [
                        int(pixel)
                        if type(pixel) is int
                        or (
                            pixel.__class__.__name__ == "Decimal"
                            and pixel == pixel.to_integral_value()
                        )
                        else pixel
                        for pixel in stored_pixels
                    ]
                except (TypeError, ValueError):
                    pixels = None

                if not valid_pixels(pixels):
                    return response(
                        500,
                        {"error": "Stored canvas data is invalid"},
                    )

                return response(
                    200,
                    {
                        "pixels": pixels,
                        "updatedAt": item.get("updated_at"),
                    },
                )

            try:
                body = event.get("body")
                if event.get("isBase64Encoded"):
                    import base64

                    body = base64.b64decode(body or "").decode("utf-8")
                payload = json.loads(body or "")
            except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
                return response(400, {"error": "Invalid JSON body"})

            if not isinstance(payload, dict) or not valid_pixels(
                payload.get("pixels")
            ):
                return response(
                    400,
                    {
                        "error": (
                            "pixels must contain exactly 256 integers "
                            "from 0 to 3"
                        )
                    },
                )

            updated_at = datetime.now(timezone.utc).isoformat()
            table.put_item(
                Item={
                    **CANVAS_KEY,
                    "pixels": payload["pixels"],
                    "updated_at": updated_at,
                }
            )

            return response(
                200,
                {
                    "pixels": payload["pixels"],
                    "updatedAt": updated_at,
                },
            )

        if path == "/visitors/current":
            result = table.get_item(
                Key={"counter_id": "portfolio"},
                ConsistentRead=True,
            )
            item = result.get("Item", {})
            return response(
                200,
                {"visitors": int(item.get("visit_count", 0))},
            )

        result = table.update_item(
            Key={"counter_id": "portfolio"},
            UpdateExpression="ADD visit_count :increment",
            ExpressionAttributeValues={":increment": 1},
            ReturnValues="UPDATED_NEW",
        )

        return response(
            200,
            {"visitors": int(result["Attributes"]["visit_count"])},
        )

    except (BotoCoreError, ClientError):
        if path == "/canvas":
            return response(500, {"error": "Unable to access shared canvas"})
        return response(500, {"error": "Unable to update visitor counter"})
