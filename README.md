# Details
## Pre-requisites
Run 
```shell
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage
This Python script has flags that you can pass to get the detail of how to use it:
```shell
python main.py -h
```
Output
```shell
usage: Migrate all Harness Applications from First Gen to Next Gen [-h] -a ACCOUNT_ID -t TOKEN -n NG_TOKEN [-d | --debug | --no-debug] [-o ORGANIZATION] [-f FILTER]
                                                                   [-r | --reverse-filter | --no-reverse-filter] [-s SECRET_SCOPE] [-c CONNECTOR_SCOPE] [-T TEMPLATE_SCOPE] [-w WORKFLOW_SCOPE]
                                                                   [-e ENVIRONMENT] [-N] [-p | --pipelines | --no-pipelines] [-W | --workflows | --no-workflows]

Perform the migration of all Harness Applications programmatically

options:
  -h, --help            show this help message and exit
  -a ACCOUNT_ID, --account-id ACCOUNT_ID
                        Harness First Gen Organization ID
  -t TOKEN, --token TOKEN
                        Harness First Gen API Token. You can fetch it from here https://app.harness.io/#/account/ACCOUNT_ID/access-management/api-keys
  -n NG_TOKEN, --ng-token NG_TOKEN
                        Harness Next Gen API Token. You can follow the process from here https://developer.harness.io/docs/platform/role-based-access-control/add-and-manage-service-account/
  -d, --debug, --no-debug
                        Enable debug log level
  -o ORGANIZATION, --organization ORGANIZATION
                        Organization Identifier - If not set, defaults to "default"
  -f FILTER, --filter FILTER
                        Comma separated list with filters to be applied for the applications
  -r, --reverse-filter, --no-reverse-filter
                        Negate filters attribute
  -s SECRET_SCOPE, --secret-scope SECRET_SCOPE
                        Secret Scope for all Applications
  -c CONNECTOR_SCOPE, --connector-scope CONNECTOR_SCOPE
                        Connector Scope for all Applications
  -T TEMPLATE_SCOPE, --template-scope TEMPLATE_SCOPE
                        Template Scope for all Applications
  -w WORKFLOW_SCOPE, --workflow-scope WORKFLOW_SCOPE
                        Workflow Scope for all Applications
  -e ENVIRONMENT, --environment ENVIRONMENT
                        Target Environment for NG Harness
  -N, --applications    Disable applications migration
  -p, --pipelines, --no-pipelines
                        Enable pipelines migration
  -W, --workflows, --no-workflows
                        Enable workflows migration
```