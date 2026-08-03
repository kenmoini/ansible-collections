
from ansible.module_utils.common.parameters import env_fallback

UNIFI_NETWORK_QUERY_OFFSET = dict(
    query_offset=dict(type='int', required=False, default=0, fallback=(env_fallback, ['UNIFI_NETWORK_QUERY_OFFSET'])),
)