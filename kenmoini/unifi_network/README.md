# Ansible Collection - kenmoini.unifi_network

> Work In Progress - [Issues](https://github.com/kenmoini/ansible-collections/issues) and [Pull Requests](https://github.com/kenmoini/ansible-collections/tree/main/kenmoini/unifi_network) are welcome.

This collection works against your local Unifi Network API endpoint, not the cloud service.

It manages a UniFi Network application (UniFi OS consoles such as the UDM, UCG and UDR, or a self-hosted UniFi OS Server)
through its official **Network Integration API** (built against API v11.0.97). The modules are idempotent and declarative:
you describe the state you want, and the modules read the current state, change only what differs, and support
`--check` and `--diff`. If you need to, you can route the requests through the UniFi cloud connector with
`unifi_network_api_path` (see [Connecting](#connecting)).

## Requirements

- ansible-core 2.15 or newer, Python 3.9 or newer. There are no extra Python dependencies.
- A UniFi Network application with the Integration API, and an API key created under
  **Settings > Control Plane > Integrations** (or **Integrations** in the site settings of older versions).

## Installation

```shell
ansible-galaxy collection install kenmoini.unifi_network
```

## Connecting

Every module takes these options. Each can also be set through an environment variable, or once per play with
`module_defaults` and the `group/kenmoini.unifi_network.fullset` action group.

| Option | Environment variable | Purpose |
| --- | --- | --- |
| `unifi_network_url` | `UNIFI_NETWORK_URL`, `UNIFI_NETWORK_API` | Console URL, for example `https://192.168.1.1` |
| `unifi_network_api_key` | `UNIFI_NETWORK_API_KEY` | API key |
| `unifi_network_site_id` | `UNIFI_NETWORK_SITE_ID`, `UNIFI_NETWORK_SITE` | Site UUID, name, or internal reference (`default`) |
| `unifi_network_skip_tls_verify` | `UNIFI_NETWORK_SKIP_TLS_VERIFY` | Accept the console's self-signed certificate |
| `unifi_network_api_path` | `UNIFI_NETWORK_API_PATH` | API path below the URL (default `/proxy/network/integrations`) |
| `unifi_network_timeout` | `UNIFI_NETWORK_TIMEOUT` | Request timeout in seconds (default 30) |

```yaml
- hosts: localhost
  gather_facts: false
  module_defaults:
    group/kenmoini.unifi_network.fullset:
      unifi_network_url: https://192.168.1.1
      unifi_network_api_key: "{{ vault_unifi_api_key }}"
      unifi_network_site_id: default
      unifi_network_skip_tls_verify: true
  tasks:
    - kenmoini.unifi_network.application_info:
```

To go through the UniFi cloud connector instead of the local console, set `unifi_network_url: https://api.ui.com` and
`unifi_network_api_path: /v1/connector/consoles/<console id>/proxy/network/integration`.

## Modules

### State modules (idempotent, check mode, `--diff`)

| Module | Manages |
| --- | --- |
| `network` | Networks (VLANs) with IPv4, DHCP, NAT and IPv6 settings |
| `firewall_zone` | Custom firewall zones and the zone membership of Networks |
| `firewall_policy` | Zone-based firewall policies |
| `firewall_policy_ordering` | The order of user-defined policies between two zones |
| `acl_rule` | Switch ACL rules (IPv4 and MAC) |
| `acl_rule_ordering` | The priority order of ACL rules |
| `dns_policy` | Local DNS records (A, AAAA, CNAME, MX, SRV, TXT) and domain forwarding |
| `traffic_matching_list` | Reusable IP address and port lists |
| `wifi_broadcast` | WiFi networks (SSIDs) |
| `hotspot_voucher` | Guest Hotspot vouchers (ensures N valid vouchers exist; cleans up) |
| `device` | Adopting and removing devices |
| `client_guest_access` | Authorizing and unauthorizing guest clients |

### Action modules

`device_action` (restart a device) and `port_action` (power cycle a PoE port) are imperative. They always report a
change, and in check mode they only verify that the target exists.

### Info modules (read-only, run in check mode)

`site_info`, `application_info`, `device_info`, `pending_device_info`, `device_statistics_info`, `device_tag_info`,
`client_info`, `network_info`, `network_references_info`, `firewall_zone_info`, `firewall_policy_info`,
`firewall_policy_ordering_info`, `acl_rule_info`, `acl_rule_ordering_info`, `dns_policy_info`,
`traffic_matching_list_info`, `wifi_broadcast_info`, `hotspot_voucher_info`, `radius_profile_info`, `vpn_server_info`,
`site_to_site_tunnel_info`, `wan_interface_info`, `lag_info`, `mc_lag_domain_info`, `switch_stack_info`,
`country_info`, `dpi_application_info`, `dpi_category_info`.

Run `ansible-doc kenmoini.unifi_network.<module>` for the full options and examples of each module.

## How idempotency works

The state modules behave like any other Ansible module rather than wrapping single API calls. You describe the state you
want; the module works out what, if anything, has to change:

- **Objects are found by a natural key.** That is usually `name`, `type` + `domain` for DNS policies (the domain is
  compared case-insensitively), and the MAC address for devices. Set `id` instead to target a specific object, which also
  lets you rename it. When several objects match, the module fails and lists their UUIDs instead of guessing.
- **Extra reads instead of guesses.** A run costs a few read calls before any write: one to find the object by its
  natural key, one to fetch the full object (list endpoints only return a summary), and one per name used to reference
  another object. Lookups are cached for the rest of the task. Nothing is written when nothing differs.
- **Only the options you set are managed.** The module reads the object, merges your options into it, and compares.
  If nothing differs, it reports `changed: false` and makes no write. The API replaces whole objects on update, so the
  module always sends the merged object, and settings you did not mention (including ones changed in the UniFi UI) are kept.
- **Lists are authoritative.** `networks`, `items`, `ports` and similar lists are replaced, not appended to, and order does
  not matter unless it is meaningful (DNS server order, for example). `firewall_zone` has `append: true` for adding
  Networks.
- **Optional features are switched off explicitly**, for example `dhcp_guarding: {enabled: false}`, `ipv6: {enabled: false}`,
  `dhcp: {mode: none}`, or an empty list such as `protocols: []`. Leaving an option out never removes anything.
- **Changing a variant replaces it.** For example, switching DHCP from `server` to `relay`, or a firewall source from
  networks to IP addresses, drops the settings of the old variant instead of leaving them stale.
- **References take names or UUIDs**, for example `zone: Internal`, `networks: [IoT]`, `device: Core Switch`, or
  `ip_address_list: Admin Workstations`. Names cost one lookup each and are cached for the rest of the task.
- **Secrets are not read back.** WiFi passphrases are never compared, because the API cannot be relied on to return them. Because every
  update replaces the whole configuration, pass the passphrase on every run of a WPA personal broadcast; it is sent along
  with any change (the module refuses to update without it). Set `update_passphrase: always` to force a rotation,
  which reports a change on every run, like `update_password` in `ansible.builtin.user`. `wifi_broadcast_info` strips
  passphrases from its results.
- **System-defined objects are protected.** You can change the Networks of a system zone and the logging of a
  system policy, but you cannot rename or delete them. Derived ACL rules are read-only.
- **Check mode and diff.** With `--check` the module returns the object it would create or update, and `--diff` shows
  the object before and after.

```yaml
- name: IoT VLAN with DHCP in its own firewall zone
  kenmoini.unifi_network.network:
    name: IoT
    management: gateway
    vlan_id: 30
    ipv4:
      host_ip_address: 10.30.0.1
      prefix_length: 24
      dhcp:
        mode: server
        ip_address_range: {start: 10.30.0.100, stop: 10.30.0.200}

- name: Put it in an Untrusted zone
  kenmoini.unifi_network.firewall_zone:
    name: Untrusted
    networks: [IoT]

- name: Let IoT reach the Home Assistant host on its API port only
  kenmoini.unifi_network.firewall_policy:
    name: IoT to Home Assistant
    action: allow
    source:
      zone: Untrusted
      networks: [IoT]
    destination:
      zone: Internal
      ip_addresses: [192.168.1.50]
      ports: [8123]

- name: Local DNS name for the NAS
  kenmoini.unifi_network.dns_policy:
    type: a
    domain: nas.home.arpa
    ipv4_address: 192.168.1.20
    ttl_seconds: 300
```

## How filtering works

Each `<resource>_info` module returns a list under the plural resource name (for example `networks`). It fetches every
page (200 items per request), because the API returns only 25 items per page by default and earlier versions of these
modules stopped there. The filtering itself happens in the API, so only matching items are transferred. To narrow the
results:

- `id`: one object (an empty list if it does not exist). It cannot be combined with `name` or filters.
- `name`: an exact name match. It is combined with `filters` or `filters_raw` using AND.
- `filters`: one condition, or a list of conditions, each with `property`, `function` and `value`.
  - Values keep their YAML type: booleans and numbers (`true`, `10`) are sent unquoted, while strings, UUIDs and
    timestamps are quoted.
  - `in`, `notIn` and `containsAny`/`containsAll`/`containsExactly` take a list; `isNull`/`isNotNull`/`isEmpty` take no
    value. The module fails before calling the API if a value is missing or not allowed.
  - `like` matches patterns where `*` matches any characters and `.` one character.
  - Each module's documentation lists its filterable properties and the functions each one allows.
- `filters_match`: `all` (AND, the default) or `any` (OR) for a list of conditions.
- `filters_raw`: a raw expression for anything else, for example `not(name.like('guest*'))` or
  `and(vlanId.ge(10),or(enabled.eq(false),name.eq('IoT')))`. It cannot be combined with `filters`.
- `limit`: the maximum number of items to return.

Names containing a quote or a backslash are matched after listing instead of in the API filter, because the API's
escaping for those characters has not been verified.

```yaml
- name: VLANs above 10, plus the IoT and Cameras networks
  kenmoini.unifi_network.network_info:
    filters_match: any
    filters:
      - {property: vlanId, function: gt, value: 10}
      - {property: name, function: in, value: [IoT, Cameras]}
  register: r

- ansible.builtin.debug:
    msg: "{{ r.networks | map(attribute='name') | list }}"
```

## Upgrading from 1.x

- Plural info modules were folded into singular ones (`networks_info` became `network_info`, `adopted_devices_info`
  became `device_info`, and so on), and `pending_devices`, `device_statistics` and `network_references` gained an `_info`
  suffix. The old names still work through redirects with a deprecation warning until 3.0.0.
- Info modules now return a plain list, for example `result.networks[0]` instead of `result.networks_info.data[0]`.
- The `requests` library is no longer needed.

See [`changelogs/fragments`](changelogs/fragments) for the full list of changes.

## Known issues

Small problems that are known but not fixed yet, with workarounds, are listed in [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md).

## Development

- The OpenAPI specification the modules are built from is in [`docs/api`](docs/api).
- Unit tests (pytest, with an in-memory fake of the API) live in `tests/unit`. Run them with `ansible-test units`, or
  directly with pytest from an `ansible_collections/kenmoini/unifi_network` checkout.
- The playbooks in [`playbooks`](playbooks) exercise the modules against a real controller.
  `test-state-modules.yaml` creates, re-runs, updates and deletes throwaway `ansible-test-*` objects to check idempotency.
