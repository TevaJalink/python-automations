import boto3
import sys

client = boto3.client('sns',
                      region_name='us-east-1',
                      aws_access_key_id='',
                      aws_secret_access_key='')
Body = {
	"requirements": {
		"CPU": f"{sys.argv[1]}",
		"RAM": f"{sys.argv[2]}",
		"DiskSpace": f"{sys.argv[3]}",
		"ServerName": f"{sys.argv[4]}"
	}
}
send_messages = client.publish(
    TopicArn='arn:aws:sns:us-east-1:193244750463:ServiceNow-SNS-Topic',
    Message=f'{Body}'
)