#!/bin/bash
# $1 = node address
# $2 = key
# $3 = causal-context
curl --max-time 5.5                                         \
    --request GET                                                \
     --header    "Content-Type: application/json"                 \
     --data "{\"causal-context\": $3}"                       \
     http://$1/kv-store/keys/$2
     
# --write-out "%{http_code}\n"                                 \