#!powershell
#########################################################################################################################################
# kenmoini.hyperv.vmswitch_info - Get the configuration information of Virtual Switches from a Windows Server running Hyper-V
#########################################################################################################################################

# WANT_JSON
# POWERSHELL_COMMON

#Requires -Module Ansible.ModuleUtils.Legacy
Set-StrictMode -Version 2

#########################################################################################################################################
# Functions
#########################################################################################################################################

Function VirtualSwitch-Info {
  $CheckVirtualSwitch = Get-VMSwitch -name $name -ErrorAction SilentlyContinue
  
  if ($CheckVirtualSwitch) {
    $cmd="Get-VMSwitch -name $name | ConvertTo-Json -Compress"
    $result.cmd_used = $cmd
    $result.changed = $true

    if (!$check_mode) {
      $results = invoke-expression $cmd
      $result.json = $results
    }
  } else {
    $result.changed = $false
  }
}

#########################################################################################################################################
# Parameter Setup
#########################################################################################################################################

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false
$result = @{
  changed = $false
  cmd_used = ""
}

$debug_level = Get-AnsibleParam -obj $params -name "_ansible_verbosity" -type "int"
$debug = $debug_level -gt 2

$name = Get-AnsibleParam $params "name" -type "str" -FailIfEmpty $true -emptyattributefailmessage "missing required argument: name"

#########################################################################################################################################
# State Action Switches
#########################################################################################################################################

Try {
  VirtualSwitch-Info
  Exit-Json $result;
} Catch {
  Fail-Json $result $_.Exception.Message
}
