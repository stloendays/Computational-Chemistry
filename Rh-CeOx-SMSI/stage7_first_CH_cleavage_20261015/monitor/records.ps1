# Visible record of the stage-7 monitor: monitor\records\
#   README.md               index, newest first (monitor runs + Claude takeovers)
#   monitor_<stamp>.md      each monitor report
#   takeover_<stamp>.md     each takeover: conclusion + every step (what it read, commands, outputs)
# Dot-sourced by monitor_stage7.ps1 and claude_takeover_stage7.ps1. Windows PowerShell 5.1, ASCII only.
$RecDir = Join-Path $PSScriptRoot 'records'
$RecUtf8 = New-Object System.Text.UTF8Encoding($false)
if (-not (Test-Path $RecDir)) { New-Item -ItemType Directory -Path $RecDir | Out-Null }

function Short([string]$s, [int]$n) {
    if ($null -eq $s) { return '' }
    $s = $s.Trim(); if ($s.Length -gt $n) { return $s.Substring(0, $n) + ' ...' } else { return $s }
}

# Render a Claude stream-json / transcript jsonl into readable Markdown steps.
function Render-Steps([string]$Jsonl) {
    $out = New-Object System.Collections.Generic.List[string]
    $n = 0
    foreach ($line in [IO.File]::ReadAllLines($Jsonl, [Text.Encoding]::UTF8)) {
        if (-not $line.Trim()) { continue }
        try { $j = $line | ConvertFrom-Json } catch { continue }
        if (-not $j.message -or -not $j.message.content) { continue }
        $c = $j.message.content
        if ($c -is [string]) { continue }
        foreach ($x in $c) {
            if ($j.type -eq 'assistant' -and $x.type -eq 'text' -and $x.text.Trim()) {
                $out.Add(''); $out.Add('> ' + ((Short $x.text 1500) -replace "`n", "`n> "))
            } elseif ($j.type -eq 'assistant' -and $x.type -eq 'tool_use') {
                $n++; $i = $x.input; $what = ''
                switch ($x.name) {
                    'Bash'       { $what = $i.description; $cmd = $i.command }
                    'PowerShell' { $what = $i.description; $cmd = $i.command }
                    'Read'       { $what = 'read ' + $i.file_path; $cmd = '' }
                    'Edit'       { $what = 'edit ' + $i.file_path; $cmd = '' }
                    'Write'      { $what = 'write ' + $i.file_path; $cmd = '' }
                    'Grep'       { $what = 'grep ' + $i.pattern; $cmd = '' }
                    'Agent'      { $what = 'subagent (' + $i.model + '): ' + $i.description; $cmd = (Short $i.prompt 600) }
                    default      { $what = ($i | ConvertTo-Json -Compress -Depth 3); $cmd = '' }
                }
                $out.Add(''); $out.Add("**$n. $($x.name)** - $(Short $what 200)")
                if ($cmd) { $out.Add('```'); $out.Add((Short $cmd 1200)); $out.Add('```') }
            } elseif ($j.type -eq 'user' -and $x.type -eq 'tool_result') {
                $t = $x.content
                if ($t -isnot [string]) { $t = ($t | Where-Object { $_.type -eq 'text' } | ForEach-Object { $_.text }) -join "`n" }
                $t = ($t -split "`n" | Where-Object { $_ -notmatch 'post-quantum|store now|openssh.com/pq|Authorized users' }) -join "`n"
                if ($t.Trim()) { $out.Add('<details><summary>output</summary>'); $out.Add(''); $out.Add('```'); $out.Add((Short $t 1500)); $out.Add('```'); $out.Add('</details>') }
            }
        }
    }
    return ($out -join "`r`n")
}

function Write-Takeover-Record([string]$Stamp, [string]$Jsonl, [string]$Status, [string]$Result, [string]$Attn) {
    $steps = ''
    if ($Jsonl -and (Test-Path $Jsonl)) { $steps = Render-Steps $Jsonl }
    $t = "# Claude takeover $Stamp`r`n`r`nStatus: **$Status**`r`n`r`n## Items handed over`r`n`r`n$Attn`r`n`r`n## Result`r`n`r`n$Result`r`n`r`n## Steps`r`n$steps`r`n"
    [IO.File]::WriteAllText((Join-Path $RecDir "takeover_$Stamp.md"), $t, $RecUtf8)
}

function Update-Index {
    $rows = foreach ($f in (Get-ChildItem $RecDir -Filter '*_2026*.md' | Sort-Object Name -Descending)) {
        $txt = [IO.File]::ReadAllText($f.FullName, [Text.Encoding]::UTF8)
        $kind = if ($f.Name -like 'takeover_*') { 'Claude takeover' } else { 'monitor' }
        $lines = $txt -split "\r?\n" | Where-Object { $_.Trim() -and $_ -notmatch '^#' }
        if ($kind -eq 'Claude takeover') {
            $m = [regex]::Match($txt, '## Result\s+(.+?)\r?\n'); $sum = if ($m.Success) { $m.Groups[1].Value } else { '' }
            $st = [regex]::Match($txt, 'Status: \*\*(.+?)\*\*').Groups[1].Value; $sum = "[$st] $sum"
        } else { $sum = $lines | Select-Object -First 1 }
        $when = ($f.BaseName -replace '^[a-z]+_', '') -replace '^(\d{4})(\d\d)(\d\d)_(\d\d)(\d\d)$', '$1-$2-$3 $4:$5'
        "| $when | $kind | $((Short $sum 160) -replace '\|', '/') | [$($f.Name)]($($f.Name)) |"
    }
    $h = "# Vanda stage-7 monitor records`r`n`r`nEvery 5 h the monitor writes a report here; when it raises items that need handling, a background Claude takes over and its full processing record (steps, commands, outputs) is saved as takeover_*.md. Newest first.`r`n`r`n| Time (SGT) | Kind | Summary | File |`r`n|---|---|---|---|`r`n"
    [IO.File]::WriteAllText((Join-Path $RecDir 'README.md'), $h + ($rows -join "`r`n") + "`r`n", $RecUtf8)
}
