import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from infrastructure.stack import PortfolioStack


def test_stack_defines_http_api_lambda_and_visitor_table():
    app = cdk.App()
    stack = PortfolioStack(
        app,
        "TestPortfolioStack",
        env=cdk.Environment(
            account="123456789012",
            region="ap-southeast-1",
        ),
    )

    template = Template.from_stack(stack)

    template.resource_count_is("AWS::Lambda::Function", 1)
    template.resource_count_is("AWS::ApiGatewayV2::Api", 1)
    template.resource_count_is("AWS::ApiGatewayV2::Integration", 1)
    template.resource_count_is("AWS::ApiGatewayV2::Route", 3)
    template.resource_count_is("AWS::Lambda::Url", 0)
    template.resource_count_is("AWS::DynamoDB::Table", 1)

    template.has_resource_properties(
        "AWS::Lambda::Function",
        {
            "Runtime": "python3.12",
            "Handler": "app.handler",
            "MemorySize": 128,
            "Timeout": 5,
        },
    )

    template.has_resource_properties(
        "AWS::ApiGatewayV2::Api",
        {
            "Name": "serverless-portfolio-api",
            "ProtocolType": "HTTP",
            "CorsConfiguration": {
                "AllowOrigins": [
                    "https://aimanhaizal.github.io",
                    "http://localhost:8000",
                ],
                "AllowMethods": ["GET"],
                "AllowHeaders": ["content-type"],
                "MaxAge": 600,
            },
        },
    )

    template.has_resource_properties(
        "AWS::ApiGatewayV2::Integration",
        {
            "IntegrationType": "AWS_PROXY",
            "PayloadFormatVersion": "2.0",
        },
    )

    template.has_resource_properties(
        "AWS::ApiGatewayV2::Route",
        {
            "RouteKey": "GET /health",
        },
    )

    template.has_resource_properties(
        "AWS::ApiGatewayV2::Route",
        {
            "RouteKey": "GET /visitors",
        },
    )

    template.has_resource_properties(
        "AWS::ApiGatewayV2::Route",
        {
            "RouteKey": "GET /visitors/current",
        },
    )

    template.has_resource_properties(
        "AWS::DynamoDB::Table",
        {
            "BillingMode": "PAY_PER_REQUEST",
            "KeySchema": [
                {
                    "AttributeName": "counter_id",
                    "KeyType": "HASH",
                }
            ],
        },
    )
