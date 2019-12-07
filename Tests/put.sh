#!/bin/bash
# $1 = node address
# $2 = key
# $3 = value
# $4 = causal-context
curl --max-time 5.5 --request PUT                                                \
     --header    "Content-Type:application/json"                 \
     --data      "{\"value\": \"$3\", \"causal-context\": $4}"                       \
     --write-out "%{http_code}\n"                                 \
     http://$1/kv-store/keys/$2