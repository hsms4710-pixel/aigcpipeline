# keep-awake.ps1 - block Modern Standby sleep (SetThreadExecutionState, no admin needed)
$sig = @"
[DllImport("kernel32.dll", CharSet = CharSet.Auto, SetLastError = true)]
public static extern uint SetThreadExecutionState(uint esFlags);
"@
$type = Add-Type -MemberDefinition $sig -Name Win32SetExec -Namespace Win32 -PassThru
$ES_CONTINUOUS = 0x80000000
$ES_SYSTEM_REQUIRED = 0x00000001
$ES_DISPLAY_REQUIRED = 0x00000002
[void]$type::SetThreadExecutionState([uint32]2147483651)
Write-Output "keep-awake active (PID $PID)"
try {
  while ($true) {
    Start-Sleep -Seconds 30
    [void]$type::SetThreadExecutionState([uint32]2147483651)
  }
} finally {
  [void]$type::SetThreadExecutionState([uint32]2147483648)
  Write-Output "keep-awake released"
}
