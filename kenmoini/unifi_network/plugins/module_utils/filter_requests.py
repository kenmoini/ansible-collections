
from ansible.module_utils.basic import AnsibleModule

# Utility function to filter requests
def filter_requests(module, targetURL, result):
    urlPrefix = "?"
    if "?" in targetURL:
        urlPrefix = "&"

    # Make sure both filter parameters are not provided
    if module.params.get('unifi_network_filters') and module.params.get('unifi_network_filters_raw'):
        module.fail_json(msg="Both 'unifi_network_filters' and 'unifi_network_filters_raw' parameters cannot be provided at the same time.", **result)
    
    # Apply raw filter if provided
    if module.params.get('unifi_network_filters_raw'):
        targetURL += urlPrefix + 'filter=' + module.params['unifi_network_filters_raw']

    # Apply simple structured filter if provided
    if module.params.get('unifi_network_filters'):
        filter_param = module.params['unifi_network_filters']
        targetURL += urlPrefix + 'filter=%s.%s(\'%s\')' % (filter_param['property'], filter_param['function'], filter_param['value'])

    return targetURL