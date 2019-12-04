#!/bin/bash
# $1 = node1 address
# $2 = node2 address
# $3 = node3 address
# $4 = node4 address

curl -s -o /dev/null http://$1/kv-store/clear
curl -s -o /dev/null http://$2/kv-store/clear
curl -s -o /dev/null http://$3/kv-store/clear
curl -s -o /dev/null http://$4/kv-store/clear