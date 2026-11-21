# Known issues

Small problems in `kenmoini.unifi_network` 2.0.0 that are known but not fixed yet. None of them should affect a
typical playbook, and most have a simple workaround.

## Changing a network's management type or an ACL rule's type keeps the old variant's fields

**Affects:** `network`, `acl_rule`

Changing `management` on an existing network (for example from `gateway` to `switch`), or `type` on an existing ACL
rule (from `ipv4` to `mac`), keeps the fields that only belong to the old variant in the update. For a network these
are `zoneId`, `internetAccessEnabled`, `mdnsForwardingEnabled`, IPv6 and outbound NAT settings; for an ACL rule they are
`protocolFilter` or `networkIdFilter`. The controller may reject the update, or ignore those fields.
`wifi_broadcast` already strips such fields when its `type` changes; `network` and `acl_rule` should do the same.

**Workaround:** delete the object and create it again with the new type.

## An empty `description` may report a change on every run

**Affects:** `acl_rule`, `firewall_policy`

`description: ''` is turned into "no description", and an absent value is treated as matching. If the API stores and
returns an empty string (`""`) instead of omitting the field, the comparison sees a difference and every run reports
`changed`. The empty-value check in `plugins/module_utils/diff.py` (`_is_empty`) does not treat `''` as empty.

**Workaround:** leave `description` out instead of setting it to an empty string.

## `hotspot_voucher`: `count` is not range-checked, and there is no `filters` option for deletion

**Affects:** `hotspot_voucher`

The API accepts 1 to 1000 vouchers per request, but `count` is not validated, so an out-of-range value only fails
when the API rejects it. The plan also called for `filters` when deleting vouchers (`state: absent`); only `id`, `name`
and `only_expired` are available.

**Workaround:** keep `count` between 1 and 1000. To delete by other criteria, list the vouchers with
`hotspot_voucher_info` and `filters`, then delete each one by `id`.

## Two modules claim diff support they don't have

**Affects:** `hotspot_voucher`, `client_guest_access`

Both modules use the `attributes.state` documentation fragment, which says diff mode is fully supported, while their
notes say diff mode is not supported. The notes are correct: neither module returns a `diff`. The modules should use
an attributes fragment that marks diff mode as unsupported.

## The two time parsers behave differently

**Affects:** `wifi_broadcast` (`blackout_schedule`), `firewall_policy` (`schedule`)

- The WiFi blackout schedule accepts an hour of `24` (so `24:30` passes validation and is sent to the API), while the
  firewall schedule only accepts hours up to 23.
- YAML 1.1 reads an unquoted `17:30` as the number 1050. `firewall_policy` converts such numbers back to `17:30`, but
  `wifi_broadcast` rejects them with an error asking you to quote the time.

**Workaround:** always quote times, for example `start_time: "06:00"`, and use hours 00 to 23.

## The unit tests need ansible-core 2.19 or newer

**Affects:** development only

`tests/unit/plugins/utils.py` uses `ansible.module_utils.testing.patch_module_args`, which was added in ansible-core
2.19. The collection itself supports ansible-core 2.15 and newer, but `ansible-test units` fails to import the tests on
2.15 to 2.18.

**Workaround:** run the unit tests with ansible-core 2.19 or newer. A fix would fall back to the older way of setting
module arguments (patching `ansible.module_utils.basic._ANSIBLE_ARGS`) when `patch_module_args` is not available.

## Two redirect warnings describe the wrong return type

**Affects:** the deprecated `device_statistics` and `network_references` module names

In `meta/runtime.yml`, the deprecation warning for these two redirects says the new module "returns a list of items
rather than the raw API page". `device_statistics_info` and `network_references_info` actually return a dict
(`statistics` and `network_references`), as the old modules did. Only the warning text is wrong.

## `report_flow_enabled` on some built-in firewall policies reports a change every run

**Affects:** `firewall_policy`

For system-defined policies the module only changes `logging_enabled` and `report_flow_enabled`, through a partial
update. According to the API specification, the controller ignores `report_flow_enabled` on the predefined "Allow
Return Traffic" policies and on the predefined policies that only allow multicast or IPv6 neighbor discovery traffic
(those are never reported). The value never changes, so every run reports `changed`.

**Workaround:** don't set `report_flow_enabled` on those built-in policies.
