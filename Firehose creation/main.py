import boto3
import random
import string
import json
import time

#set variables
region = 'us-east-1'
boto3.setup_default_session(profile_name='sso_Treasury')
randomstring = ''.join(random.choices(string.ascii_lowercase, k=5))

#check if NewRelic Role is created or not
IAM_client = boto3.client('iam')

try:
    NRIAMRole_response = IAM_client.get_role(
    RoleName='NewRelicInfrastructure-Integrations'
)
except:
    Assume_Role_Policy = {
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Effect" : "Allow",
        "Principal" : {
          "AWS" : "arn:aws:iam::754728514883:root"
        },
        "Action" : "sts:AssumeRole",
        "Condition" : {
          "StringEquals" : {
            "sts:ExternalId" : "1647222"
          }
        }
      }
    ]
  }
    Policy_Json = {
      "Version" : "2012-10-17",
      "Statement" : [
        {
          "Action" : [
            "budgets:ViewBudget"
          ],
          "Effect" : "Allow",
          "Resource" : "*"
        }
      ]
    }
    IAM_PolicyForNR = IAM_client.create_policy(
    PolicyName = 'NewRelicBudget',
    PolicyDocument = json.dumps(Policy_Json)
    )
    NRIAMRole_response = IAM_client.create_role(
        RoleName = 'NewRelicInfrastructure-Integrations',
        AssumeRolePolicyDocument = json.dumps(Assume_Role_Policy)
        )
    Attach_ReadOnlyAcces = IAM_client.attach_role_policy(
        RoleName = 'NewRelicInfrastructure-Integrations',
        PolicyArn = 'arn:aws:iam::aws:policy/ReadOnlyAccess'
    )
    Attach_NRbudgetPolicy = IAM_client.attach_role_policy(
        RoleName = 'NewRelicInfrastructure-Integrations',
        PolicyArn = IAM_PolicyForNR['Policy']['Arn']
        )


#create s3 bucket
if region == 'us-east-1':
    s3_client = boto3.client('s3')
    s3_response = s3_client.create_bucket(
    ACL = 'private',
    Bucket ='firehose-backup-' + randomstring,
    )
else:
    s3_client = boto3.client('s3')
    s3_response = s3_client.create_bucket(
        ACL = 'private',
        Bucket ='firehose-backup-' + randomstring,
        CreateBucketConfiguration={
            'LocationConstraint': f'{region}'
        },
    )

#create IAM roles and policies
AssumeRolePolicy = {
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "firehose.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
  }

IAMRole_response = IAM_client.create_role(
    RoleName = 'firehose_s3_access_role_' + randomstring,
    AssumeRolePolicyDocument = json.dumps(AssumeRolePolicy)
)

#create IAM policy
IAMPolicy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:AbortMultipartUpload",
                "s3:GetBucketLocation",
                "s3:GetObject",
                "s3:ListBucket",
                "s3:ListBucketMultipartUploads",
                "s3:PutObject"
            ],
            "Resource": [
                "arn:aws:s3:::firehose-backup-" + randomstring,
                "arn:aws:s3:::firehose-backup-" + randomstring + "/*"
            ]
        }
    ]
}

IAMPolicy_response = IAM_client.create_policy(
    PolicyName = 'firehose_s3_access_policy_' + randomstring,
    PolicyDocument = json.dumps(IAMPolicy)
)

IAMRoleAttachresponse = IAM_client.attach_role_policy(
    RoleName='firehose_s3_access_role_' + randomstring,
    PolicyArn = IAMPolicy_response['Policy']['Arn']
)


time.sleep(10)

#firehose creation
client = boto3.client('firehose', region_name = region)
response = client.create_delivery_stream(
    DeliveryStreamName='NewRelic-Delivery-Stream-' + region,
    DeliveryStreamType='DirectPut',
    HttpEndpointDestinationConfiguration={
            'EndpointConfiguration': {
            'Url': 'https://aws-api.newrelic.com/cloudwatch-metrics/v1',
            'Name': 'New Relic',
            'AccessKey': 'b1a808a19fa62e51c15a5f01457e40dcb96311b8'
        },
        'BufferingHints': {
            'SizeInMBs': 1,
            'IntervalInSeconds': 60
        },
        'RequestConfiguration': {
            'ContentEncoding': 'GZIP',
        },
        'S3BackupMode': 'FailedDataOnly',
        'S3Configuration': {
            'RoleARN': IAMRole_response['Role']['Arn'],
            'BucketARN': 'arn:aws:s3:::firehose-backup-' + randomstring,
            'ErrorOutputPrefix': 'string',
            'BufferingHints': {
                'SizeInMBs': 5,
                'IntervalInSeconds': 300
            },
            'CompressionFormat': 'GZIP',
            'EncryptionConfiguration': {
                'NoEncryptionConfig': 'NoEncryption',
            },
        }
    }
)
