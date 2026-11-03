# DynSMSI stage 7 (first C-H cleavage of CH4, four models, 20 jobs), local side of the REPORT-ONLY monitor.
# Windows Task Scheduler runs this every 5 h (task "vanda-stage7-monitor-5h"; the interval is the trigger repetition,
# adjustable from the monitor hub). Adapted from monitor_d3.ps1.
# 1. uploads monitor_stage7.py to /scratch/junbotong/Dynamic_SMSI_stage7_first_CH_cleavage_20261015/monitor/ and runs
#    it on the Vanda login node (no PBS action there; only a silent allocation refresh);
# 2. stores the report and the remote state here, writes hub_status.json, appends actions to monitor_actions.md,
#    shows a toast;
# 3. ATTENTION items -> claude_takeover_stage7.ps1 in the background (headless Claude Code CLI, diagnose + report,
#    no resubmission), unless the same items were already handled;
# 4. DONE -> copy results/stage7_table.md and E_stage7.txt from Vanda into ..\results\, hub done, task disables itself.
# Windows PowerShell 5.1 compatible; ASCII only (report text is UTF-8 from the server).
$ErrorActionPreference = 'Continue'
$env:PSModulePath = [Environment]::GetEnvironmentVariable('PSModulePath', 'Machine')   # do not inherit PowerShell 7 module paths
function Sha256File([string]$p) { $s = [Security.Cryptography.SHA256]::Create(); try { -join ($s.ComputeHash([IO.File]::ReadAllBytes($p)) | ForEach-Object { $_.ToString('X2') }) } finally { $s.Dispose() } }
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$OutputEncoding = [Text.Encoding]::UTF8
$Here     = Split-Path -Parent $MyInvocation.MyCommand.Path
$Stage    = Split-Path -Parent $Here
$ActMd    = Join-Path $Here 'monitor_actions.md'
$NextFile = Join-Path $Here 'NEXT_CHECK.txt'
$LocalSt  = Join-Path $Here 'local_state.json'
$TaskName = 'vanda-stage7-monitor-5h'
$RDir     = '/scratch/junbotong/Dynamic_SMSI_stage7_first_CH_cleavage_20261015'
$Remote   = "python3 $RDir/monitor/monitor_stage7.py"
$RemoteSt = "cat $RDir/monitor/state.json"
$ResDir   = Join-Path $Stage 'results'
$LocalTab = Join-Path $ResDir 'stage7_table.md'
$LocalE   = Join-Path $ResDir 'E_stage7.txt'
$Utf8     = New-Object System.Text.UTF8Encoding($false)
$Stamp    = Get-Date -Format 'yyyyMMdd_HHmm'

# interval (h) = the task's trigger repetition, so "next" stays right when the hub changes it
$IntervalH = 5.0
try {
    $rep = (Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop).Triggers[0].Repetition.Interval
    if ($rep) { $IntervalH = [Xml.XmlConvert]::ToTimeSpan($rep).TotalHours }
} catch { }

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

# the local copy of monitor_stage7.py is authoritative: upload it before every run
& ssh -o BatchMode=yes -o ConnectTimeout=30 vanda "mkdir -p $RDir/monitor" *> $null
& scp -q -o BatchMode=yes -o ConnectTimeout=30 (Join-Path $Here 'monitor_stage7.py') "vanda:$RDir/monitor/monitor_stage7.py" *> $null

$raw = & ssh -o BatchMode=yes -o ConnectTimeout=30 -o ServerAliveInterval=30 vanda $Remote 2>&1 |
       Where-Object { $_ -notmatch 'post-quantum|store now|openssh.com/pq|Authorized users' } | Out-String

# hub_status.json for the monitor hub (schema D:\Research\Monitor\hub\hub_status.schema.json)
$HubFile = Join-Path $Here 'hub_status.json'
$Results = @(
    @{ label = 'Stage-7 results table (20 jobs)'; path = $LocalTab },
    @{ label = 'Stage-7 energies E0 (txt)'; path = $LocalE })
function Write-Hub($obj) {
    $obj | Add-Member -NotePropertyName updated -NotePropertyValue ((Get-Date).ToString('s')) -Force
    $obj | Add-Member -NotePropertyName next -NotePropertyValue ((Get-Date).AddHours($IntervalH).ToString('s')) -Force
    $obj | Add-Member -NotePropertyName results -NotePropertyValue $Results -Force
    [IO.File]::WriteAllText($HubFile, ($obj | ConvertTo-Json -Depth 8), $Utf8)
}

if ($raw -notmatch '===REPORT===') {
    # SSH failure is not compute failure (maintenance, login-node or network trouble): report, never act.
    $ls.ssh_fail += 1; Save-LocalState
    try {
        $h = $null
        if (Test-Path $HubFile) { $h = [IO.File]::ReadAllText($HubFile, [Text.Encoding]::UTF8) | ConvertFrom-Json }
        if (-not $h) { $h = New-Object PSObject -Property @{ headline = 'ssh failed'; done = $false; attention = @(); table = @{ cols = @(); rows = @(); tags = @() } } }
        $h | Add-Member -NotePropertyName error -NotePropertyValue ("ssh/remote monitor failed ($($ls.ssh_fail) in a row): " + ($raw.Trim() -split "`n" | Select-Object -Last 1)) -Force
        Write-Hub $h
    } catch { }
    $msg = "# Vanda stage-7 monitor $(Get-Date -Format 'yyyy-MM-dd HH:mm') SGT`r`n`r`nssh/remote monitor FAILED ($($ls.ssh_fail) in a row):`r`n`r`n$raw"
    [IO.File]::WriteAllText((Join-Path $Here 'status_latest.md'), $msg, $Utf8)
    [IO.File]::AppendAllText((Join-Path $Here 'monitor_local.log'), "$msg`r`n`r`n", $Utf8)
    $last = ($raw.Trim() -split "`n" | Select-Object -Last 1)
    if ($ls.ssh_fail -ge 3) { Show-Toast "Vanda unreachable $($ls.ssh_fail)x in a row" "maintenance? last ok: $($ls.last_ok)  $last" }
    else { Show-Toast 'Vanda stage-7 monitor: ssh failed' $last }
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
try { . (Join-Path $Here 'records.ps1'); [IO.File]::WriteAllText((Join-Path $RecDir "monitor_$Stamp.md"), "$report`r`n", $Utf8); Update-Index } catch { }

# at DONE: fetch the deliverables so the hub lists existing files
$doneOk = $false; $doneErr = ''
if ($done) {
    try {
        if (-not (Test-Path $ResDir)) { New-Item -ItemType Directory -Path $ResDir | Out-Null }
        & scp -q -o BatchMode=yes -o ConnectTimeout=30 "vanda:$RDir/results/stage7_table.md" "$LocalTab.part" *> $null
        & scp -q -o BatchMode=yes -o ConnectTimeout=30 "vanda:$RDir/E_stage7.txt" "$LocalE.part" *> $null
        $n = 0
        if (Test-Path "$LocalE.part") { $n = @([IO.File]::ReadAllLines("$LocalE.part") | Where-Object { $_ -match '^\S+ -?\d+\.\d+$' }).Count }
        if ((Test-Path "$LocalTab.part") -and $n -eq 20) {
            Move-Item -Force "$LocalTab.part" $LocalTab; Move-Item -Force "$LocalE.part" $LocalE; $doneOk = $true
        } else { $doneErr = "results/stage7_table.md or E_stage7.txt missing on Vanda, or E_stage7.txt has $n of 20 lines" }
    } catch { $doneErr = "DONE handling failed: $($_.Exception.Message)" }
}
try {
    $h = (Section 'HUB') | ConvertFrom-Json
    $h | Add-Member -NotePropertyName error -NotePropertyValue $doneErr -Force
    $h | Add-Member -NotePropertyName working -NotePropertyValue '' -Force
    if ($done) { $h | Add-Member -NotePropertyName done -NotePropertyValue $doneOk -Force }
    Write-Hub $h
} catch { }

if ($acts) {
    $lines = ($acts -split "\r?\n" | Where-Object { $_.Trim() } | ForEach-Object { "- $_" }) -join "`r`n"
    $hdr = [char]0x81EA + [char]0x52A8 + [char]0x76D1 + [char]0x63A7   # "auto monitor" in Chinese, kept ASCII-safe
    [IO.File]::AppendAllText($ActMd, "`r`n## $(Get-Date -Format 'yyyy-MM-dd HH:mm') SGT - $hdr`r`n$lines`r`n", $Utf8)
}

if ($done -and $doneOk) {
    [IO.File]::WriteAllText($NextFile, "DONE`r`n", $Utf8)
    Show-Toast 'Vanda stage-7: all 20 jobs done' 'results\stage7_table.md and E_stage7.txt fetched.'
    try { Disable-ScheduledTask -TaskName $TaskName -ErrorAction Stop | Out-Null } catch { }
    exit 0
}
if ($done) { Show-Toast 'Vanda stage-7: done on Vanda, local step failed' $doneErr }
[IO.File]::WriteAllText($NextFile, ((Get-Date).AddHours($IntervalH).ToString('yyyy-MM-ddTHH:mm:sszzz') + "`r`n"), $Utf8)

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
        Show-Toast 'Vanda stage-7: waiting for you' "Claude already handled these items; see monitor\claude_takeover_latest.md. $toast"
    } else {
        Start-Process -FilePath 'powershell.exe' -WindowStyle Hidden -ArgumentList @(
            '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$(Join-Path $Here 'claude_takeover_stage7.ps1')`"",
            '-AttnFile', "`"$attnFile`"")
        Show-Toast 'Vanda stage-7: needs attention -> Claude CLI taking over' $toast
    }
} elseif (-not $done) {
    Show-Toast 'Vanda stage-7' $toast
}
exit 0
