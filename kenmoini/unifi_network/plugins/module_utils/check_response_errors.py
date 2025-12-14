
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.parameters import env_fallback
import requests

def check_response_errors(module, response, result, context=''):
    if response.status_code != 200:
        json_response = response.json()
        if response.status_code == 400:
            module.fail_json(msg=f'Bad Request sent to Unifi Network API{context}, missing credential? Code: ' + json_response['code'] + ' - Message: ' + json_response['message'], **result)
        if response.status_code == 401:
            module.fail_json(msg=f'Unauthorized to access Unifi Network API{context}, invalid API Key? Code: ' + json_response['code'] + ' - Message: ' + json_response['message'], **result)
        if response.status_code == 403:
            module.fail_json(msg=f'Forbidden to access Unifi Network API{context}, check API Key permissions? Code: ' + json_response['code'] + ' - Message: ' + json_response['message'], **result)
        if response.status_code == 404:
            module.fail_json(msg=f'Resource not found in Unifi Network API{context}, check provided IDs? Code: ' + json_response['code'] + ' - Message: ' + json_response['message'], **result)
        if response.status_code == 500:
            module.fail_json(msg=f'Unifi Network API Internal Server Error{context}, try again later? Code: ' + json_response['code'] + ' - Message: ' + json_response['message'], **result)

        module.fail_json(msg=f'Failed to retrieve data from Unifi Network{context}. Code: ' + json_response['code'] + ' - Message: ' + json_response['message'], **result)