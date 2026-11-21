#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Ken Moini <ken@kenmoini.com>
# MIT License

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: wifi_broadcast
short_description: Manage WiFi broadcasts (SSIDs) in UniFi Network
version_added: "2.0.0"
description:
  - Creates, updates or deletes WiFi broadcasts (SSIDs) with their security, network, broadcasting devices,
    schedule and filtering settings.
  - The broadcast is found by O(name), or by O(id) when given (which also allows renaming it).
  - Only the options you set are managed. The module reads the broadcast first, merges your options into it
    and only writes when something differs, so unrelated settings made in the UniFi UI are kept.
  - "Which options apply depends on O(type): V(standard) broadcasts support every option, V(iot_optimized)
    broadcasts do not support the options marked as standard only."
  - Passphrases are never compared, because the API cannot be relied on to return them. See O(update_passphrase) for how they are applied.
options:
  name:
    description:
      - The WiFi name (SSID). Used to find the broadcast when O(id) is not set.
      - Required unless O(id) is set.
    type: str
    aliases: [ssid]
  id:
    description:
      - UUID of an existing broadcast to manage. When set, O(name) renames the broadcast.
    type: str
  state:
    description:
      - V(present) creates or updates the broadcast, V(absent) deletes it.
    type: str
    choices: [present, absent]
    default: present
  force:
    description:
      - With O(state=absent), delete the broadcast even if other resources still reference it.
    type: bool
    default: false
  type:
    description:
      - V(standard) is a regular broadcast. V(iot_optimized) is tuned for IoT devices and supports fewer options.
      - New broadcasts are V(standard) unless this is set. Changing the type drops the settings the new type does not support.
    type: str
    choices: [standard, iot_optimized]
  enabled:
    description:
      - Whether the broadcast is enabled. New broadcasts are enabled unless this is V(false).
    type: bool
  security:
    description:
      - Security settings. O(security.type) is required when creating a broadcast.
      - Changing O(security.type) replaces all security settings, so give every security option you want to keep.
      - Each option is only valid for the security types listed in its description.
    type: dict
    suboptions:
      type:
        description:
          - The security type. Required when creating a broadcast.
          - The V(*_personal) types use a shared passphrase, the V(*_enterprise) types authenticate users against
            the RADIUS profile in O(security.radius_profile).
        type: str
        choices: [open, wpa2_personal, wpa3_personal, wpa2_wpa3_personal, wpa2_enterprise, wpa3_enterprise, wpa2_wpa3_enterprise]
      passphrase:
        description:
          - The WiFi passphrase, 8 to 63 characters. Only for V(*_personal) types.
          - Required when creating a broadcast with, or switching to, a personal type (for V(wpa2_personal),
            O(security.preshared_keys) can be used instead).
          - It is not read back from the API, so set it on every run; see O(update_passphrase).
        type: str
      preshared_keys:
        description:
          - Private pre-shared keys, each placing its clients on a different Network. Only for V(wpa2_personal).
          - Handled like O(security.passphrase); the list is authoritative and only sent as described in O(update_passphrase).
        type: list
        elements: dict
        suboptions:
          network:
            description:
              - Network for clients using this key, as V(native) or a Network name or UUID.
            type: str
            required: true
          passphrase:
            description:
              - The passphrase of this key.
            type: str
            required: true
      pmf_mode:
        description:
          - Protected Management Frames. V(disabled) turns them off.
          - Only for V(wpa2_personal), V(wpa2_wpa3_personal), V(wpa2_enterprise) and V(wpa2_wpa3_enterprise), and standard only.
          - Defaults to V(optional) when switching to V(wpa2_wpa3_personal) or V(wpa2_wpa3_enterprise).
        type: str
        choices: [required, optional, disabled]
      fast_roaming_enabled:
        description:
          - Fast roaming (802.11r). Not for V(open), and standard only.
        type: bool
      wpa3_fast_roaming_enabled:
        description:
          - WPA3 fast roaming; requires O(security.fast_roaming_enabled). Only for V(wpa2_wpa3_personal) and V(wpa2_wpa3_enterprise).
          - Defaults to V(false) when switching to one of those types.
        type: bool
      group_rekey_interval_seconds:
        description:
          - How often, in seconds (1 to 86400), clients get a new group key. V(0) turns group rekeying off.
          - Not for V(open), and standard only.
        type: int
      sae:
        description:
          - SAE (Simultaneous Authentication of Equals) settings. Only for V(wpa3_personal) and V(wpa2_wpa3_personal).
          - Both values default to V(5) when switching to one of those types.
        type: dict
        suboptions:
          anti_clogging_threshold_seconds:
            description: SAE anti-clogging threshold in seconds, 1 to 60.
            type: int
            aliases: [anticlogging_threshold_seconds]
          sync_time_seconds:
            description: SAE sync time in seconds, 1 to 60.
            type: int
      encryption:
        description:
          - Encryption of an open network. V(none) is plain open; the others use Enhanced Open (OWE),
            optionally with a transition network for clients without OWE support. Only for V(open).
        type: str
        choices: [none, enhanced_open, enhanced_open_with_transition]
      coa_enabled:
        description:
          - RADIUS Change of Authorization. Only for V(*_enterprise) types; defaults to V(false) when switching to one.
        type: bool
      security_mode:
        description:
          - V(high_security_192_bit) enables WPA3-Enterprise 192-bit mode. Only for V(wpa3_enterprise); defaults to V(default).
        type: str
        choices: [default, high_security_192_bit]
      radius_profile:
        description:
          - RADIUS profile, given as its name or UUID.
          - Required for V(*_enterprise) types, where it authenticates users.
          - For V(open) and V(*_personal) types it turns on RADIUS MAC authentication; an empty string turns it off.
        type: str
      nas_id:
        description:
          - A fixed RADIUS NAS identifier. Mutually exclusive with O(security.nas_id_source).
        type: str
      nas_id_source:
        description:
          - Derive the RADIUS NAS identifier from this value. Mutually exclusive with O(security.nas_id).
          - When RADIUS is first configured and neither is set, V(device_name) is used.
        type: str
        choices: [device_mac_address, device_name, site_name, bssid]
      mac_auth_format:
        description:
          - Format of the MAC address sent for RADIUS MAC authentication.
          - For V(open) and V(*_personal) types it defaults to V(lowercase_not_separated) when RADIUS is first configured.
          - For V(*_enterprise) types MAC authentication is optional; V(disabled) turns it off.
        type: str
        choices: [uppercase_not_separated, uppercase_dash_separated, uppercase_colon_separated, lowercase_not_separated,
                  lowercase_colon_separated, lowercase_dash_separated, disabled]
        aliases: [mac_address_format]
  update_passphrase:
    description:
      - V(on_create) never compares O(security.passphrase) or O(security.preshared_keys), because they are not read back from the API.
        They are sent when the broadcast is created, when the security type changes, and along with any other change.
      - Because every update replaces the whole configuration, updating a V(*_personal) broadcast requires O(security.passphrase)
        (or O(security.preshared_keys)); without it the module fails instead of sending a configuration without its key.
      - V(always) sends them on every run and reports a change, which is how to rotate a passphrase.
    type: str
    choices: [on_create, always]
    default: on_create
  network:
    description:
      - Network that clients join, as V(native) (the native network of the broadcasting devices) or a Network name or UUID.
    type: str
  devices:
    description:
      - Broadcast only from these access points, given as names, MAC addresses or UUIDs.
      - An empty list broadcasts from all access points. Mutually exclusive with O(device_tags).
    type: list
    elements: str
    aliases: [device_ids]
  device_tags:
    description:
      - Broadcast only from access points with these device tags, given as names or UUIDs.
      - An empty list broadcasts from all access points. Mutually exclusive with O(devices).
    type: list
    elements: str
    aliases: [device_tag_ids]
  hide_name:
    description:
      - Hide the WiFi name (do not broadcast the SSID). Defaults to V(false) when creating.
    type: bool
    aliases: [hide_ssid]
  client_isolation_enabled:
    description:
      - Prevent clients on this broadcast from reaching each other. Defaults to V(false) when creating.
    type: bool
  multicast_to_unicast_conversion_enabled:
    description:
      - Convert multicast traffic to unicast (multicast enhancement). Defaults to V(false) when creating.
    type: bool
  uapsd_enabled:
    description:
      - Unscheduled Automatic Power Save Delivery (U-APSD). Defaults to V(false) when creating.
    type: bool
  channel_2g_locked_to_6:
    description:
      - Lock the 2.4 GHz channel of the broadcasting devices to channel 6. Defaults to V(false) when creating.
    type: bool
  dtim_period_2g_locked_to_3:
    description:
      - Lock the 2.4 GHz DTIM period to 3. Defaults to V(false) when creating.
    type: bool
  blackout_schedule:
    description:
      - Times when the broadcast is turned off. The list is authoritative; an empty list removes the schedule.
      - An entry without times blacks out the whole day. Several entries for the same day add time ranges to that day.
    type: list
    elements: dict
    suboptions:
      day:
        description: Day of the week.
        type: str
        required: true
        choices: [mon, tue, wed, thu, fri, sat, sun]
      start_time:
        description:
          - Start of the blackout in 24-hour V(HH:MM) format. Quote it in YAML, for example V("22:00").
          - Set together with O(blackout_schedule[].end_time); omit both for the whole day.
        type: str
      end_time:
        description:
          - End of the blackout in 24-hour V(HH:MM) format. Quote it in YAML.
        type: str
        aliases: [stop_time]
  client_filtering:
    description:
      - Allow or block clients by MAC address.
    type: dict
    suboptions:
      enabled:
        description: V(false) removes the client filter.
        type: bool
        default: true
      action:
        description:
          - V(allow) only admits the listed clients, V(block) admits everyone else. Required to turn the filter on.
        type: str
        choices: [allow, block]
      mac_addresses:
        description:
          - Client MAC addresses (up to 512). The list is authoritative. Defaults to an empty list when the filter is first turned on.
        type: list
        elements: str
        aliases: [mac_address_filter]
  mdns_proxy:
    description:
      - mDNS proxy, which forwards service discovery (AirPlay, printers...) between Networks.
    type: dict
    suboptions:
      mode:
        description:
          - V(auto) proxies automatically, V(custom) uses O(mdns_proxy.policies), V(disabled) turns the proxy off.
        type: str
        required: true
        choices: [auto, custom, disabled]
      policies:
        description:
          - mDNS policies for V(custom) mode; the list is authoritative. Required when switching to V(custom).
        type: list
        elements: dict
        suboptions:
          action:
            description: Whether the policy allows or blocks mDNS.
            type: str
            required: true
            choices: [allow, block]
          services:
            description: Predefined services to allow. Only for V(allow) policies.
            type: list
            elements: str
            choices: [amazon_devices, android_tv_remote, apple_air_drop, apple_air_play, apple_file_sharing, apple_ichat, apple_itunes,
                      aqara, bose, dns_service_discovery, ftp_servers, google_chromecast, homekit, matter_network, philips_hue,
                      printers, roku, scanners, shelly, sonos, spotify_connect, ssh_servers, time_capsule, web_servers,
                      windows_file_sharing_samba]
          custom_services:
            description: Custom services to allow. Only for V(allow) policies.
            type: list
            elements: dict
            suboptions:
              name:
                description: A name for the service.
                type: str
                required: true
              type_domain:
                description: The mDNS service type, for example V(_home-assistant._tcp).
                type: str
                required: true
          bridging_networks:
            description: Networks, as names or UUIDs, whose services are bridged to this broadcast. Only for V(allow) policies.
            type: list
            elements: str
            aliases: [bridging_network_ids]
          devices:
            description:
              - Apply the policy only on these access points (names, MAC addresses or UUIDs); all when unset.
              - Mutually exclusive with O(mdns_proxy.policies[].device_tags).
            type: list
            elements: str
          device_tags:
            description:
              - Apply the policy only on access points with these device tags (names or UUIDs).
              - Mutually exclusive with O(mdns_proxy.policies[].devices).
            type: list
            elements: str
  multicast_filtering:
    description:
      - Multicast filtering policy.
    type: dict
    suboptions:
      enabled:
        description: V(false) removes multicast filtering.
        type: bool
        default: true
      action:
        description:
          - V(block) blocks multicast traffic, V(allow) only allows multicast from O(multicast_filtering.source_mac_addresses)
            (multicast from gateways is always allowed). Required to turn filtering on.
        type: str
        choices: [allow, block]
      source_mac_addresses:
        description:
          - Multicast source MAC addresses that are allowed (up to 256). Only for V(allow); defaults to an empty list.
        type: list
        elements: str
        aliases: [source_mac_address_filter]
  basic_data_rates:
    description:
      - Minimum (basic) data rates in kbps. Both rates are required when first set.
    type: dict
    suboptions:
      enabled:
        description: V(false) removes the basic data rate settings.
        type: bool
        default: true
      rate_2g:
        description: Basic data rate for 2.4 GHz, in kbps.
        type: int
        choices: [1000, 2000, 5500, 6000, 9000, 11000, 12000, 24000]
      rate_5g:
        description: Basic data rate for 5 GHz, in kbps.
        type: int
        choices: [6000, 9000, 12000, 24000]
  frequencies:
    description:
      - Bands to broadcast on, in GHz. Defaults to V(2.4) and V(5) when creating a V(standard) broadcast. Standard only.
    type: list
    elements: float
    choices: [2.4, 5, 6]
    aliases: [broadcasting_frequencies_ghz]
  band_steering_enabled:
    description:
      - Steer dual-band clients to 5 GHz. Standard only.
    type: bool
  advertise_device_name:
    description:
      - Advertise the access point name in beacon frames. Defaults to V(false) when creating. Standard only.
    type: bool
  arp_proxy_enabled:
    description:
      - Let access points answer ARP requests for clients (proxy ARP). Defaults to V(false) when creating. Standard only.
    type: bool
  bss_transition_enabled:
    description:
      - BSS transition (802.11v), which helps clients roam. Defaults to V(true) when creating. Standard only.
    type: bool
  mlo_enabled:
    description:
      - Multi-Link Operation (WiFi 7). Standard only.
    type: bool
  dns_assistance:
    description:
      - DNS assistance for clients. Standard only.
    type: dict
    suboptions:
      mode:
        description:
          - V(auto) or V(manual) DNS assistance, or V(disabled) to turn it off.
        type: str
        required: true
        choices: [auto, manual, disabled]
      servers:
        description:
          - Failover DNS servers (up to two) for V(manual) mode. Defaults to an empty list.
        type: list
        elements: str
  dtim_period_override:
    description:
      - Fixed DTIM periods per band instead of the automatic ones. All three periods are required when first set. Standard only.
    type: dict
    aliases: [dtim_period_by_frequency_ghz_override]
    suboptions:
      enabled:
        description: V(false) removes the override.
        type: bool
        default: true
      period_2g:
        description: DTIM period for 2.4 GHz, 1 to 255; must be 3 when O(dtim_period_2g_locked_to_3=true).
        type: int
      period_5g:
        description: DTIM period for 5 GHz, 1 to 255.
        type: int
      period_6g:
        description: DTIM period for 6 GHz, 1 to 255.
        type: int
  handoff_suggestions:
    description:
      - Suggest that clients with a weak signal roam to a better access point. Standard only.
    type: dict
    suboptions:
      enabled:
        description: V(false) turns handoff suggestions off.
        type: bool
        default: true
      rssi_threshold_5g:
        description: RSSI threshold in dBm for 5 GHz, -80 to -60.
        type: int
      rssi_threshold_6g:
        description: RSSI threshold in dBm for 6 GHz, -90 to -70.
        type: int
  hotspot:
    description:
      - Turn the broadcast into a hotspot with a V(captive_portal) or V(passpoint), or V(disabled) for none.
      - The portal itself is configured in the UniFi UI. Standard only.
    type: str
    choices: [captive_portal, passpoint, disabled]
extends_documentation_fragment:
  - kenmoini.unifi_network.common
  - kenmoini.unifi_network.site
  - kenmoini.unifi_network.attributes
  - kenmoini.unifi_network.attributes.state
author:
  - Ken Moini (@kenmoini)
'''

EXAMPLES = r'''
- name: Home WiFi with WPA2/WPA3 on 2.4 and 5 GHz
  kenmoini.unifi_network.wifi_broadcast:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: Home
    security:
      type: wpa2_wpa3_personal
      passphrase: "{{ home_wifi_passphrase }}"
      fast_roaming_enabled: true
    frequencies: [2.4, 5]
    band_steering_enabled: true

- name: Corporate WiFi authenticated by a RADIUS profile
  kenmoini.unifi_network.wifi_broadcast:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: Corp
    network: Staff
    security:
      type: wpa2_wpa3_enterprise
      radius_profile: Corp RADIUS
      pmf_mode: required
      nas_id_source: site_name

- name: IoT WiFi on its own Network
  kenmoini.unifi_network.wifi_broadcast:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: Things
    type: iot_optimized
    network: IoT
    hide_name: true
    client_isolation_enabled: true
    security:
      type: wpa2_personal
      passphrase: "{{ iot_wifi_passphrase }}"

- name: Guest WiFi only on upstairs access points, off at night
  kenmoini.unifi_network.wifi_broadcast:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: Guest
    network: Guest
    device_tags: [Upstairs]
    client_isolation_enabled: true
    hotspot: captive_portal
    security:
      type: open
      encryption: enhanced_open_with_transition
    blackout_schedule:
      - {day: mon, start_time: "00:00", end_time: "06:00"}
      - {day: mon, start_time: "23:00", end_time: "23:59"}
      - {day: sun}

- name: Let the IoT WiFi discover AirPlay and printers on the Home network
  kenmoini.unifi_network.wifi_broadcast:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: Things
    security:
      passphrase: "{{ iot_wifi_passphrase }}"
    mdns_proxy:
      mode: custom
      policies:
        - action: allow
          services: [apple_air_play, printers]
          bridging_networks: [Home]

- name: Preview a change (run with --check --diff)
  kenmoini.unifi_network.wifi_broadcast:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: Guest
    enabled: false
  check_mode: true
  diff: true

- name: Rotate the passphrase (always sent and reported as changed)
  kenmoini.unifi_network.wifi_broadcast:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: Home
    security:
      passphrase: "{{ new_home_wifi_passphrase }}"
    update_passphrase: always

- name: Stop broadcasting on all access points but the office ones, and drop the schedule
  kenmoini.unifi_network.wifi_broadcast:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: Guest
    devices: [Office AP, "aa:bb:cc:00:00:02"]
    blackout_schedule: []

- name: Delete a WiFi broadcast even if it is still referenced
  kenmoini.unifi_network.wifi_broadcast:
    unifi_network_url: https://192.168.1.1
    unifi_network_api_key: "{{ unifi_api_key }}"
    unifi_network_site_id: default
    name: Guest
    state: absent
    force: true
'''

RETURN = r'''
wifi_broadcast:
  description:
    - The WiFi broadcast as returned by the API after the change, or the predicted broadcast in check mode.
    - Passphrases are never included. Empty when O(state=absent).
  returned: always
  type: dict
  sample: {"id": "4b2e8f0a-3c1d-4e5f-9a7b-6c8d0e1f2a3b", "name": "Home", "type": "STANDARD", "enabled": true,
           "network": {"type": "SPECIFIC", "networkId": "497f6eca-6276-4993-bfeb-53cbbbba6f08"},
           "securityConfiguration": {"type": "WPA2_WPA3_PERSONAL", "pmfMode": "OPTIONAL", "fastRoamingEnabled": true,
                                     "wpa3FastRoamingEnabled": false,
                                     "saeConfiguration": {"anticloggingThresholdSeconds": 5, "syncTimeSeconds": 5}},
           "broadcastingFrequenciesGHz": [2.4, 5], "hideName": false, "clientIsolationEnabled": false,
           "multicastToUnicastConversionEnabled": false, "uapsdEnabled": false, "channel2gLockedTo6": false,
           "dtimPeriod2gLockedTo3": false, "advertiseDeviceName": false, "arpProxyEnabled": false,
           "bssTransitionEnabled": true, "bandSteeringEnabled": true, "metadata": {"origin": "USER_DEFINED"}}
'''

import copy
import re

from ansible_collections.kenmoini.unifi_network.plugins.module_utils.api import UnifiNetworkError
from ansible_collections.kenmoini.unifi_network.plugins.module_utils.args import state_argument_spec
from ansible_collections.kenmoini.unifi_network.plugins.module_utils.convert import pick, upper
from ansible_collections.kenmoini.unifi_network.plugins.module_utils.diff import merge, prune_none, strip_keys
from ansible_collections.kenmoini.unifi_network.plugins.module_utils.resource import StateResource, run_state_module

SECURITY_TYPES = ('open', 'wpa2_personal', 'wpa3_personal', 'wpa2_wpa3_personal',
                  'wpa2_enterprise', 'wpa3_enterprise', 'wpa2_wpa3_enterprise')
PERSONAL = ('wpa2_personal', 'wpa3_personal', 'wpa2_wpa3_personal')
ENTERPRISE = ('wpa2_enterprise', 'wpa3_enterprise', 'wpa2_wpa3_enterprise')
PMF_TYPES = ('wpa2_personal', 'wpa2_wpa3_personal', 'wpa2_enterprise', 'wpa2_wpa3_enterprise')
TRANSITION_TYPES = ('wpa2_wpa3_personal', 'wpa2_wpa3_enterprise')

# Security options and the security types they are valid for.
SECURITY_SCOPE = {
    'passphrase': PERSONAL,
    'preshared_keys': ('wpa2_personal',),
    'pmf_mode': PMF_TYPES,
    'fast_roaming_enabled': PERSONAL + ENTERPRISE,
    'wpa3_fast_roaming_enabled': TRANSITION_TYPES,
    'group_rekey_interval_seconds': PERSONAL + ENTERPRISE,
    'sae': ('wpa3_personal', 'wpa2_wpa3_personal'),
    'encryption': ('open',),
    'coa_enabled': ENTERPRISE,
    'security_mode': ('wpa3_enterprise',),
}
# Security options IoT-optimized broadcasts do not support, with their API keys.
IOT_UNSUPPORTED_SECURITY = {
    'pmf_mode': 'pmfMode', 'fast_roaming_enabled': 'fastRoamingEnabled', 'group_rekey_interval_seconds': 'groupRekeyIntervalSeconds',
}

SAE_DEFAULTS = {'anticloggingThresholdSeconds': 5, 'syncTimeSeconds': 5}
# Security fields the API requires, filled in when a security type is first set.
SECURITY_DEFAULTS = {
    'wpa3_personal': {'saeConfiguration': SAE_DEFAULTS},
    'wpa2_wpa3_personal': {'pmfMode': 'OPTIONAL', 'saeConfiguration': SAE_DEFAULTS, 'wpa3FastRoamingEnabled': False},
    'wpa2_enterprise': {'coaEnabled': False},
    'wpa3_enterprise': {'coaEnabled': False, 'securityMode': 'DEFAULT'},
    'wpa2_wpa3_enterprise': {'coaEnabled': False, 'pmfMode': 'OPTIONAL', 'wpa3FastRoamingEnabled': False},
}

# Options only standard broadcasts support, with their API keys.
STANDARD_ONLY = {
    'frequencies': 'broadcastingFrequenciesGHz', 'band_steering_enabled': 'bandSteeringEnabled',
    'advertise_device_name': 'advertiseDeviceName', 'arp_proxy_enabled': 'arpProxyEnabled',
    'bss_transition_enabled': 'bssTransitionEnabled', 'mlo_enabled': 'mloEnabled',
    'dns_assistance': 'dnsAssistanceConfiguration', 'dtim_period_override': 'dtimPeriodByFrequencyGHzOverride',
    'handoff_suggestions': 'handoffSuggestionsConfiguration', 'hotspot': 'hotspotConfiguration',
}

COMMON_DEFAULTS = {
    'enabled': True, 'hideName': False, 'clientIsolationEnabled': False, 'multicastToUnicastConversionEnabled': False,
    'uapsdEnabled': False, 'channel2gLockedTo6': False, 'dtimPeriod2gLockedTo3': False,
}
STANDARD_DEFAULTS = {
    'advertiseDeviceName': False, 'arpProxyEnabled': False, 'bssTransitionEnabled': True, 'broadcastingFrequenciesGHz': [2.4, 5],
}

FLAGS = {
    'name': 'name', 'enabled': 'enabled', 'hide_name': 'hideName', 'client_isolation_enabled': 'clientIsolationEnabled',
    'multicast_to_unicast_conversion_enabled': 'multicastToUnicastConversionEnabled', 'uapsd_enabled': 'uapsdEnabled',
    'channel_2g_locked_to_6': 'channel2gLockedTo6', 'dtim_period_2g_locked_to_3': 'dtimPeriod2gLockedTo3',
    'band_steering_enabled': 'bandSteeringEnabled', 'advertise_device_name': 'advertiseDeviceName',
    'arp_proxy_enabled': 'arpProxyEnabled', 'bss_transition_enabled': 'bssTransitionEnabled', 'mlo_enabled': 'mloEnabled',
}

MDNS_SERVICES = (
    'amazon_devices', 'android_tv_remote', 'apple_air_drop', 'apple_air_play', 'apple_file_sharing', 'apple_ichat', 'apple_itunes',
    'aqara', 'bose', 'dns_service_discovery', 'ftp_servers', 'google_chromecast', 'homekit', 'matter_network', 'philips_hue',
    'printers', 'roku', 'scanners', 'shelly', 'sonos', 'spotify_connect', 'ssh_servers', 'time_capsule', 'web_servers',
    'windows_file_sharing_samba',
)
MAC_FORMATS = ('uppercase_not_separated', 'uppercase_dash_separated', 'uppercase_colon_separated',
               'lowercase_not_separated', 'lowercase_colon_separated', 'lowercase_dash_separated')

_TIME_RE = re.compile(r'^(\d{1,2}):(\d{2})$')
_UNSET = object()


def _frequency(value):
    return int(value) if float(value).is_integer() else value


def _time(value, option):
    m = _TIME_RE.match(str(value).strip())
    if not m or int(m.group(1)) > 24 or int(m.group(2)) > 59:
        raise UnifiNetworkError('blackout_schedule %s %r must be a 24-hour time in HH:MM format; quote it in YAML, for example "06:00"'
                                % (option, value))
    return '%02d:%s' % (int(m.group(1)), m.group(2))


def _complete(fragment, current, option, mapping):
    """Fail when a sub-object whose fields are all required is first set without all of them."""
    if current:
        return fragment
    missing = ['%s.%s' % (option, opt) for opt, key in mapping if key not in fragment]
    if missing:
        raise UnifiNetworkError('%s required to set %s' % (', '.join(missing), option))
    return fragment


class WifiBroadcast(StateResource):
    path = 'wifi/broadcasts'
    result_key = 'wifi_broadcast'
    label = 'WiFi broadcast'
    create_required = {'name': 'name'}
    secret_paths = (('securityConfiguration', 'passphrase'), ('securityConfiguration', 'presharedKeys'))
    secret_update_param = 'update_passphrase'
    supports_force = True

    def create_defaults(self):
        defaults = copy.deepcopy(COMMON_DEFAULTS)
        kind = self.params['type'] or 'standard'
        defaults['type'] = upper(kind)
        if kind == 'standard':
            defaults.update(copy.deepcopy(STANDARD_DEFAULTS))
        return defaults

    def check_scope(self, kind):
        if kind == 'standard':
            return
        p = self.params
        invalid = [opt for opt in sorted(STANDARD_ONLY) if p[opt] is not None]
        invalid += ['security.%s' % opt for opt in sorted(IOT_UNSUPPORTED_SECURITY) if (p['security'] or {}).get(opt) is not None]
        if invalid:
            raise UnifiNetworkError('Option(s) %s are only valid for standard WiFi broadcasts, not %s' % (', '.join(invalid), kind))

    def to_api(self, current):
        p = self.params
        current = current or {}
        kind = p['type'] or (current.get('type') or 'standard').lower()
        self.check_scope(kind)

        desired = pick(p, FLAGS)
        if p['type']:
            desired['type'] = upper(p['type'])
        if p['security'] is not None or not current:
            desired['securityConfiguration'] = self.security(kind, current.get('securityConfiguration'))
        if p['network'] is not None:
            desired['network'] = self.network_ref(p['network'])
        if p['devices'] is not None:
            desired['broadcastingDeviceFilter'] = self.device_filter(p['devices'], None)
        if p['device_tags'] is not None:
            desired['broadcastingDeviceFilter'] = self.device_filter(None, p['device_tags'])
        if p['blackout_schedule'] is not None:
            desired['blackoutScheduleConfiguration'] = self.blackout_schedule(p['blackout_schedule'])
        if p['client_filtering'] is not None:
            desired['clientFilteringPolicy'] = self.client_filtering(p['client_filtering'], current.get('clientFilteringPolicy'))
        if p['mdns_proxy'] is not None:
            desired['mdnsProxyConfiguration'] = self.mdns_proxy(p['mdns_proxy'], current.get('mdnsProxyConfiguration'))
        if p['multicast_filtering'] is not None:
            desired['multicastFilteringPolicy'] = self.multicast_filtering(p['multicast_filtering'],
                                                                           current.get('multicastFilteringPolicy'))
        rates = p['basic_data_rates']
        if rates is not None:
            desired['basicDataRateKbpsByFrequencyGHz'] = None if not rates['enabled'] else _complete(
                pick(rates, {'rate_2g': '2.4', 'rate_5g': '5'}), current.get('basicDataRateKbpsByFrequencyGHz'),
                'basic_data_rates', (('rate_2g', '2.4'), ('rate_5g', '5')))
        self.standard_settings(desired, current)
        return desired

    # ---- security -----------------------------------------------------
    def security(self, kind, current_sec):
        s = self.params['security'] or {}
        current_sec = current_sec or {}
        current_type = (current_sec.get('type') or '').lower() or None
        sec_type = s.get('type') or current_type
        if not sec_type:
            raise UnifiNetworkError('Creating a %s requires: security.type' % self.label)
        for opt in sorted(SECURITY_SCOPE):
            if s.get(opt) is not None and sec_type not in SECURITY_SCOPE[opt]:
                raise UnifiNetworkError('Option security.%s is only valid for security type(s) %s, not %s' % (
                    opt, ', '.join(SECURITY_SCOPE[opt]), sec_type))
        replacing = sec_type != current_type

        sec = pick(s, {'passphrase': 'passphrase', 'fast_roaming_enabled': 'fastRoamingEnabled',
                       'wpa3_fast_roaming_enabled': 'wpa3FastRoamingEnabled', 'coa_enabled': 'coaEnabled'})
        if s.get('type'):
            sec['type'] = upper(s['type'])
        if s.get('pmf_mode'):
            sec['pmfMode'] = None if s['pmf_mode'] == 'disabled' else upper(s['pmf_mode'])
        if s.get('group_rekey_interval_seconds') is not None:
            sec['groupRekeyIntervalSeconds'] = s['group_rekey_interval_seconds'] or None
        if s.get('encryption'):
            sec['encryption'] = None if s['encryption'] == 'none' else upper(s['encryption'])
        if s.get('security_mode'):
            sec['securityMode'] = upper(s['security_mode'])
        if s.get('sae'):
            sec['saeConfiguration'] = pick(s['sae'], {'anti_clogging_threshold_seconds': 'anticloggingThresholdSeconds',
                                                      'sync_time_seconds': 'syncTimeSeconds'})
        if s.get('preshared_keys') is not None:
            sec['presharedKeys'] = [{'network': self.network_ref(k['network']), 'passphrase': k['passphrase']}
                                    for k in s['preshared_keys']]
        radius = self.radius(s, sec_type, None if replacing else current_sec.get('radiusConfiguration'))
        if radius is not _UNSET:
            sec['radiusConfiguration'] = radius

        if replacing:
            defaults = copy.deepcopy(SECURITY_DEFAULTS.get(sec_type, {}))
            if kind != 'standard':
                for key in IOT_UNSUPPORTED_SECURITY.values():
                    defaults.pop(key, None)
            sec = merge(defaults, sec)
            if sec_type in PERSONAL and not sec.get('passphrase') and not sec.get('presharedKeys'):
                raise UnifiNetworkError('security.passphrase is required for security type %s' % sec_type)
            if sec_type in ENTERPRISE and not sec.get('radiusConfiguration'):
                raise UnifiNetworkError('security.radius_profile is required for security type %s' % sec_type)
        return sec

    def radius(self, s, sec_type, current_radius):
        """Return the radiusConfiguration fragment, ``None`` to remove it, or ``_UNSET`` to leave it alone."""
        enterprise = sec_type in ENTERPRISE
        profile = s.get('radius_profile')
        if profile == '':
            if enterprise:
                raise UnifiNetworkError('security.radius_profile is required for security type %s' % sec_type)
            return None
        radius = {}
        if profile:
            radius['profileId'] = self.refs.resolve('radius_profile', profile)
        if s.get('nas_id') is not None:
            radius['nasId'] = {'type': 'USER_DEFINED', 'value': s['nas_id']}
        if s.get('nas_id_source'):
            radius['nasId'] = {'type': 'DERIVED', 'source': upper(s['nas_id_source'])}
        mac_format = s.get('mac_auth_format')
        if mac_format == 'disabled':
            if not enterprise:
                raise UnifiNetworkError('security.mac_auth_format=disabled is only valid for enterprise security types; '
                                        'set security.radius_profile to an empty string to turn RADIUS MAC authentication off')
            radius['macAuthenticationConfiguration'] = None
        elif mac_format:
            radius['macAuthenticationConfiguration'] = {'macAddressFormat': upper(mac_format)}
        if not radius:
            return _UNSET
        if not current_radius:
            if 'profileId' not in radius:
                raise UnifiNetworkError('security.radius_profile is required to configure RADIUS')
            defaults = {'nasId': {'type': 'DERIVED', 'source': 'DEVICE_NAME'}}
            if not enterprise:
                defaults['macAuthenticationConfiguration'] = {'macAddressFormat': 'LOWERCASE_NOT_SEPARATED'}
            radius = merge(defaults, radius)
        return radius

    # ---- references ---------------------------------------------------
    def network_ref(self, value):
        if value.lower() == 'native':
            return {'type': 'NATIVE'}
        return {'type': 'SPECIFIC', 'networkId': self.refs.resolve('network', value)}

    def device_filter(self, devices, tags):
        if devices:
            return {'type': 'DEVICES', 'deviceIds': self.refs.resolve_many('device', devices)}
        if tags:
            return {'type': 'DEVICE_TAGS', 'deviceTagIds': self.refs.resolve_many('device_tag', tags)}
        return None

    # ---- nested features ----------------------------------------------
    def blackout_schedule(self, entries):
        if not entries:
            return None
        order, ranges = [], {}
        for entry in entries:
            day = entry['day']
            if day not in ranges:
                order.append(day)
                ranges[day] = []
            if entry['start_time'] is None:
                ranges[day].append(None)
            else:
                ranges[day].append({'startTime': _time(entry['start_time'], 'start_time'),
                                    'endTime': _time(entry['end_time'], 'end_time')})
        days = []
        for day in order:
            if None in ranges[day]:
                if len(ranges[day]) > 1:
                    raise UnifiNetworkError('blackout_schedule lists %s as all day (no times) more than once or together '
                                            'with time ranges' % day)
                days.append({'day': upper(day), 'type': 'ALL_DAY'})
            else:
                days.append({'day': upper(day), 'type': 'TIME_RANGE', 'timeRanges': ranges[day]})
        return {'days': days}

    def client_filtering(self, cf, current):
        if not cf['enabled']:
            return None
        if not cf['action'] and not current:
            raise UnifiNetworkError('client_filtering.action is required to turn client filtering on')
        policy = {'action': upper(cf['action']) if cf['action'] else current['action']}
        macs = cf['mac_addresses']
        policy['macAddressFilter'] = macs if macs is not None else list((current or {}).get('macAddressFilter') or [])
        return policy

    def mdns_proxy(self, mdns, current):
        if mdns['mode'] == 'disabled':
            return None
        if mdns['mode'] == 'auto':
            if mdns['policies'] is not None:
                raise UnifiNetworkError('mdns_proxy.policies is only valid for mode custom')
            return {'mode': 'AUTO'}
        config = {'mode': 'CUSTOM'}
        if mdns['policies']:
            config['policies'] = [self.mdns_policy(pol) for pol in mdns['policies']]
        elif (current or {}).get('mode') != 'CUSTOM' or mdns['policies'] is not None:
            raise UnifiNetworkError('mdns_proxy.policies (at least one) is required for mode custom')
        return config

    def mdns_policy(self, pol):
        entry = {'action': upper(pol['action'])}
        if pol['action'] == 'block':
            extras = [opt for opt in ('services', 'custom_services', 'bridging_networks') if pol[opt] is not None]
            if extras:
                raise UnifiNetworkError('mdns_proxy.policies[].%s is only valid for allow policies' % ', '.join(extras))
        if pol['bridging_networks']:
            entry['bridgingNetworkIds'] = self.refs.resolve_many('network', pol['bridging_networks'])
        services = [{'type': 'PREDEFINED', 'name': upper(name)} for name in pol['services'] or []]
        services += [{'type': 'CUSTOM', 'name': c['name'], 'typeDomain': c['type_domain']} for c in pol['custom_services'] or []]
        if services:
            entry['serviceFilter'] = services
        device_filter = self.device_filter(pol['devices'], pol['device_tags'])
        if device_filter:
            entry['deviceFilter'] = device_filter
        return entry

    def multicast_filtering(self, mf, current):
        if not mf['enabled']:
            return None
        current = current or {}
        action = mf['action'] or (current.get('action') or '').lower()
        if not action:
            raise UnifiNetworkError('multicast_filtering.action is required to turn multicast filtering on')
        if action == 'block':
            if mf['source_mac_addresses'] is not None:
                raise UnifiNetworkError('multicast_filtering.source_mac_addresses is only valid for action allow')
            return {'action': 'BLOCK'}
        macs = mf['source_mac_addresses']
        if macs is None:
            macs = list(current.get('sourceMacAddressFilter') or []) if current.get('action') == 'ALLOW' else []
        return {'action': 'ALLOW', 'sourceMacAddressFilter': macs}

    def standard_settings(self, desired, current):
        p = self.params
        if p['frequencies'] is not None:
            desired['broadcastingFrequenciesGHz'] = [_frequency(f) for f in p['frequencies']]
        if p['hotspot']:
            desired['hotspotConfiguration'] = None if p['hotspot'] == 'disabled' else {'type': upper(p['hotspot'])}
        dns = p['dns_assistance']
        if dns is not None:
            if dns['mode'] != 'manual' and dns['servers'] is not None:
                raise UnifiNetworkError('dns_assistance.servers is only valid for mode manual')
            if dns['mode'] == 'disabled':
                desired['dnsAssistanceConfiguration'] = None
            elif dns['mode'] == 'auto':
                desired['dnsAssistanceConfiguration'] = {'mode': 'AUTO'}
            else:
                cur = current.get('dnsAssistanceConfiguration') or {}
                servers = dns['servers']
                if servers is None:
                    servers = list(cur.get('servers') or []) if cur.get('mode') == 'MANUAL' else []
                desired['dnsAssistanceConfiguration'] = {'mode': 'MANUAL', 'servers': servers}
        dtim = p['dtim_period_override']
        if dtim is not None:
            mapping = (('period_2g', '2.4'), ('period_5g', '5'), ('period_6g', '6'))
            desired['dtimPeriodByFrequencyGHzOverride'] = None if not dtim['enabled'] else _complete(
                pick(dtim, dict(mapping)), current.get('dtimPeriodByFrequencyGHzOverride'), 'dtim_period_override', mapping)
        handoff = p['handoff_suggestions']
        if handoff is not None:
            desired['handoffSuggestionsConfiguration'] = None if not handoff['enabled'] else pick(handoff, {
                'rssi_threshold_5g': 'band5GHzRssiThreshold', 'rssi_threshold_6g': 'band6GHzRssiThreshold'})

    # ---- update -------------------------------------------------------
    def update_request(self, current, desired):
        new_type = desired.get('type')
        if new_type and new_type != current.get('type'):
            # Changing the broadcast type: drop what the new type does not support, add what it requires.
            base = strip_keys(current, tuple(self.read_only_keys) + tuple(STANDARD_ONLY.values()))
            if new_type == 'STANDARD':
                base = merge(base, copy.deepcopy(STANDARD_DEFAULTS))
            elif base.get('securityConfiguration'):
                base['securityConfiguration'] = strip_keys(base['securityConfiguration'], IOT_UNSUPPORTED_SECURITY.values())
            method, body = 'PUT', prune_none(merge(base, desired))
        else:
            method, body = super(WifiBroadcast, self).update_request(current, desired)
        self.check_secrets_present(body)
        return method, body

    def check_secrets_present(self, body):
        """Refuse a full-replacement PUT that would leave a personal-security broadcast without its key.

        When the API does not return the passphrase, the merged body only carries one if the user supplied it.
        """
        sec = body.get('securityConfiguration') or {}
        sec_type = (sec.get('type') or '').lower()
        if sec_type in PERSONAL and not sec.get('passphrase') and not sec.get('presharedKeys'):
            raise UnifiNetworkError(
                'security.passphrase is required to update the %s broadcast %r: the API does not return the current '
                'passphrase and every update replaces the whole configuration. Set it on every run; it is only compared '
                'when update_passphrase=always.' % (sec_type, body.get('name')))


def argument_spec():
    psk_spec = dict(
        network=dict(type='str', required=True),
        passphrase=dict(type='str', required=True, no_log=True),
    )
    security_spec = dict(
        type=dict(type='str', choices=list(SECURITY_TYPES)),
        passphrase=dict(type='str', no_log=True),
        preshared_keys=dict(type='list', elements='dict', options=psk_spec, no_log=False),
        pmf_mode=dict(type='str', choices=['required', 'optional', 'disabled']),
        fast_roaming_enabled=dict(type='bool'),
        wpa3_fast_roaming_enabled=dict(type='bool'),
        group_rekey_interval_seconds=dict(type='int', no_log=False),
        sae=dict(type='dict', options=dict(
            anti_clogging_threshold_seconds=dict(type='int', aliases=['anticlogging_threshold_seconds']),
            sync_time_seconds=dict(type='int'),
        )),
        encryption=dict(type='str', choices=['none', 'enhanced_open', 'enhanced_open_with_transition']),
        coa_enabled=dict(type='bool'),
        security_mode=dict(type='str', choices=['default', 'high_security_192_bit']),
        radius_profile=dict(type='str'),
        nas_id=dict(type='str'),
        nas_id_source=dict(type='str', choices=['device_mac_address', 'device_name', 'site_name', 'bssid']),
        mac_auth_format=dict(type='str', choices=list(MAC_FORMATS) + ['disabled'], aliases=['mac_address_format']),
    )
    blackout_spec = dict(
        day=dict(type='str', required=True, choices=['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']),
        start_time=dict(type='str'),
        end_time=dict(type='str', aliases=['stop_time']),
    )
    mdns_policy_spec = dict(
        action=dict(type='str', required=True, choices=['allow', 'block']),
        services=dict(type='list', elements='str', choices=list(MDNS_SERVICES)),
        custom_services=dict(type='list', elements='dict', options=dict(
            name=dict(type='str', required=True),
            type_domain=dict(type='str', required=True),
        )),
        bridging_networks=dict(type='list', elements='str', aliases=['bridging_network_ids']),
        devices=dict(type='list', elements='str'),
        device_tags=dict(type='list', elements='str'),
    )
    spec = state_argument_spec()
    spec.update(
        name=dict(type='str', aliases=['ssid']),
        force=dict(type='bool', default=False),
        type=dict(type='str', choices=['standard', 'iot_optimized']),
        enabled=dict(type='bool'),
        security=dict(type='dict', options=security_spec, mutually_exclusive=[('nas_id', 'nas_id_source')]),
        update_passphrase=dict(type='str', default='on_create', choices=['on_create', 'always'], no_log=False),
        network=dict(type='str'),
        devices=dict(type='list', elements='str', aliases=['device_ids']),
        device_tags=dict(type='list', elements='str', aliases=['device_tag_ids']),
        hide_name=dict(type='bool', aliases=['hide_ssid']),
        client_isolation_enabled=dict(type='bool'),
        multicast_to_unicast_conversion_enabled=dict(type='bool'),
        uapsd_enabled=dict(type='bool'),
        channel_2g_locked_to_6=dict(type='bool'),
        dtim_period_2g_locked_to_3=dict(type='bool'),
        blackout_schedule=dict(type='list', elements='dict', options=blackout_spec, required_together=[('start_time', 'end_time')]),
        client_filtering=dict(type='dict', options=dict(
            enabled=dict(type='bool', default=True),
            action=dict(type='str', choices=['allow', 'block']),
            mac_addresses=dict(type='list', elements='str', aliases=['mac_address_filter']),
        )),
        mdns_proxy=dict(type='dict', options=dict(
            mode=dict(type='str', required=True, choices=['auto', 'custom', 'disabled']),
            policies=dict(type='list', elements='dict', options=mdns_policy_spec, mutually_exclusive=[('devices', 'device_tags')]),
        )),
        multicast_filtering=dict(type='dict', options=dict(
            enabled=dict(type='bool', default=True),
            action=dict(type='str', choices=['allow', 'block']),
            source_mac_addresses=dict(type='list', elements='str', aliases=['source_mac_address_filter']),
        )),
        basic_data_rates=dict(type='dict', options=dict(
            enabled=dict(type='bool', default=True),
            rate_2g=dict(type='int', choices=[1000, 2000, 5500, 6000, 9000, 11000, 12000, 24000]),
            rate_5g=dict(type='int', choices=[6000, 9000, 12000, 24000]),
        )),
        frequencies=dict(type='list', elements='float', choices=[2.4, 5, 6], aliases=['broadcasting_frequencies_ghz']),
        band_steering_enabled=dict(type='bool'),
        advertise_device_name=dict(type='bool'),
        arp_proxy_enabled=dict(type='bool'),
        bss_transition_enabled=dict(type='bool'),
        mlo_enabled=dict(type='bool'),
        dns_assistance=dict(type='dict', options=dict(
            mode=dict(type='str', required=True, choices=['auto', 'manual', 'disabled']),
            servers=dict(type='list', elements='str'),
        )),
        dtim_period_override=dict(type='dict', aliases=['dtim_period_by_frequency_ghz_override'], options=dict(
            enabled=dict(type='bool', default=True),
            period_2g=dict(type='int'),
            period_5g=dict(type='int'),
            period_6g=dict(type='int'),
        )),
        handoff_suggestions=dict(type='dict', options=dict(
            enabled=dict(type='bool', default=True),
            rssi_threshold_5g=dict(type='int'),
            rssi_threshold_6g=dict(type='int'),
        )),
        hotspot=dict(type='str', choices=['captive_portal', 'passpoint', 'disabled']),
    )
    return spec


def main():
    run_state_module(WifiBroadcast, argument_spec(), required_one_of=[('name', 'id')],
                     mutually_exclusive=[('devices', 'device_tags')])


if __name__ == '__main__':
    main()
