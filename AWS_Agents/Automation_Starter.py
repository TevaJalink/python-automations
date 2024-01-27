import requests, jenkins, os, base64, json, time, sys

PAT = os.environ['PAT_Token']
Requirements = os.environ['information']
Requirements_replace = Requirements.replace("'", "\"")
Information = json.loads(Requirements_replace)
request_name = Information['RequestName']
base64_PAT = str(base64.b64encode(bytes(':'+PAT, 'ascii')), 'ascii')
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Basic {base64_PAT}"
}

def Create_Jenkins_Connection():
    Jenkins_Session_Token = os.environ['Jenkins_Session_Token']
    server = jenkins.Jenkins('https://jenkinssre.crbcloud.com/',username='2f42af9b-7b3f-4928-8184-14dff7259143',password=f'{Jenkins_Session_Token}')
    return server

def Run_SFTP_Automation(server):
    Jenkins_Pipeline_Token = os.environ['Jenkins_Token']
    Company_Name = Information['Company_Name']
    Ticket_ID = Information['Ticket_ID']
    server.build_job("ITEngineering/sftp-automation",{"COMPANY_NAME": f"{Company_Name}", "TICKET_ID": f"{Ticket_ID}"}, token = f"{Jenkins_Pipeline_Token}")
    time.sleep(10)
    get_build_number = server.get_job_info('ITEngineering/sftp-automation')['lastBuild']['number']
    return get_build_number

def Test_SFTP_Job_Status(server, get_build_number):
    get_build_info = server.get_build_info("ITEngineering/sftp-automation", get_build_number)['result']
    if get_build_info == 'SUCCESS':
        print('SFTP OnBoarding completed successfuly')
        sys.exit(0)
    if get_build_info == 'None':
        time.sleep(10)
        Test_SFTP_Job_Status(server, get_build_number)
    if get_build_info == 'FAILURE':
        sys.exit('SFTP OnBoarding Failed in Jenkins Pipeline')

def Run_CVM_LVM():
    User_Name = Information['User_Name']
    Operating_System = Information['Operating_System']
    Machine_Type = Information['Machine_Type']
    post_url = 'https://dev.azure.com/crossriverbank/Infrastructure/_apis/pipelines/1446/runs?api-version=7.1-preview.1'
    uri_data = {
        "resources": {},
        "templateParameters": {"pipelineparam1": User_Name, "pipelineparam2": Operating_System, "pipelineparam4": Machine_Type},
        "variables": {}
    }
    response = requests.post(post_url,headers=headers,json=uri_data)
    if response.status_code == 200:
        response_json = json.loads(response.text)
        buildid = response_json['id']
        return buildid
    else:
        raise Exception("NO build ID found")

def Run_EC2_Creation():
    Account_Name = Information['Account_Name']
    Instance_Name = Information['Instance_Name']
    Domain_To_Join = Information['Domain_To_Join']
    Image = Information['Image']
    Instance_Type = Information['Instance_Type']
    post_url = 'https://dev.azure.com/crossriverbank/Infrastructure/_apis/pipelines/1644/runs?api-version=7.1-preview.1'
    uri_data = {
        "resources": {},
        "templateParameters": {"parameter1": Account_Name, "parameter2": Instance_Name,"domain_name": Domain_To_Join, "parameter3": Image, "parameter4": Instance_Type},
        "variables": {}
    }
    response = requests.post(post_url,headers=headers,json=uri_data)
    if response.status_code == 200:
        response_json = json.loads(response.text)
        buildid = response_json['id']
        return buildid
    else:
        raise Exception("No build ID found")

def Test_ADO_Build_Status(buildid):
    get_url = f'https://dev.azure.com/crossriverbank/Infrastructure/_apis/build/builds/{buildid}?api-version=7.1-preview.7'
    response = requests.get(get_url,headers=headers)
    response_json = json.loads(response.text)
    if response_json['status'] != 'completed':
        time.sleep(60)
        Test_ADO_Build_Status(buildid)
    if response_json['status'] == 'completed':
        return "Build completed"


if request_name == 'SFTP OnBoarding':
    server = Create_Jenkins_Connection()
    get_build_number = Run_SFTP_Automation(server)
    time.sleep(60)
    Test_SFTP_Job_Status(server, get_build_number)
if request_name == 'CVM LVM Deployment':
    buildid = Run_CVM_LVM()
    Test_ADO_Build_Status(buildid)
if request_name == 'EC2 deployment':
    buildid = Run_EC2_Creation()
    Test_ADO_Build_Status(buildid)
