# Vanda via GitHub Actions

Claude cloud containers cannot open outbound SSH (port 22 is blocked; port 443
is intercepted by the egress gateway). `.github/workflows/vanda-ssh.yml` runs
`ssh vanda '<cmd>'` on a GitHub runner instead.

The repository is public, so the output never appears in plain text: the caller
supplies a one-time RSA public key, the runner encrypts the output with it, and
only ciphertext is written to the job log.

## One-time setup

Repository → Settings → Secrets and variables → Actions → New repository secret:

| Secret | Value |
|---|---|
| `VANDA_GATE_KEY_B64` | same value as the cloud environment variable of that name |
| `VANDA_RELAY_HOST` | relay address |

Only the repository owner can trigger the workflow (`if: github.actor == github.repository_owner`).

## Usage

```bash
tools/vanda-gh/vanda_gh.sh keygen  <dir>          # prints the base64 public key
# dispatch vanda-ssh.yml with inputs cmd=<command>, pubkey=<printed key>
tools/vanda-gh/vanda_gh.sh decrypt <dir> <log>    # log file or https:// log URL
```

Keep `<dir>` outside the repository (e.g. the session scratchpad).
