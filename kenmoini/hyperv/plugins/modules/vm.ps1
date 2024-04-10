#!powershell

#########################################################################################################################################
# kenmoini.hyperv.vm - Create/Delete Virtual Machines from a Windows Server running Hyper-V
#########################################################################################################################################

# WANT_JSON
# POWERSHELL_COMMON

#Requires -Module Ansible.ModuleUtils.Legacy
Set-StrictMode -Version 2

#########################################################################################################################################
# Functions
#########################################################################################################################################

Function VM-Create {
  $CheckVM = Get-VM -name $name -ErrorAction SilentlyContinue
  
  if (!$CheckVM) {
    $cmd="New-VM -Name '$name'"

    if ($memory) {
      $cmd=$cmd + " -MemoryStartupBytes $memory"
    } else {
      Fail-Json $result "Memory is required when creating a VM"
    }

    if ($diskPath) {
      # Check to see if the disk path exists
      if (!(Test-Path $diskPath -PathType Leaf)) {
        # Path does not exist, create it if we are also supplied a diskSize
        if ($diskSize) {
          $cmd=$cmd + " -NewVHDPath $diskPath -NewVHDSizeBytes $diskSize"
        } else {
          Fail-Json $result "diskPath does not exist and no diskSize was supplied!"
        }
      } else {
        # Path exists, pass it as an existing VHD for the VM
        $cmd=$cmd + " -VHDPath $diskPath"
      }
    }

    if ($generation) {
      $cmd=$cmd + " -Generation $generation"
    }

    if ($bootDevice) {
      $cmd=$cmd + " -BootDevice $bootDevice"
    }

    # Next command chain for setting Processors
    if ($cpu) {
      $cmd=$cmd + "; Set-VMProcessor '$name' -Count $cpu"
    }

    # Next command chain for setting CDROM ISO
    if ($cdrom) {
      # Check to see if the ISO exists
      if (!(Test-Path $cdrom -PathType Leaf)) {
        # Path does not exist, error out
        Fail-Json $result "cdrom does not exist, must exist on host!"
      } else {
        $cmd=$cmd + "; Add-VMDvdDrive -VMName '$name' -Path '$cdrom'"
      }
    }

    # Next command chain for setting Processor Live Migration
    if ($liveMigration) {
      $cmd=$cmd + '; Set-VMProcessor "$name" -CompatibilityForMigrationEnabled $true'
    }

    # Next command chain for setting Processor Nested Virtualization
    if ($nestedVirtualization) {
      $cmd=$cmd + '; Set-VMProcessor "$name" -ExposeVirtualizationExtensions $true'
    }

    # Next command attach the network
    if ($networkSwitch) {
      $cmd=$cmd + "; Add-VMNetworkAdapter -VMName '$name' -SwitchName '$networkSwitch'"
    }

    $result.cmd_used = $cmd
    $result.changed = $true

    if (!$check_mode) {
      $results = invoke-expression $cmd
      # Get the information about the VM and return it as JSON
      $result.json = Get-VM -Name "$name" | ConvertTo-Json -Compress
    }
  } else {
    # [TODO] VM Exists, check to see if the configuration is the same
    $result.changed = $false
  }
}

Function VM-Start {
  $CheckVM = Get-VM -name $name -ErrorAction SilentlyContinue
  
  if ($CheckVM) {
    $cmd="Start-VM -Name $name"

    $result.cmd_used = $cmd
    $result.changed = $true

    if (!$check_mode) {
      $results = invoke-expression $cmd
    }
  } else {
    $result.changed = $false
  }
}

Function VM-Stop {
  $CheckVM = Get-VM -name $name -ErrorAction SilentlyContinue
  
  if ($CheckVM) {
    $cmd="Stop-VM -Name $name"

    if ($force) {
      $cmd="$cmd -TurnOff"
    }

    $result.cmd_used = $cmd
    $result.changed = $true

    if (!$check_mode) {
      $results = invoke-expression $cmd
    }
  } else {
    $result.changed = $false
  }
}

Function VM-Delete {
  $CheckVM = Get-VM -name $name -ErrorAction SilentlyContinue
  
  if ($CheckVM) {
    $cmd="Stop-VM -Name $name -TurnOff; Remove-VM -Name $name -Force"
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

$force = Get-AnsibleParam $params "force" -type "bool" -Default $null
$cpu = Get-AnsibleParam $params "cpu" -type "int" -Default $null
$memory = Get-AnsibleParam $params "memory" -type "str" -Default $null
$generation = Get-AnsibleParam $params "generation" -type "int" -Default "1"

$networkSwitch = Get-AnsibleParam $params "networkSwitch" -type "str" -aliases "network" -Default $null

$diskPath = Get-AnsibleParam $params "diskPath" -type "str" -aliases "path" -Default $null
$diskSize = Get-AnsibleParam $params "diskSize" -type "str" -aliases "size" -Default $null
$bootDevice = Get-AnsibleParam $params "bootDevice" -type "str" -Default $null
$cdrom = Get-AnsibleParam $params "cdrom" -type "str" -Default $null

$liveMigration = Get-AnsibleParam $params "liveMigration" -type "bool" -Default $null
$nestedVirtualization = Get-AnsibleParam $params "nestedVirtualization" -type "bool" -Default $null

#########################################################################################################################################
# State Action Switches
#########################################################################################################################################

Try {
  switch ($state) {
    "present" {VM-Create}
    "absent" {VM-Delete}
    "stopped" {VM-Stop}
    "poweredoff" {VM-Stop}
    "started" {VM-Start}
    "poweredon" {VM-Start}
  }
  Exit-Json $result;
} Catch {
  Fail-Json $result $_.Exception.Message
}
