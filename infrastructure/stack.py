from pathlib import Path

from aws_cdk import (
    CfnOutput,
    Duration,
    Stack,
    aws_lambda as lambda_,
)
from aws_cdk import aws_lambda as lambda_service
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

        api_function = lambda_service.Function(
            self,
            "PortfolioApiFunction",
            runtime=lambda_.Runtime.PYTHON_3_10,
            handler="app.handler",
            code=lambda_.Code.from_asset(str(backend_path)),
            description="Serverless portfolio HTTP handler",
            memory_size=128,
            timeout=Duration.seconds(5),
        )

        function_url = api_function.add_function_url(
            auth_type=lambda_.FunctionUrlAuthType.NONE,
            cors=lambda_.FunctionUrlCorsOptions(
                allowed_origins=["http://localhost:8000"],
                allowed_methods=[lambda_.HttpMethod.GET],
                allowed_headers=["content-type"],
                max_age=Duration.minutes(10),
            ),
        )

        CfnOutput(
            self,
            "PortfolioFunctionUrl",
            value=function_url.url,
            description="Public HTTPS endpoint for the portfolio API",
        )
