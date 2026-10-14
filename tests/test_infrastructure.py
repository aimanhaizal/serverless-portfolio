import aws_cdk as cdk
from aws_cdk.assertions import Template

from infrastructure.stack import PortfolioStack


def test_stack_defines_lambda_and_function_url():
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
    template.resource_count_is("AWS::Lambda::Url", 1)

    template.has_resource_properties(
        "AWS::Lambda::Function",
        {
            "Runtime": "python3.10",
            "Handler": "app.handler",
            "MemorySize": 128,
        },
    )
