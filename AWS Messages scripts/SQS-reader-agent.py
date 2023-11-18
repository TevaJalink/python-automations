import boto3, json
import requests

client = boto3.client(
    'sqs',
    aws_access_key_id= '',
    aws_secret_access_key= '',
    aws_session_token = '',
    region_name = 'us-east-1'
                      )

response = client.receive_message(
    QueueUrl = 'https://sqs.us-east-1.amazonaws.com/193244750463/ServiceNow-SNS-SQS-Agent-Queue',
)
Body = response['Messages'][0]['Body']
ticket_uniqe_id = Body['Id'] #need to verify the id for tickets

def start_jenkins_job(jobname):
    url_post = f'https://jenkinssre.crbcloud.com/job/ITEngineering/job/{jobname}/build'
    print(url_post)
    # post_Response = requests.post (url_post, json = '')
    # response_json = post_Response.json()

if ticket_uniqe_id == '':
    start_jenkins_job('SFTP Automation')
elif ticket_uniqe_id == '':
    start_jenkins_job('VMWare Server Creation')
elif ticket_uniqe_id == '':
    start_jenkins_job('AWS Workspaces Creation')









