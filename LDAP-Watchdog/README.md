# LDAP WatchDog improved automation
The following repo contains the LDAP Watchdog python script that was writen by MegaManSec.
Url for github repo: https://github.com/MegaManSec/LDAP-Monitoring-Watchdog

## Changes made to the code
The code is based on the python library ldap3, the changes made are as follow:
1. The code used basic authentication to authenticate to AD, i changed it to use NTLM.
2. Used environment variables insted of hard coded credentials.
3. the code was refering to an attribute called entryUUID, the attribute does not exist and was switched with objectGUID.

## Docker file
The Dockerfile used references the ServiceNow-Agent ubuntu image, to clearify the image is a ubuntu:22.04 image with the /agent directory built into it. (slight modification to the Dockerfile can fix any issues if you do not have the ubuntu:servicenow-agent image)

The code requires specific packages to be installed such as: ldap3, pycryptodome.
1. LDAP3 - is used for AD querys.
2. pycryptodome - is used for NTLM authentication.