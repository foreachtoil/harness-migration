import requests
import argparse
import json
import subprocess
import logging
import re
import random
import yaml

from typing import List, Dict

logFormatter = logging.Formatter("%(asctime)s [%(levelname)-7.7s]  %(message)s")
rootLogger = logging.getLogger()
rootLogger.setLevel(logging.INFO)

fileHandler = logging.FileHandler("{0}/{1}.log".format('.', 'harness_migration'))
fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)


def run_cmd(cmd, to_json=False, exit_on_error=True):
    try:
        rootLogger.info('Running command')
        rootLogger.debug(f'Command: {cmd}')
        p = subprocess.run(cmd, shell=True, capture_output=True)
        raw = p.stdout.decode('utf-8').replace('\x1b[0m', '')
        if p.stderr:
            rootLogger.error(p.stderr.decode('utf-8').replace('\x1b[0m', ''))
            return None

        if to_json:
            return json.loads(raw)
        else:
            return raw
    except subprocess.CalledProcessError as e:
        if not exit_on_error:
            return None
        rootLogger.error(f'command [{cmd}] failed')


def create_next_gen_projects(account: str, applications: List[Dict[str, str | None]], token: str, org: str):
    url = f'https://app.harness.io/ng/api/projects?accountIdentifier={account}&orgIdentifier={org}'
    headers = {
        'content-type': 'application/json',
        'x-api-key': token
    }
    payload = {
        'project': {
            'orgIdentifier': org,
            'modules': [
                "CD", "CI", "CV", "CF", "CE", "STO", "CHAOS", "SRM", "IACM", "CET", "CODE", "CORE", "PMS",
                "TEMPLATESERVICE"
            ]
        }
    }

    for application in applications:
        application['identifier'] = re.sub('[^0-9a-zA-Z]+', '', application['name'])
        payload['project']['identifier'] = application['identifier']
        payload['project']['name'] = application['name']
        payload['project']['description'] = application['description']
        payload['project']['color'] = f'#{hex(random.randrange(0, 2 ** 24))[2:]}'
        response = requests.post(url=url, json=payload, headers=headers).json()
        if response['status'] == 'ERROR':
            logging.warning(response['message'])
            logging.debug(payload)
        else:
            logging.info(f'Project {application["name"]} created successfuly in Organization {org}')
    return applications


def migrate_harness(
        harness_applications: List[Dict[str, str | None]],
        token: str,
        org: str,
        account: str,
        secret_scope: str,
        connector_scope: str,
        template_scope: str,
        workflow_scope: str,
        environment: str,
        applications: bool,
        pipelines: bool,
        workflows: bool,
        workflows_as_pipelines: bool,

):
    migrations = [
        'app --all' if applications else '',
        'pipelines --all import' if pipelines else '',
        'workflows --all' if workflows else ''
        'workflows --all --as-pipelines' if workflows_as_pipelines else ''
    ]
    prefix = './values-'
    migrations = list(filter(None, migrations))
    index = 0
    total_harness_applications = len(harness_applications)
    for application in harness_applications:
        with open(f'{prefix}{application["identifier"]}.yaml', 'w+') as outfile:
            yaml.dump({
                "env": environment,
                "api-key": token,
                "account": account,
                "app": application["id"],
                "project": application["identifier"],
                "org": org,
                "secret-scope": secret_scope,
                "connector-scope": connector_scope,
                "template-scope": template_scope,
                "workflow-scope": workflow_scope
            }, outfile, default_flow_style=False)
            rootLogger.info(f'File created at {prefix}{application["identifier"]}.yaml')
        migration_type = []
        if application:
            migration_type.extend(["application", "workflows", "secrets", "pipelines"])
        else:
            if pipelines:
                migration_type.append("pipelines")
            if workflows and not application:
                migration_type.append("workflows")
            if workflows_as_pipelines and not application:
                migration_type.append("workflows as pipelines")
        logging.info(f'Migrating {", ".join(migration_type)} for application {application["name"]}')
        for migration in migrations:
            command = f'harness-upgrade --api-key {token} --project {application["identifier"]} --org {org} ' \
                      f'--account {account} --app {application["id"]} --secret-scope {secret_scope} ' \
                      f'--connector-scope {connector_scope} --template-scope {template_scope} ' \
                      f'--workflow-scope {workflow_scope} --env {environment} {migration}'

            rootLogger.info(f'You can run this again by executing the following command: ')
            rootLogger.info(f'harness-upgrade --load {prefix}{application["identifier"]}.yaml {migration}')
            output = run_cmd(command)
            rootLogger.info(f'Application {application["name"]} has been migrated to Harness NG.')
            rootLogger.debug(output)
        index+=1
        rootLogger.info(f'{index} applications migrated out of {total_harness_applications}')


def get_all_applications(account: str, token: str, app_filter: str, reverse_filter: bool):
    harness_first_gen_url = f'https://app.harness.io/gateway/api/graphql?accountId={account}'
    applications = []
    filtered_applications = []
    headers = {
        'x-api-key': f'{token}',
        'content-type': 'application/json'
    }
    body_start = '{ applications( limit: 100    offset:'
    body_end = '){nodes{id  name description }}}'
    offset = 0
    try:
        while extracted_applications := requests.post(
                url=harness_first_gen_url,
                json={"query": f'{body_start}{offset}{body_end}'}, headers=headers
        ).json()['data']['applications']['nodes']:
            applications.extend(extracted_applications)
            offset += 100
        else:
            rootLogger.debug(f'Last offset used {offset}')
    except KeyError:
        rootLogger.error('Error Authenticating against Harness - Verify your token')
    if app_filter:
        app_filter = app_filter.split(',')
        for application in applications:
            if (application['name'] in app_filter) is not reverse_filter and app_filter:
                rootLogger.debug(f'Application {application["name"]} filtered based in {"reverse" if reverse_filter else "direct"} match')
                filtered_applications.append(application)
    else:
        filtered_applications = applications
    rootLogger.info(f'Total applications {"after filters " if app_filter else ""}{len(filtered_applications)}')
    return filtered_applications


def main():
    parser = argparse.ArgumentParser(
        prog='Migrate all Harness Applications from First Gen to Next Gen',
        description='Perform the migration of all Harness Applications programmatically'
    )
    parser.add_argument(
        '-a',
        '--account-id',
        help='Harness First Gen Organization ID',
        required=True
    )
    parser.add_argument(
        '-t',
        '--token',
        help='Harness First Gen API Token. \n You can fetch it from here https://app.harness.io/#/account/ACCOUNT_ID/access-management/api-keys',
        required=True
    )
    parser.add_argument(
        '-n',
        '--ng-token',
        help='Harness Next Gen API Token. \n'
             'You can follow the process from here '
             'https://developer.harness.io/docs/platform/role-based-access-control/add-and-manage-service-account/',
        required=True
    )
    parser.add_argument(
        '-d',
        '--debug',
        help='Enable debug log level',
        action=argparse.BooleanOptionalAction
    )
    parser.add_argument(
        '-o',
        '--organization',
        help='Organization Identifier - If not set, defaults to "default"',
        default='default'
    )
    parser.add_argument(
        '-f',
        '--filter',
        help='Comma separated list with filters to be applied for the applications',
        default=''
    )
    parser.add_argument(
        '-r',
        '--reverse-filter',
        help='Negate filters attribute',
        action=argparse.BooleanOptionalAction,
        default=False
    )
    parser.add_argument(
        '-s',
        '--secret-scope',
        help='Secret Scope for all Applications',
        default='account'
    )
    parser.add_argument(
        '-c',
        '--connector-scope',
        help='Connector Scope for all Applications',
        default='account'
    )
    parser.add_argument(
        '-T',
        '--template-scope',
        help='Template Scope for all Applications',
        default='account'
    )
    parser.add_argument(
        '-w',
        '--workflow-scope',
        help='Workflow Scope for all Applications',
        default='project'
    )
    parser.add_argument(
        '-e',
        '--environment',
        help='Target Environment for NG Harness',
        default='Prod'
    )
    parser.add_argument(
        '-N',
        '--applications',
        help='Disable applications migration',
        action='store_false',
    )
    parser.add_argument(
        '-p',
        '--pipelines',
        help='Enable pipelines migration',
        action=argparse.BooleanOptionalAction,
        default=False
    )
    parser.add_argument(
        '-W',
        '--workflows',
        help='Enable workflows migration',
        action=argparse.BooleanOptionalAction,
        default=False
    )
    parser.add_argument(
        '--workflows-as-pipelines',
        help='Enable workflows migration as pipelines',
        action=argparse.BooleanOptionalAction,
        default=False
    )

    args = parser.parse_args()
    if args.debug:
        rootLogger.setLevel(logging.DEBUG)
    harness_applications = get_all_applications(
        account=args.account_id,
        token=args.token,
        app_filter=args.filter,
        reverse_filter=args.reverse_filter
    )
    harness_next_gen_applications = create_next_gen_projects(
        account=args.account_id,
        applications=harness_applications,
        token=args.ng_token,
        org=args.organization
    )

    migrate_harness(
        harness_applications=harness_next_gen_applications,
        account=args.account_id,
        token=args.ng_token,
        org=args.organization,
        secret_scope=args.secret_scope,
        connector_scope=args.connector_scope,
        template_scope=args.template_scope,
        workflow_scope=args.workflow_scope,
        environment=args.environment,
        applications=args.applications,
        pipelines=args.pipelines,
        workflows=args.workflows,
        workflows_as_pipelines=args.workflows_as_pipelines
    )


if __name__ == '__main__':
    main()
