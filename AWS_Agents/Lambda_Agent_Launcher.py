import boto3, json

def lambda_handler(event, context):
    Body = event['Records'][0]['body']
    ConvertBodytoJson = json.loads(Body)
    Message = json.loads(ConvertBodytoJson['Message'])
    Requirements = Message['requirements']
    launch_agent(Requirements)


def launch_agent(Requirements):
    sts_connection = boto3.client('sts')
    developer_role = sts_connection.assume_role(
        RoleArn = "arn:aws:iam::************:role/ECS-Lambda-Agent",
        RoleSessionName = "developer_role"
    )
    access_key = developer_role['Credentials']['AccessKeyId']
    secret_key = developer_role['Credentials']['SecretAccessKey']
    session_token = developer_role['Credentials']['SessionToken']

    client = boto3.client('ecs',
                          aws_access_key_id = access_key,
                          aws_secret_access_key = secret_key,
                          aws_session_token = session_token)
    response = client.run_task(
        cluster = 'arn:aws:ecs:us-east-1:************:cluster/infrastructure_prod_cluster',
        count = 1,
        enableECSManagedTags = False,
        enableExecuteCommand = False,
        launchType = 'FARGATE',
        networkConfiguration={
            'awsvpcConfiguration': {
                'subnets': [
                    'subnet-09ff541150c0b2116', 'subnet-0d50e287ffa2ac044',
                ],
                'securityGroups': [
                    'sg-07105dcf7df6466f8', 'sg-0f635e54a71fddcf9',
                ],
                'assignPublicIp': 'DISABLED'
            }
        },
        overrides={
                'containerOverrides': [
                {
                    'name': 'agent-1',
                    'environment': [
                        {
                            'name': 'information',
                            'value': f'{Requirements}'
                        },
                    ],
                },
            ],
        },
        taskDefinition='ServiceNow-Agent'
    )
    return(response)
