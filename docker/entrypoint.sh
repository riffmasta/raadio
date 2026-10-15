#!/bin/sh
set -eu

config_file=${RAADIO_CONF:-/config/config.env}
if [ ! -f "$config_file" ]; then
    echo "Seadete fail puudub: $config_file" >&2
    echo "Kopeeri docker/config.env.example faili docker/config.env ja täida parool." >&2
    exit 1
fi

exec "$@"
