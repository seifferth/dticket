#!/bin/sh

get_like_firefox() {
    curl \
        -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0' \
        -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8' \
        -H 'Accept-Language: en-US,en;q=0.5' \
        -H 'Accept-Encoding: gzip, deflate, br, zstd' \
        -H 'Connection: keep-alive' \
        -H 'Upgrade-Insecure-Requests: 1' \
        -H 'Sec-Fetch-Dest: document' \
        -H 'Sec-Fetch-Mode: navigate' \
        -H 'Sec-Fetch-Site: none' \
        -H 'Sec-Fetch-User: ?1' \
        -H 'Priority: u=0, i' \
        "$1" -o "$2"
}

print_help() {
cat <<EOF
Usage: dticket-insert YYYY-MM FILE
EOF
}

if test "$1" = "-h" || test "$1" = "--help"; then
    print_help
    exit 0
elif ! test "$#" = 2 || ! echo "$1" |
                grep -q '^[0-9][0-9][0-9][0-9]-[0-9][0-9]$'; then
    print_help >&2
    exit 1
fi

mkdir -p ~/tickets
if test "$(head -c4 "$2")" = "%PDF"; then
    printf "%s" "Storing original pdf as '~/tickets/abobestätigung-$1.pdf'"
    cp "$2" ~/tickets/abobestätigung-"$1".pdf
    printf "\n"
fi
if printf "%s" "$2" | grep -q '^https://'; then
    tempfile="$(mktemp)"
    get_like_firefox "$2" "$tempfile"
fi
printf "%s" "Storing ticket as '~/tickets/deutschlandticket-$1.pdf' ..." >&2
if test "$tempfile"; then
    dticket-convert "$tempfile" -o ~/tickets/deutschlandticket-"$1".pdf
    rm "$tempfile"
else
    dticket-convert "$2" -o ~/tickets/deutschlandticket-"$1".pdf
fi
printf "\b\b\b   \b\b\b\b\n" >&2
