# Vanda via GitHub Actions

Claude cloud containers cannot open outbound SSH (port 22 is blocked; port 443
is intercepted by the egress gateway). `.github/workflows/vanda-ssh.yml` runs
`ssh vanda` on a GitHub runner instead.

| mode | inputs | result |
|---|---|---|
| `run` | `cmd` | command output, encrypted, in the job log |
| `get` | `path` (file or dir; absolute or relative to `$HOME`) | encrypted tar.gz as artifact `vanda-get` (kept 1 day) |
| `put` | `blob` (repo path made by `pack`), `dest`, `overwrite` | unpacked on Vanda; existing files are kept unless `overwrite` |

All modes take `timeout_s` (default 900). The relay hop alone can take ~2 min.

## Encryption

The repository is public. Everything crossing it (logs, artifacts, upload blobs)
is AES-256 encrypted with a key derived from the relay key:
`sha256("vanda-transfer-v1" || decoded VANDA_GATE_KEY_B64)`. The runner derives
it from the secret, the cloud session from its environment variable of the same
name; the key itself is never printed or committed.

## One-time setup

Repository → Settings → Environments → `VANDA_GATE_KEY_B64` → Environment secrets:

| Secret | Value |
|---|---|
| `VANDA_GATE_KEY_B64` | same value as the cloud environment variable of that name |
| `VANDA_RELAY_HOST` | relay address |

Only the repository owner can trigger the workflow (`if: github.actor == github.repository_owner`).

## Usage

```bash
K=<scratch>/xfer.key
tools/vanda-gh/vanda_gh.sh key     $K
tools/vanda-gh/vanda_gh.sh decrypt $K <log file or URL>          # run / put output
tools/vanda-gh/vanda_gh.sh pack    $K .vanda-transfer/x.enc FILES # then commit, dispatch put
tools/vanda-gh/vanda_gh.sh unpack  $K <artifact zip or URL> OUTDIR
```

Delete `.vanda-transfer/*.enc` after a put.
