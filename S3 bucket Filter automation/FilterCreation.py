import boto3
import testing
import botocore

client = boto3.client(
    's3',
    aws_access_key_id= testing.aws_access_key_id,
    aws_secret_access_key= testing.aws_secret_access_key,
    aws_session_token = testing.aws_session_token,
    region_name = testing.aws_region
)

s3 = boto3.resource(
    's3',
    aws_access_key_id= testing.aws_access_key_id,
    aws_secret_access_key= testing.aws_secret_access_key,
    aws_session_token = testing.aws_session_token,
    region_name = testing.aws_region
    )

# this for loop gets all s3 buckets and creates a request metric filter
for bucket in s3.buckets.all():
    Bucket = s3.Bucket(bucket.name)
    try:
        response = client.put_bucket_metrics_configuration(
        Bucket=Bucket.name,
        Id='EntireBucket',
        MetricsConfiguration={
            'Id': 'EntireBucket',
            }
        )
        print(response)
    except botocore.exceptions.ClientError:
        print('An error occurred when calling the ListBuckets operation: The AWS Access Key Id you provided does not exist in our records.')
        break
