FROM ubuntu:servicenow-agent

RUN apt update -y
RUN apt upgrade -y
RUN apt install python3 pip procps -y
RUN pip install ldap3 pycryptodome requests

WORKDIR /agent

COPY ./ldap-watchdog.py ./

CMD ["python3", "./ldap-watchdog.py"]