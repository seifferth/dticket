#!/bin/sh

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
printf "%s" "Storing ticket as '~/tickets/deutschlandticket-$1.pdf' ..." >&2
dticket-convert "$2" -o ~/tickets/deutschlandticket-"$1".pdf
printf "\b\b\b   \b\b\b\b\n" >&2
