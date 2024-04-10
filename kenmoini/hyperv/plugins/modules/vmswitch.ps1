#!powershell
#########################################################################################################################################
# kenmoini.hyperv.vmswitch - Create/Delete Virtual Switches from a Windows Server running Hyper-V
#########################################################################################################################################

# WANT_JSON
# POWERSHELL_COMMON

#Requires -Module Ansible.ModuleUtils.Legacy
Set-StrictMode -Version 2

#########################################################################################################################################
# Functions
#########################################################################################################################################

Function VirtualSwitch-Create {
  #Check If the VirtualSwitch already exists
  $CheckVirtualSwitch = Get-VMSwitch -name $name -ErrorAction SilentlyContinue
  
  if (!$CheckVirtualSwitch) {
    $cmd = "New-VMSwitch -Name $name"
    
    if ($switchType) {
      $cmd += " -SwitchType $switchType"
    } else {
      Fail-Json $result "switchType is required when creating a VirtualSwitch"
    }
    
    if ($adapterName) {
      $cmd += " -NetAdapterName '$adapterName'"
    } else {
      Fail-Json $result "adapterName is required when creating a VirtualSwitch"
    }
    
    if ($allowManagementOS) {
      if ($allowManagementOS -eq "enabled") {
        $b = $true
        $cmd += ' -AllowManagementOS $b '
      }
      if ($allowManagementOS -eq "disabled") {
        $b = $false
        $cmd += ' -AllowManagementOS $b '
      }
    }

    $result.cmd_used = $cmd
    $result.changed = $true
    
    if (!$check_mode) {
      $results = invoke-expression -Command "$cmd"

      # Get the information about the VMSwitch and return it as JSON
      $result.json = Get-VMSwitch -Name "$name" | ConvertTo-Json -Compress
    }
  } else {
    $result.changed = $false
  }
}

Function VirtualSwitch-Delete {
  $CheckVirtualSwitch = Get-VMSwitch -name $name -ErrorAction SilentlyContinue
  
  if ($CheckVirtualSwitch) {
    $cmd="Remove-VMSwitch -Name $name -Force"
    $result.cmd_used = $cmd
    $result.changed = $true

    if (!$check_mode) {
      $results = invoke-expression $cmd
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
$state = Get-AnsibleParam $params "state" -type "str" -FailIfEmpty $true -emptyattributefailmessage "missing required argument: state"
$switchType = Get-AnsibleParam $params "switchType" -type "str" -aliases "type" -Default $null
$adapterName = Get-AnsibleParam $params "adapterName" -type "str" -aliases "adapter" -Default $null
$allowManagementOS = Get-AnsibleParam $params "allowManagementOS" -type "string" -Default $null

#########################################################################################################################################
# State Action Switches
#########################################################################################################################################

Try {
  switch ($state) {
    "present" {VirtualSwitch-Create}
    "absent" {VirtualSwitch-Delete}
  }
  Exit-Json $result;
} Catch {
  Fail-Json $result $_.Exception.Message
}
