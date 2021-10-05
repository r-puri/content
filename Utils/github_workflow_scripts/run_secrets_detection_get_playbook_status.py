#!/usr/bin/env python3

import argparse
import ast
import sys
import time
import logging

import demisto_client

import urllib3
from demisto_client.demisto_api.rest import ApiException
from demisto_sdk.commands.common.constants import PB_Status

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# ----- Constants ----- #
DEFAULT_TIMEOUT = 60
DEFAULT_INTERVAL = 20
GOLD_SERVER_URL = "https://content-gold.paloaltonetworks.com"


# returns current investigation playbook state - 'inprogress'/'failed'/'completed'
def __get_investigation_playbook_state(client, inv_id):
    try:
        investigation_playbook_raw = demisto_client.generic_request_func(self=client, method='GET',
                                                                         path='/inv-playbook/' + inv_id)
        investigation_playbook = ast.literal_eval(investigation_playbook_raw[0])
    except ApiException:
        logging.exception(
            'Failed to get investigation playbook state, error trying to communicate with demisto server')
        return PB_Status.FAILED

    try:
        state = investigation_playbook['state']
        return state
    except:  # noqa: E722
        return PB_Status.NOT_SUPPORTED_VERSION


# wait for playbook to finish run
# return playbook status
def check_integration(investigation_id, client):
    logging.info(f'Investigation URL: {GOLD_SERVER_URL}/#/WorkPlan/{investigation_id}')

    timeout = time.time() + DEFAULT_TIMEOUT
    i = 1
    # wait for playbook to finish run
    while True:
        # give playbook time to run
        time.sleep(1)

        try:
            # fetch status
            playbook_state = __get_investigation_playbook_state(client, investigation_id)
        except demisto_client.demisto_api.rest.ApiException:
            playbook_state = 'Pending'
            client = demisto_client.configure(base_url=client.api_client.configuration.host,
                                              api_key=client.api_client.configuration.api_key, verify_ssl=False)

        if playbook_state == PB_Status.COMPLETED:
            break

        if playbook_state == PB_Status.FAILED:
            print(f' Secrets playbook was failed as secrets were found. To investigate go to: <>')
            sys.exit(1)

        if time.time() > timeout:
            print(f' Secrets playbook timeout reached. To investigate go to: <>')
            sys.exit(1)

        i = i + 1

    if playbook_state == PB_Status.COMPLETED:
        print("Secrets playbook finished successfully, no secrets were found. ")


def arguments_handler():
    """ Validates and parses script arguments.

     Returns:
        Namespace: Parsed arguments object.

     """
    parser = argparse.ArgumentParser(description='Get playbook status.')
    parser.add_argument('-i', '--investigation_id', help='The investigation id of the secrets detection playbook.')
    #parser.add_argument('-k', '--api_key', help='Gold Api key')
    return parser.parse_args()


def main():
    options = arguments_handler()
    investigation_id = options.investigation_id
    # api_key = options.api_key
    api_key = "10C1EF6CE6DD39E327CE5B327ECC5AE1"  # temp one
    if investigation_id:
        """
            :param demisto_user: Username of the demisto user running the tests.
            :param demisto_pass: Password of the demisto user running the tests.
        """
        client = demisto_client.configure(base_url=GOLD_SERVER_URL, api_key=api_key, verify_ssl=False)
        check_integration(investigation_id, client)
    else:
        print("Secrets detection playbook was failed to get investigation id")
        sys.exit(1)


if __name__ == "__main__":
    main()
