"""Provide ecr construct tests."""
import json
import os

from troposphere import ec2, Ref

from e3.aws.troposphere import Stack
from e3.aws.troposphere.ec2 import VPC
from e3.aws.troposphere.iam.policy_statement import Allow
from e3.aws.troposphere.iam.policy_document import PolicyDocument


TEST_DIR = os.path.dirname(os.path.abspath(__file__))


def test_vpc(stack: Stack) -> None:
    """Test VPC creation."""
    ecr_endpoint_pd = PolicyDocument(
        statements=[
            Allow(
                action=[
                    "ecr:BatchGetImage",
                    "ecr:GetAuthorizationToken",
                    "ecr:GetDownloadUrlForLayer",
                ],
                resource="*",
                principal="*",
            )
        ]
    )
    s3_endpoint_pd = PolicyDocument(
        statements=[
            Allow(action=["s3:PutObject", "s3:GetObject"], resource="*", principal="*"),
            Allow(action="s3:ListBucket", resource="*", principal="*"),
        ]
    )
    cloudwatch_endpoint_pd = PolicyDocument(
        statements=[
            Allow(
                action=[
                    "logs:CreateLogStream",
                    "logs:CreateLogGroup",
                    "logs:PutLogEvents",
                ],
                resource="*",
                principal="*",
            )
        ]
    )
    sm_endpoint_pd = PolicyDocument(
        statements=[
            Allow(
                action=[
                    "secretsmanager:GetResourcePolicy",
                    "secretsmanager:GetSecretValue",
                    "secretsmanager:DescribeSecret",
                    "secretsmanager:ListSecretVersionIds",
                ],
                resource=["this_is_a_secret_arn"],
                principal="*",
            )
        ]
    )
    vpc = VPC(
        name="TestVPC",
        region="eu-west-1",
        nat_gateway=True,
        s3_endpoint_policy_document=s3_endpoint_pd,
        interface_endpoints=[
            ("logs", cloudwatch_endpoint_pd),
            ("ecr.api", ecr_endpoint_pd),
            ("ecr.dkr", ecr_endpoint_pd),
            ("sts", None),
            ("secretsmanager", sm_endpoint_pd),
        ],
    )
    stack.add(vpc)

    # Add a security group with access to VPC endpoints
    group_name = "SGWithVPCEndpointsAccess"
    sg = ec2.SecurityGroup(
        group_name,
        GroupDescription="Security group for some privileged runners that need "
        "outbound to the world",
        GroupName=group_name,
        SecurityGroupEgress=vpc.egress_to_vpc_endpoints,
        VpcId=Ref(vpc.vpc),
    )
    stack.add(sg)

    with open(os.path.join(TEST_DIR, "vpc.json")) as fd:
        expected_template = json.load(fd)

    assert stack.export()["Resources"] == expected_template


def test_vpc_with_ses_endpoint(stack: Stack) -> None:
    """Test creation of a VPC with an SES endpoint."""
    vpc = VPC(
        name="TestVPC",
        region="eu-west-1",
        nat_gateway=False,
        interface_endpoints=[
            ("email-smtp", None),
        ],
    )
    stack.add(vpc)

    with open(os.path.join(TEST_DIR, "vpc_ses_endpoint.json")) as fd:
        expected_template = json.load(fd)

    assert stack.export()["Resources"] == expected_template


def test_vpc_with_ses_and_other_endpoints(stack: Stack) -> None:
    """Test creation of a VPC with an SES endpoint and other endpoints."""
    vpc = VPC(
        name="TestVPC",
        region="eu-west-1",
        nat_gateway=False,
        interface_endpoints=[
            ("email-smtp", None),
            ("logs", None),
            ("sts", None),
        ],
    )
    stack.add(vpc)

    with open(os.path.join(TEST_DIR, "vpc_ses_and_other_endpoints.json")) as fd:
        expected_template = json.load(fd)

    assert stack.export()["Resources"] == expected_template
