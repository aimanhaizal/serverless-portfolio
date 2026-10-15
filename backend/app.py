import json
import os

import boto3
from botocore.exceptions import BotoCoreError, ClientError


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

    if path not in ("/health", "/visitors", "/visitors/current"):
        return response(404, {"error": "Not found"})

    if method != "GET":
        return response(405, {"error": "Method not allowed"})

    if path == "/health":
        return response(200, {"status": "ok"})

    table_name = os.environ.get("VISITOR_TABLE_NAME")
    if not table_name:
        return response(500, {"error": "Visitor counter is not configured"})

    try:
        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table(table_name)

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
        return response(500, {"error": "Unable to update visitor counter"})
