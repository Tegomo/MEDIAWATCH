#!/bin/sh
# Replace environment variables in kong.yml template
sed "s|\${ANON_KEY}|${ANON_KEY}|g; s|\${SERVICE_ROLE_KEY}|${SERVICE_ROLE_KEY}|g" \
  /var/lib/kong/kong.yml.template > /tmp/kong.yml

# Start Kong
/docker-entrypoint.sh kong docker-start
