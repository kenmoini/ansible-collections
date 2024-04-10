#!powershell
#########################################################################################################################################
# kenmoini.hyperv.vhd_info - Get the configuration information of Virtual Hard Disks from a Windows Server running Hyper-V
#########################################################################################################################################

# WANT_JSON
# POWERSHELL_COMMON

#Requires -Module Ansible.ModuleUtils.Legacy
Set-StrictMode -Version 2

#########################################################################################################################################
# Functions
#########################################################################################################################################

Function VHD-Info {
  $CheckVHD = Get-VHD -path $path -ErrorAction SilentlyContinue
  
  if ($CheckVHD) {
    $cmd="Get-VHD -Path $path | ConvertTo-Json -Compress"
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

$path = Get-AnsibleParam $params "path" -type "str" -FailIfEmpty $true -emptyattributefailmessage "missing required argument: path"

#########################################################################################################################################
# State Action Switches
#########################################################################################################################################

Try {
  VHD-Info
  Exit-Json $result;
} Catch {
  Fail-Json $result $_.Exception.Message
}
