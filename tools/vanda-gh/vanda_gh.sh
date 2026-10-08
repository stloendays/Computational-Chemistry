#!/usr/bin/env bash
# Client side of .github/workflows/vanda-ssh.yml.
#
#   vanda_gh.sh key     KEYFILE               derive the transfer key from $VANDA_GATE_KEY_B64
#   vanda_gh.sh decrypt KEYFILE LOG           print the output block of a run/put job log
#                                             (LOG is a file path or an https:// log URL)
#   vanda_gh.sh pack    KEYFILE OUT PATH...   encrypted tar.gz of PATHs for mode=put
#   vanda_gh.sh unpack  KEYFILE IN OUTDIR     unpack a mode=get artifact (.zip, URL, or .enc)
#
# Keep KEYFILE outside the repository (e.g. the session scratchpad).
set -euo pipefail

usage() { sed -n '2,11p' "$0" >&2; exit 2; }

cmd=${1:-}; key=${2:-}
[ -n "$cmd" ] && [ -n "$key" ] || usage

enc() { openssl enc -aes-256-cbc -pbkdf2 -salt -pass "file:$key" "$@"; }
dec() { openssl enc -d -aes-256-cbc -pbkdf2 -pass "file:$key" "$@"; }

fetch() {  # fetch SRC DST: copy a local file or download an https:// URL
  if [[ $1 == https://* ]]; then curl -fsSL "$1" -o "$2"; else cp "$1" "$2"; fi
}

case "$cmd" in
  key)
    [ -n "${VANDA_GATE_KEY_B64:-}" ] || { echo "VANDA_GATE_KEY_B64 is not set" >&2; exit 1; }
    mkdir -p "$(dirname "$key")"
    (umask 077
     { printf 'vanda-transfer-v1'; printf '%s' "$VANDA_GATE_KEY_B64" | tr -d ' \r\n' | base64 -d; } \
       | sha256sum | cut -d' ' -f1 > "$key")
    echo "transfer key written to $key" >&2
    ;;
  decrypt)
    log=${3:-}; [ -n "$log" ] || usage
    tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
    fetch "$log" "$tmp/log"
    # Job logs prefix each line with an ISO-8601 timestamp.
    sed -E 's/^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9:.]+Z //; s/\r$//' "$tmp/log" > "$tmp/clean"
    grep -E '^(elapsed|remote exit code|output bytes|files listed): ' "$tmp/clean" >&2 || true
    sed -n '/^-----BEGIN VANDA DATA-----$/,/^-----END VANDA DATA-----$/p' "$tmp/clean" \
      | sed '1d;$d' | base64 -d > "$tmp/out.enc"
    [ -s "$tmp/out.enc" ] || { echo "no encrypted block in log" >&2; exit 1; }
    dec -in "$tmp/out.enc" | gunzip -c
    ;;
  pack)
    out=${3:-}; [ -n "$out" ] && [ $# -ge 4 ] || usage
    shift 3
    tar czf - -- "$@" | enc -out "$out"
    echo "packed $# path(s) into $out ($(wc -c < "$out") bytes)" >&2
    ;;
  unpack)
    in=${3:-}; outdir=${4:-}; [ -n "$in" ] && [ -n "$outdir" ] || usage
    tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
    fetch "$in" "$tmp/in"
    if unzip -tq "$tmp/in" > /dev/null 2>&1; then
      unzip -q "$tmp/in" -d "$tmp/z"
      src=$(find "$tmp/z" -type f -name '*.enc' | head -n 1)
    else
      src="$tmp/in"
    fi
    mkdir -p "$outdir"
    dec -in "$src" | tar xzvf - -C "$outdir"
    ;;
  *) usage ;;
esac
