#!/bin/bash
# $1 = node address
# $2 = key
# $3 = value

curl -s --request PUT                                                \
     --header    "Content-Type: application/json"                 \
     --data      "{\"value\": \"$3\"}"                       \
     --write-out "%{http_code}\n"                                 \
     http://$1/kv-store/keys/$2