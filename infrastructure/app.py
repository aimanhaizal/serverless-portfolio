#!/usr/bin/env python3

import aws_cdk as cdk

from stack import PortfolioStack

app = cdk.App()

PortfolioStack(
    app,
    "ServerlessPortfolioStack",
    env=cdk.Environment(
        account=app.node.try_get_context("account"),
        region=app.node.try_get_context("region") or "ap-southeast-1",
    ),
)

app.synth()
