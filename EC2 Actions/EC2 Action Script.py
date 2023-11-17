import boto3
import os
import sys
import time

requested_machine = sys.argv[1][0:4].lower() + sys.argv[1][-6:].upper()
Action_requested = sys.argv[2]

def check_user_integrity():
    pipeline_user_name = os.getenv('BUILD_REQUESTEDFOR')
    user_name_split_array = pipeline_user_name.split(' ')
    user_name_string_attached = (user_name_split_array[0][0] + user_name_split_array[1][0:3]).lower()
    if requested_machine == str(user_name_string_attached) + 'AWSLVM':
        print('User LVM Machine Found')
    elif requested_machine == str(user_name_string_attached) + 'AWSCVM':
        print('User CVM Machine Found')
    else:
        raise Exception("No Valid Machine Found Or Machine Does Not Belong To You")

def get_instance_id(Machine_Name):
    client = boto3.client('ec2', region_name='us-east-1', aws_access_key_id=sys.argv[3], aws_secret_access_key=sys.argv[4] )
    response = client.describe_instances(Filters=[{'Name': 'tag:Name', 'Values': [Machine_Name]}])
    response_Reservations = response['Reservations']
    InstanceID = response_Reservations[0]['Instances'][0]['InstanceId']
    return InstanceID

def preform_action(Action, InstanceId):
    client = boto3.client('ec2', region_name='us-east-1', aws_access_key_id=sys.argv[3], aws_secret_access_key=sys.argv[4] )
    if Action in ['ShutDown', 'Restart']:
        try:
            client.stop_instances(InstanceIds=[InstanceId])
            print(f'the machine {requested_machine} is shutting down')
        except:
            print("something went wrong")
    if Action in ['StartUp', 'Restart']:
        time.sleep(1)
        response = client.describe_instances(InstanceIds=[InstanceId])
        instance_status = response['Reservations'][0]['Instances'][0]['State']['Name']
        if instance_status == 'stopped':
            try:
                client.start_instances(InstanceIds=[InstanceId])
                print(f'the machine {requested_machine} is starting up')
            except:
                print("something went wrong")
        elif instance_status == 'running':
            raise Exception(f'Machine {requested_machine} is already running')
        else:
            time.sleep(5)
            preform_action('StartUp', InstanceID)

check_user_integrity()
InstanceID = get_instance_id(requested_machine)
preform_action(Action_requested, InstanceID)
