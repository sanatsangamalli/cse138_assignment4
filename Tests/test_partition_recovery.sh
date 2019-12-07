#!/bin/bash
#$1 = address of node 1
#$2 = address of node 2

putOutput=$(./Tests/put.sh $1 "testKey1" "value1" "{}")
echo $putOutput

./Tests/disconnect_node.sh node1

echo "polling replica for value, which it cannot service under partition"
./Tests/get.sh $2


echo "sleeping until partition heals"
sleep 5
echo "woke up, checking for value"