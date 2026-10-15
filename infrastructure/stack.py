from pathlib import Path

from aws_cdk import (
    CfnOutput,
    Duration,
    RemovalPolicy,
    Stack,
    aws_apigatewayv2 as apigatewayv2,
    aws_apigatewayv2_integrations as integrations,
    aws_dynamodb as dynamodb,
    aws_lambda as lambda_,
)
from constructs import Construct


class PortfolioStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        backend_path = Path(__file__).resolve().parent.parent / "backend"

        visitor_table = dynamodb.Table(
            self,
            "VisitorCounterTable",
            partition_key=dynamodb.Attribute(
                name="counter_id",
                type=dynamodb.AttributeType.STRING,
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
        )

        api_function = lambda_.Function(
            self,
            "PortfolioApiFunction",
            # runtime=lambda_.Runtime.PYTHON_3_10,
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="app.handler",
            code=lambda_.Code.from_asset(str(backend_path)),
            description="Serverless portfolio HTTP handler",
            memory_size=128,
            timeout=Duration.seconds(5),
            environment={
                "VISITOR_TABLE_NAME": visitor_table.table_name,
            },
        )

        # Grant the Lambda access to the visitor counter table.
        visitor_table.grant_read_write_data(api_function)

        # Public HTTP API with browser CORS restricted to known origins.
        http_api = apigatewayv2.HttpApi(
            self,
            "PortfolioHttpApi",
            api_name="serverless-portfolio-api",
            description="HTTP API for the serverless portfolio",
            cors_preflight=apigatewayv2.CorsPreflightOptions(
                allow_origins=[
                    "https://aimanhaizal.github.io",
                    "http://localhost:8000",
                ],
                allow_methods=[
                    apigatewayv2.CorsHttpMethod.GET,
                    apigatewayv2.CorsHttpMethod.PUT,
                ],
                allow_headers=["content-type"],
                max_age=Duration.minutes(10),
            ),
        )

        lambda_integration = integrations.HttpLambdaIntegration(
            "PortfolioLambdaIntegration",
            api_function,
        )

        http_api.add_routes(
            path="/health",
            methods=[apigatewayv2.HttpMethod.GET],
            integration=lambda_integration,
        )

        http_api.add_routes(
            path="/visitors",
            methods=[apigatewayv2.HttpMethod.GET],
            integration=lambda_integration,
        )

        http_api.add_routes(
            path="/visitors/current",
            methods=[apigatewayv2.HttpMethod.GET],
            integration=lambda_integration,
        )

        http_api.add_routes(
            path="/canvas",
            methods=[
                apigatewayv2.HttpMethod.GET,
                apigatewayv2.HttpMethod.PUT,
            ],
            integration=lambda_integration,
        )

        CfnOutput(
            self,
            "PortfolioApiUrl",
            value=http_api.api_endpoint,
            description="Base HTTPS endpoint for the portfolio HTTP API",
        )
