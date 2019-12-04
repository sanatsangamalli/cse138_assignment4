#!/bin/bash
# $1 = node address
# $2 = causal-context
# $3 = shard_id

curl -s --request GET                                                 \
      --header "Content-Type: application/json"                     \
      --write-out "%{http_code}\n"                                  \
      --data "{\"causal-context\": \"$2\"}"                             \
      http://$1/kv-store/shards/$3