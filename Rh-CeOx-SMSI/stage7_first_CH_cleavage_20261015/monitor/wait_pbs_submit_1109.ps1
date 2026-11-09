# 2026-11-09: wait for the Vanda PBS server (down after /scratch filled up) and run monitor/submit_1109.py once.
# exit 9 from the script = PBS still down -> retry in 10 min; exit 0 = submitted (or already done) -> run the monitor
# once and stop; any other exit = partial/failed submission -> stop for a human look (no blind retry).
$R = '/scratch/junbotong/Dynamic_SMSI_stage7_first_CH_cleavage_20261015/monitor'
$deadline = (Get-Date).AddHours(72)
while ((Get-Date) -lt $deadline) {
    $out = & ssh -o BatchMode=yes -o ConnectTimeout=30 vanda "bash `$HOME/hpc_login.sh > /dev/null 2>&1; cd $R && python3 submit_1109.py" 2>&1 |
        Where-Object { $_ -notmatch 'post-quantum|store now|openssh.com/pq|Authorized users|vulnerable' } | Out-String
    $rc = $LASTEXITCODE
    Write-Output "$(Get-Date -Format 'MM-dd HH:mm') rc=$rc $($out.Trim())"
    if ($rc -eq 0) {
        $mon = & ssh -o BatchMode=yes -o ConnectTimeout=30 vanda "cd $R && timeout 270 python3 monitor_stage7.py | head -40" 2>&1 | Out-String
        Write-Output $mon
        Write-Output 'SUBMIT_DONE'
        exit 0
    }
    if ($rc -ne 9 -and $rc -ne 255) { Write-Output 'SUBMIT_FAILED: check by hand'; exit 1 }
    Start-Sleep -Seconds 600
}
Write-Output 'TIMEOUT: PBS still down after 72 h'
