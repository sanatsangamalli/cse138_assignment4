#!/bin/bash
# $1 = node address
# $2 = key

curl -s --request GET                                                \
     --header    "Content-Type: application/json"                 \
     http://$1/kv-store/keys/$2
     
# --write-out "%{http_code}\n"                                 \