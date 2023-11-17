import boto3, json
import requests

client = boto3.client(
    'sqs',
    aws_access_key_id= 'ASIASZ7SI4J7SGLVQQHO',
    aws_secret_access_key= 'fM7ZsaBC4XzyVKKdTLYogD/840ZtxzKBci0mMXDC',
    aws_session_token = 'IQoJb3JpZ2luX2VjEFwaCXVzLWVhc3QtMSJIMEYCIQDL5HAk+bWLn7lFwV4Lnk7qNk8aHuuvy0a86VEbf77WjwIhAI7gqVJKS591IPI0yZQX9AYLqsATzsixUUHWFyYaO9PBKpIDCHUQAxoMMTkzMjQ0NzUwNDYzIgxgiKwVxkupyj0Kzf0q7wITCz3dtits6uEZhF2L+4x9c3Gs606Ia/1ppeIoFOZZFJNJ2xh91ue6JXFQ/k8N3jeSKV8V7fApriVb+4V28R9k5wpMz+yGVb01VBpxFJPjCQV4hdL2zcpYwdrmAK0CdvWbnwmNiT6NLRf+sJgC+84ppR5ydxJDbZ7nkNDbhnOnbtwnM/299F2L3FwNx7H7eDqnaqIzD4J4RE9U+cw2hEJh759V30JpGWjuXbrMxBNpxo35VJTZaFEoVQAoGaFvVCJTYmYCAmNr9Y8FR/sFTfYnNm09LpRwHpanvfLUjGL8cY+USxzc5agxXeO3l0n8gwGniYgDbApCNVsnabzU0IFwP4cObU5HuSCgFBxZ4MJCiY/U+Y/ITQY/RHRWX39wUAZEYaYB8A9PJRFQ3ZJh0LG4jGA/pIXzLZ8+Ab/G3u/9JB86m+xjNjqFlkes641xXyEjikSCQCgqg7AxuP0Lu3EHnFumj0tFvokGWoRlCX38MJze6KIGOqUBn3CGdYbZT3pMcyLFkwqIAzgA5pbueK5qCCbkLhJY52kJ4ZTHf3ppk7N3WSp+XOzQPETnXJbYPRukoIt1OinHCoFEKmUfSz2sKp5d67+Rn/ciF6qK69RxsBW3+2jl3QsBb3ycfG6+6fZwA1b0WBEIk0MPGeX2eMY3BG02o1HNNMWXOCOyYmQNLo1OBQQDpCwgyTrC+Te5kwM7S2safI1rRlBH5t0R',
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









