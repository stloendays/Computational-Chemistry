# Claude Code CLI takeover (headless `claude -p`) for ATTENTION items of the stage-3 monitor, and for the final
# sync at DONE. Started in the background by monitor_stage3.ps1; never waits for a human. CLI only, no desktop
# sidebar session (user 2026-09-24: monitor and operate through the CLI). Windows PowerShell 5.1 compatible; ASCII only.
#   -AttnFile <file>   ATTENTION items (UTF-8), inserted into claude_takeover_prompt_stage3.md
#   -Test              send a one-line prompt instead (checks that headless Claude works here)
#   -DryRun            only build the prompt file, do not start Claude
param([string]$AttnFile = '', [switch]$Test, [switch]$DryRun)
$ErrorActionPreference = 'Continue'
$env:PSModulePath = [Environment]::GetEnvironmentVariable('PSModulePath', 'Machine')   # do not inherit PowerShell 7 module paths
function Sha256File([string]$p) { $s = [Security.Cryptography.SHA256]::Create(); try { -join ($s.ComputeHash([IO.File]::ReadAllBytes($p)) | ForEach-Object { $_.ToString('X2') }) } finally { $s.Dispose() } }
$Here    = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root    = 'D:\OneDrive - National University of Singapore\ComputeChem'
$Claude  = 'D:\Download\npm-global\node_modules\@anthropic-ai\claude-code\bin\claude.exe'
$Lock    = Join-Path $Here 'claude_takeover_stage3.lock'
$Last    = Join-Path $Here 'claude_takeover_last.json'
$Utf8    = New-Object System.Text.UTF8Encoding($false)
$Stamp   = Get-Date -Format 'yyyyMMdd_HHmm'
$Out     = Join-Path $Here "claude_takeover_$Stamp.md"
$Err     = Join-Path $Here "claude_takeover_$Stamp.err.txt"
$PromptF = Join-Path $Here "claude_takeover_$Stamp.prompt.md"
$TimeoutMin = 150

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

# one takeover at a time (two agents acting on the same jobs happened on 2026-09-23)
if (Test-Path $Lock) {
    $age = ((Get-Date) - (Get-Item $Lock).LastWriteTime).TotalMinutes
    $old = (Get-Content $Lock -ErrorAction SilentlyContinue | Select-Object -First 1)
    $alive = $false
    if ($old -match '^\d+$') { $alive = [bool](Get-Process -Id ([int]$old) -ErrorAction SilentlyContinue) }
    if ($alive -and $age -lt ($TimeoutMin + 10)) { exit 0 }
    Remove-Item $Lock -Force -ErrorAction SilentlyContinue
}
[IO.File]::WriteAllText($Lock, "$PID`r`n", $Utf8)

try {
    if ($Test) {
        $prompt = 'Reply with exactly one line: TAKEOVER-OK'
    } else {
        $attn = ''
        if ($AttnFile -and (Test-Path $AttnFile)) { $attn = [IO.File]::ReadAllText($AttnFile, [Text.Encoding]::UTF8).Trim() }
        $items = ($attn -split "\r?\n" | Where-Object { $_.Trim() } | ForEach-Object { "- $_" }) -join "`n"
        $tpl = [IO.File]::ReadAllText((Join-Path $Here 'claude_takeover_prompt_stage3.md'), [Text.Encoding]::UTF8)
        $prompt = $tpl.Replace('{{ATTN}}', $items)
    }
    [IO.File]::WriteAllText($PromptF, $prompt, $Utf8)
    if ($DryRun) { Write-Output "dry-run prompt: $PromptF"; return }

    . (Join-Path $Here 'records.ps1')
    $attnShow = ''
    if ($AttnFile -and (Test-Path $AttnFile)) { $attnShow = (([IO.File]::ReadAllText($AttnFile, [Text.Encoding]::UTF8).Trim() -split "\r?\n") | ForEach-Object { "- $_" }) -join "`r`n" }
    $Jsonl = Join-Path $Here "claude_takeover_$Stamp.jsonl"
    $ProjDir = 'C:\Users\ASUS\.claude\projects\D--OneDrive---National-University-of-Singapore-ComputeChem'
    $t0 = Get-Date
    # --- Claude Code CLI, headless; prompt on stdin, working directory = ComputeChem (CLAUDE.md, memory, skills) ---
    $p = Start-Process -FilePath $Claude -ArgumentList @('-p', '--dangerously-skip-permissions', '--output-format', 'stream-json', '--verbose') `
         -WorkingDirectory $Root -RedirectStandardInput $PromptF -RedirectStandardOutput $Jsonl `
         -RedirectStandardError $Err -WindowStyle Hidden -PassThru
    $null = $p.Handle   # cache the handle, otherwise ExitCode is empty after WaitForExit
    $deadline = (Get-Date).AddMinutes($TimeoutMin); $finished = $false
    while ((Get-Date) -lt $deadline) {
        if ($p.WaitForExit(30000)) { $finished = $true; break }
        if (-not $Test) { try { Write-Takeover-Record $Stamp $Jsonl 'running' '(in progress)' $attnShow; Update-Index } catch { } }
    }
    if (-not $finished) { try { $p.Kill() } catch { } }
    $code = if ($finished) { $p.ExitCode } else { -1 }

    $text = ''; $isErr = $false
    if (Test-Path $Jsonl) {
        foreach ($l in [IO.File]::ReadAllLines($Jsonl, [Text.Encoding]::UTF8)) {
            if ($l -match '"type":"result"') { try { $r = $l | ConvertFrom-Json; $text = "$($r.result)"; $isErr = [bool]$r.is_error } catch { } }
        }
    }
    [IO.File]::WriteAllText($Out, $text, $Utf8)
    if ($isErr) { $code = if ($code -eq 0) { 1 } else { $code } }
    $errt = ''
    if (Test-Path $Err) { $errt = [IO.File]::ReadAllText($Err, [Text.Encoding]::UTF8) }
    # failures seen on 2026-09-22/23: session limit, Fable limit, API 500, not logged in
    $limitRe = 'hit your session limit|reached your .* limit|usage limit|API Error|Internal server error|Invalid API key|Please run /login|credit balance|rate limit'
    $failed = (-not $finished) -or ($code -ne 0) -or ($text.Trim() -eq '') -or ($text -match $limitRe) -or ($errt -match $limitRe)
    $first = ($text -split "\r?\n" | Where-Object { $_.Trim() } | Select-Object -First 1)
    if (-not $first) { $first = ($errt -split "\r?\n" | Where-Object { $_.Trim() } | Select-Object -First 1) }
    if (-not $finished) { $first = "timeout after $TimeoutMin min" }

    if (-not $Test) {
        $hash = ''
        if ($AttnFile -and (Test-Path $AttnFile)) { $hash = (Sha256File $AttnFile) }
        $rec = @{ time = (Get-Date).ToString('s'); ok = (-not $failed); exit = $code; hash = $hash;
                  report = (Split-Path -Leaf $Out); first = "$first" } | ConvertTo-Json -Compress
        [IO.File]::WriteAllText($Last, $rec, $Utf8)
        if (Test-Path $Out) { [IO.File]::Copy($Out, (Join-Path $Here 'claude_takeover_latest.md'), $true) }
    }
    if (-not $Test) {
        try { Write-Takeover-Record $Stamp $Jsonl ($(if ($failed) { 'FAILED' } else { 'done' })) $text $attnShow; Update-Index } catch { }
    }
    if ($failed) { Show-Toast 'Vanda stage-3: Claude CLI takeover FAILED' "$first" }
    else { Show-Toast 'Vanda stage-3: Claude CLI took over' "$first" }
    if ($Test) { Write-Output "exit=$code failed=$failed first=$first" }
}
finally {
    Remove-Item $Lock -Force -ErrorAction SilentlyContinue
}
