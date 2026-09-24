# DynSMSI stage-3 monitor, local side. Windows Task Scheduler runs this every 5 h (task "vanda-stage3-monitor-5h").
# 1. runs /scratch/.../Dynamic_SMSI_stage3_units_CH4_20260924/monitor/monitor_stage3.py on the Vanda login node
#    (all mechanical PBS actions happen there);
# 2. stores the report and the remote state here, appends actions to SUBMISSION_stage3.md, shows a toast;
# 3. ATTENTION items -> claude_takeover_stage3.ps1 in the background: the Claude Code CLI (headless) handles them
#    (user 2026-09-24: monitor and operate through the CLI), unless the same items were already handled;
# 4. DONE -> one more CLI run to finalise and sync (handoff, memory, GitHub), then the task disables itself.
# Windows PowerShell 5.1 compatible; ASCII only (report text is UTF-8 from the server).
$ErrorActionPreference = 'Continue'
$env:PSModulePath = [Environment]::GetEnvironmentVariable('PSModulePath', 'Machine')   # do not inherit PowerShell 7 module paths
function Sha256File([string]$p) { $s = [Security.Cryptography.SHA256]::Create(); try { -join ($s.ComputeHash([IO.File]::ReadAllBytes($p)) | ForEach-Object { $_.ToString('X2') }) } finally { $s.Dispose() } }
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$Here     = Split-Path -Parent $MyInvocation.MyCommand.Path
$Stage    = Split-Path -Parent $Here
$SubMd    = Join-Path $Stage 'SUBMISSION_stage3.md'
$NextFile = Join-Path $Stage 'NEXT_CHECK.txt'
$LocalSt  = Join-Path $Here 'local_state.json'
$TaskName = 'vanda-stage3-monitor-5h'
$Remote   = 'python3 /scratch/junbotong/Dynamic_SMSI_stage3_units_CH4_20260924/monitor/monitor_stage3.py'
$RemoteSt = 'cat /scratch/junbotong/Dynamic_SMSI_stage3_units_CH4_20260924/monitor/state.json'
$Utf8     = New-Object System.Text.UTF8Encoding($false)
$Stamp    = Get-Date -Format 'yyyyMMdd_HHmm'

function Show-Toast([string]$Title, [string]$Body) {
    try {
        [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
        [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
        $t = [Security.SecurityElement]::Escape($Title); $b = [Security.SecurityElement]::Escape($Body)
        $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
        $xml.LoadXml("<toast><visual><binding template=`"ToastGeneric`"><text>$t</text><text>$b</text></binding></visual></toast>")
        $app = '{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe'
        [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($app).Show((New-Object Windows.UI.Notifications.ToastNotification $xml))
    } catch { }
}

$ls = @{ ssh_fail = 0; last_ok = '' }
if (Test-Path $LocalSt) {
    try { $j = [IO.File]::ReadAllText($LocalSt, [Text.Encoding]::UTF8) | ConvertFrom-Json; $ls.ssh_fail = [int]$j.ssh_fail; $ls.last_ok = "$($j.last_ok)" } catch { }
}
function Save-LocalState { [IO.File]::WriteAllText($LocalSt, ($ls | ConvertTo-Json -Compress), $Utf8) }

$raw = & ssh -o BatchMode=yes -o ConnectTimeout=30 -o ServerAliveInterval=30 vanda $Remote 2>&1 |
       Where-Object { $_ -notmatch 'post-quantum|store now|openssh.com/pq|Authorized users' } | Out-String

if ($raw -notmatch '===REPORT===') {
    # SSH failure is not compute failure (maintenance, login-node or network trouble): report, never act.
    $ls.ssh_fail += 1; Save-LocalState
    $msg = "# Vanda stage-3 monitor $(Get-Date -Format 'yyyy-MM-dd HH:mm') SGT`r`n`r`nssh/remote monitor FAILED ($($ls.ssh_fail) in a row):`r`n`r`n$raw"
    [IO.File]::WriteAllText((Join-Path $Here 'status_latest.md'), $msg, $Utf8)
    [IO.File]::AppendAllText((Join-Path $Here 'monitor_local.log'), "$msg`r`n`r`n", $Utf8)
    $last = ($raw.Trim() -split "`n" | Select-Object -Last 1)
    if ($ls.ssh_fail -ge 3) { Show-Toast "Vanda unreachable $($ls.ssh_fail)x in a row" "maintenance? last ok: $($ls.last_ok)  $last" }
    else { Show-Toast 'Vanda stage-3 monitor: ssh failed' $last }
    exit 1
}

function Section([string]$name) {
    $m = [regex]::Match($raw, "===$name===\r?\n(.*?)(?=\r?\n===[A-Z]+===|\s*$)", 'Singleline')
    if ($m.Success) { return $m.Groups[1].Value.Trim() } else { return '' }
}
$report = Section 'REPORT'
$acts   = Section 'ACTIONS'
$attnT  = Section 'ATTN'
$toast  = Section 'TOAST'
$flags  = Section 'FLAGS'
$attn   = $flags -match 'ATTENTION=1'
$done   = $flags -match 'DONE=1'
$ls.ssh_fail = 0; $ls.last_ok = (Get-Date).ToString('yyyy-MM-dd HH:mm'); Save-LocalState
try { $stj = & ssh -o BatchMode=yes -o ConnectTimeout=30 vanda $RemoteSt 2>$null | Out-String; if ($stj -match '"systems"') { [IO.File]::WriteAllText((Join-Path $Here 'state_remote.json'), $stj, $Utf8) } } catch { }

[IO.File]::WriteAllText((Join-Path $Here 'status_latest.md'), "$report`r`n", $Utf8)
[IO.File]::WriteAllText((Join-Path $Here "status_$Stamp.md"), "$report`r`n", $Utf8)
[IO.File]::AppendAllText((Join-Path $Here 'monitor_local.log'), "$report`r`n`r`n", $Utf8)
try { . (Join-Path $Here 'records.ps1'); [IO.File]::WriteAllText((Join-Path $RecDir "monitor_s3_$Stamp.md"), "$report`r`n", $Utf8); Update-Index } catch { }

if ($acts) {
    $lines = ($acts -split "\r?\n" | Where-Object { $_.Trim() } | ForEach-Object { "- $_" }) -join "`r`n"
    $hdr = [char]0x81EA + [char]0x52A8 + [char]0x76D1 + [char]0x63A7   # "auto monitor" in Chinese, kept ASCII-safe
    [IO.File]::AppendAllText($SubMd, "`r`n## $(Get-Date -Format 'yyyy-MM-dd HH:mm') SGT - $hdr`r`n$lines`r`n", $Utf8)
}

if ($done) {
    [IO.File]::WriteAllText($NextFile, "DONE`r`n", $Utf8)
    $attnFile = Join-Path $Here 'attention_latest.txt'
    [IO.File]::WriteAllText($attnFile, "DONE: step 1 finished; results/stage3_step1_table.md written. Finalise and sync (handoff, memory, GitHub).`r`n", $Utf8)
    Start-Process -FilePath 'powershell.exe' -WindowStyle Hidden -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$(Join-Path $Here 'claude_takeover_stage3.ps1')`"", '-AttnFile', "`"$attnFile`"")
    Show-Toast 'Vanda stage-3: step 1 done' $toast
    try { Disable-ScheduledTask -TaskName $TaskName -ErrorAction Stop | Out-Null } catch { }
    exit 0
}
[IO.File]::WriteAllText($NextFile, ((Get-Date).AddHours(5).ToString('yyyy-MM-ddTHH:mm:sszzz') + "`r`n"), $Utf8)

if ($attn -and $attnT) {
    $attnFile = Join-Path $Here 'attention_latest.txt'
    [IO.File]::WriteAllText($attnFile, "$attnT`r`n", $Utf8)
    $hash = (Sha256File $attnFile)
    $skip = $false
    $lastF = Join-Path $Here 'claude_takeover_last.json'
    if (Test-Path $lastF) {
        try {
            $l = [IO.File]::ReadAllText($lastF, [Text.Encoding]::UTF8) | ConvertFrom-Json
            # same items, already handled successfully -> they are waiting for the user; do not spend another run
            if ($l.ok -and $l.hash -eq $hash) { $skip = $true }
        } catch { }
    }
    if ($skip) {
        Show-Toast 'Vanda stage-3: waiting for you' "Claude already handled these items; see monitor\claude_takeover_latest.md. $toast"
    } else {
        Start-Process -FilePath 'powershell.exe' -WindowStyle Hidden -ArgumentList @(
            '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$(Join-Path $Here 'claude_takeover_stage3.ps1')`"",
            '-AttnFile', "`"$attnFile`"")
        Show-Toast 'Vanda stage-3: needs attention -> Claude CLI taking over' $toast
    }
} else {
    Show-Toast 'Vanda stage-3' $toast
}
exit 0
