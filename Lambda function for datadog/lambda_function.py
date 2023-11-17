import boto3
from datadog_lambda.metric import lambda_metric

BucketName = ''
def lambda_handler(event, context):
    if(event.__contains__("Records")):
        FileName = event['Records'][0]['s3']['object']['key']
        FileSize = event['Records'][0]['s3']['object']['size']
        s3_trigger(FileName, FileSize)
    else:
        eventbridge_trigger()


def s3_trigger(FileName, FileSize):
    lambda_metric(
        'crb-inbound-mplfairlending',
        FileSize,
        tags = [f'Name:{FileName}']
        )

def eventbridge_trigger():
    client = boto3.client('s3')
    Files = client.list_objects_v2(
        Bucket = BucketName,
    )
    for File in Files['Contents']:
        FileName = (File['Key'])
        FileSize = (File['Size'])
        lambda_metric(
            'crb-inbound-mplfairlending',
            FileSize,
            tags = [f'Name:{FileName}']
            )
