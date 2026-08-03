
from ansible.module_utils.common.parameters import env_fallback

UNIFI_NETWORK_QUERY_LIMIT = dict(
    query_limit=dict(type='int', required=False, default=100, fallback=(env_fallback, ['UNIFI_NETWORK_QUERY_LIMIT'])),
)