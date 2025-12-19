from ansible.module_utils.common.parameters import env_fallback

ACL_RULE_ID_ARG_SPEC = dict(
    unifi_network_acl_rule_id=dict(type='str', required=True, aliases=['acl_rule_uuid', 'acl_rule_id', 'rule', 'rule_id', 'zone_uuid', 'unifi_network_acl_rule_uuid'], fallback=(env_fallback, ['UNIFI_NETWORK_ACL_RULE_ID', 'UNIFI_NETWORK_ACL_RULE_UUID'])),
)

CLIENT_ID_ARG_SPEC = dict(
    unifi_network_client_id=dict(type='str', required=True, aliases=['client_uuid', 'client', 'unifi_network_client_uuid'], fallback=(env_fallback, ['UNIFI_NETWORK_CLIENT_ID', 'UNIFI_NETWORK_CLIENT_UUID']))
)

DEVICE_ID_ARG_SPEC = dict(
    unifi_network_device_id=dict(type='str', required=True, aliases=['device_uuid', 'device', 'unifi_network_device_uuid'], fallback=(env_fallback, ['UNIFI_NETWORK_DEVICE_ID', 'UNIFI_NETWORK_DEVICE_UUID'])),
)

FIREWALL_ZONE_ID_ARG_SPEC = dict(
    unifi_network_firewall_zone_id=dict(type='str', required=True, aliases=['firewall_zone_uuid', 'firewall_zone_id', 'zone', 'zone_id', 'zone_uuid', 'unifi_network_firewall_zone_uuid'], fallback=(env_fallback, ['UNIFI_NETWORK_FIREWALL_ZONE_ID', 'UNIFI_NETWORK_FIREWALL_ZONE_UUID'])),
)

HOTSPOT_VOUCHER_ID_ARG_SPEC = dict(
    unifi_network_hotspot_voucher_id=dict(type='str', required=True, aliases=['hotspot_voucher_uuid', 'hotspot_voucher_id', 'voucher', 'voucher_id', 'voucher_uuid', 'unifi_network_hotspot_voucher_uuid'], fallback=(env_fallback, ['UNIFI_NETWORK_HOTSPOT_VOUCHER_ID', 'UNIFI_NETWORK_HOTSPOT_VOUCHER_UUID'])),
)

NETWORK_ID_ARG_SPEC = dict(
    unifi_network_network_id=dict(type='str', required=True, aliases=['network_uuid', 'network', 'unifi_network_network_uuid'], fallback=(env_fallback, ['UNIFI_NETWORK_NETWORK_ID', 'UNIFI_NETWORK_NETWORK_UUID'])),
)

PORT_ID_ARG_SPEC = dict(
    unifi_network_port_id=dict(type='int', required=True, aliases=['port', 'port_id', 'unifi_network_device_port_id'], fallback=(env_fallback, ['UNIFI_NETWORK_PORT_ID', 'UNIFI_NETWORK_DEVICE_PORT_ID'])),
)

SITE_ID_ARG_SPEC = dict(
    unifi_network_site_id=dict(type='str', required=True, aliases=['site_id', 'site_uuid', 'site', 'unifi_network_site_uuid'], fallback=(env_fallback, ['UNIFI_NETWORK_SITE_ID', 'UNIFI_NETWORK_SITE_UUID'])),
)

TRAFFIC_MATCHING_LIST_ID_ARG_SPEC = dict(
    unifi_network_traffic_matching_list_id=dict(type='str', required=True, aliases=['traffic_matching_list_uuid', 'traffic_matching_list_id', 'zone', 'zone_id', 'zone_uuid', 'unifi_network_traffic_matching_list_uuid'], fallback=(env_fallback, ['UNIFI_NETWORK_TRAFFIC_MATCHING_LIST_ID', 'UNIFI_NETWORK_TRAFFIC_MATCHING_LIST_UUID'])),
)

WIFI_BROADCAST_ID_ARG_SPEC = dict(
    unifi_network_wifi_broadcast_id=dict(type='str', required=True, aliases=['wifi_broadcast_uuid', 'wifi_broadcast_id', 'unifi_network_wifi_broadcast_uuid'], fallback=(env_fallback, ['UNIFI_NETWORK_WIFI_BROADCAST_ID', 'UNIFI_NETWORK_WIFI_BROADCASTUU_ID'])),
)

FILTERS_ARG_SPEC = dict(
    unifi_network_filters=dict(type='dict', required=False, aliases=['filters', 'filter'],
        options=dict(
          property=dict(type='str', required=True),
          function=dict(type='str', required=True, choices=['isNull', 'isNotNull', 'eq', 'ne', 'gt', 'ge', 'lt', 'le', 'like', 'in', 'notIn', 'isEmpty', 'contains', 'containsAny', 'containsAll', 'containsExactly']),
          value=dict(type='raw', required=False, default=None),
        ),
    ),
    unifi_network_filters_raw=dict(type='str', required=False, aliases=['filters_raw', 'filter_raw'])
)