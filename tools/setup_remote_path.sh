#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<'EOF'
Usage:
  bash tools/setup_remote_path.sh [OPTIONS]

Options:
  --token TOKEN       Set a fixed PQViewer token on this remote account.
  --token-file FILE   Read the fixed token from FILE.
  --help             Show this help.

If neither --token nor --token-file is given, this script tries:
  tools/pqv_token.txt
EOF
}

token=""
token_file=""

while (($#)); do
    case "$1" in
        --token)
            token="${2:?--token requires a value}"
            shift 2
            ;;
        --token-file)
            token_file="${2:?--token-file requires a value}"
            shift 2
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            echo "setup_remote_path.sh: unknown option: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
done

# Resolve the tools directory from this script location.
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
tools_dir="$repo_root/tools"
default_token_file="$tools_dir/pqv_token.txt"

if [[ -z "$token" ]]; then
    if [[ -n "$token_file" ]]; then
        if [[ ! -r "$token_file" ]]; then
            echo "[ERROR] Token file is not readable: $token_file" >&2
            exit 1
        fi
        token="$(tr -d '\r\n' < "$token_file")"
    elif [[ -r "$default_token_file" ]]; then
        token="$(tr -d '\r\n' < "$default_token_file")"
    fi
fi

if [[ -z "$token" ]]; then
    echo "[ERROR] No token was provided." >&2
    echo >&2
    echo "Run one of the following:" >&2
    echo "  bash tools/setup_remote_path.sh --token TOKEN" >&2
    echo "  bash tools/setup_remote_path.sh --token-file tools/pqv_token.txt" >&2
    exit 1
fi

if [[ ! -f "$tools_dir/pqv-open" ]]; then
    echo "[ERROR] pqv-open was not found:" >&2
    echo "  $tools_dir/pqv-open" >&2
    exit 1
fi

chmod +x "$tools_dir/pqv-open"

printf '%s\n' "$token" > "$default_token_file"
chmod 600 "$default_token_file" 2>/dev/null || true

shell_name="$(basename "${SHELL:-}")"

echo "PQViewer repository root:"
echo "  $repo_root"
echo
echo "PQViewer tools directory:"
echo "  $tools_dir"
echo
echo "Fixed token file:"
echo "  $default_token_file"
echo

if [[ "$shell_name" == "fish" ]]; then
    conf_dir="$HOME/.config/fish/conf.d"
    conf_file="$conf_dir/pqviewer_remote_open.fish"
    mkdir -p "$conf_dir"

    cat > "$conf_file" <<EOF
# Added by PQViewer Remote Open setup.
fish_add_path "$tools_dir"
set -x PQV_TOKEN "$token"
set -x PQVIEWER_ROOT "$repo_root"
set -x PQVIEWER_TOOLS "$tools_dir"
EOF

    echo "Installed fish setup:"
    echo "  $conf_file"
    echo
    echo "Reload with:"
    echo "  source $conf_file"
else
    rc_file="$HOME/.bashrc"
    marker_begin="# >>> PQViewer Remote Open setup >>>"
    marker_end="# <<< PQViewer Remote Open setup <<<"
    tmp_file="$(mktemp)"

    touch "$rc_file"

    awk -v begin="$marker_begin" -v end="$marker_end" '
        $0 == begin {skip=1; next}
        $0 == end {skip=0; next}
        !skip {print}
    ' "$rc_file" > "$tmp_file"

    cat >> "$tmp_file" <<EOF

$marker_begin
export PATH="$tools_dir:\$PATH"
export PQV_TOKEN="$token"
export PQVIEWER_ROOT="$repo_root"
export PQVIEWER_TOOLS="$tools_dir"
$marker_end
EOF

    mv "$tmp_file" "$rc_file"

    echo "Updated bash setup:"
    echo "  $rc_file"
    echo
    echo "Reload with:"
    echo "  source ~/.bashrc"
fi

echo
echo "Setup finished."
echo
echo "Check with:"
echo "  which pqv-open"
echo "  echo \$PQV_TOKEN"
