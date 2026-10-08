#!/usr/bin/env bash
# Client side of .github/workflows/vanda-ssh.yml.
#
#   vanda_gh.sh keygen  DIR          one-time RSA key pair in DIR; prints the
#                                    base64 public key for the workflow "pubkey" input
#   vanda_gh.sh decrypt DIR LOG      decrypt the output block from a job log
#                                    (LOG is a file path or an https:// log URL)
set -euo pipefail

usage() { sed -n '2,8p' "$0" >&2; exit 2; }

cmd=${1:-}; dir=${2:-}
[ -n "$cmd" ] && [ -n "$dir" ] || usage

case "$cmd" in
  keygen)
    mkdir -p "$dir" && chmod 700 "$dir"
    openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:3072 -out "$dir/priv.pem" 2> /dev/null
    chmod 600 "$dir/priv.pem"
    openssl pkey -in "$dir/priv.pem" -pubout | base64 -w 0
    echo
    ;;
  decrypt)
    log=${3:-}; [ -n "$log" ] || usage
    tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
    if [[ $log == https://* ]]; then
      curl -fsSL "$log" -o "$tmp/log"
    else
      cp "$log" "$tmp/log"
    fi
    # Job logs prefix each line with an ISO-8601 timestamp.
    sed -E 's/^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9:.]+Z //; s/\r$//' "$tmp/log" > "$tmp/clean"
    grep -E '^remote exit code: |^output bytes: ' "$tmp/clean" >&2 || true
    sed -n '/^-----BEGIN VANDA KEY-----$/,/^-----END VANDA KEY-----$/p' "$tmp/clean" \
      | sed '1d;$d' | base64 -d > "$tmp/k.enc"
    sed -n '/^-----BEGIN VANDA DATA-----$/,/^-----END VANDA DATA-----$/p' "$tmp/clean" \
      | sed '1d;$d' | base64 -d > "$tmp/out.enc"
    [ -s "$tmp/k.enc" ] && [ -s "$tmp/out.enc" ] || { echo "no encrypted block in log" >&2; exit 1; }
    openssl pkeyutl -decrypt -inkey "$dir/priv.pem" \
      -pkeyopt rsa_padding_mode:oaep -pkeyopt rsa_oaep_md:sha256 \
      -in "$tmp/k.enc" -out "$tmp/k.txt"
    openssl enc -d -aes-256-cbc -pbkdf2 -pass "file:$tmp/k.txt" -in "$tmp/out.enc" | gunzip -c
    ;;
  *) usage ;;
esac
