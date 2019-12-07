#!/bin/bash
#$1 = address of node 1
#$2 = address of node 2

putOutput=$(./Tests/put.sh $1 "testKey1" "value1" "{}")
echo $putOutput

./Tests/disconnect_node.sh node1

echo "polling replica for value, which it cannot service under partition"
./Tests/get.sh $2 "testKey1" "{\"10.10.0.2:13800\":1,\"10.10.0.3:13800\":0}"

./Tests/connect_node.sh node1

echo "sleeping until partition heals"
sleep 5
echo "woke up, checking for the same value again"
./Tests/get_expected.sh $2 "testKey1" "{\"10.10.0.2:13800\":1,\"10.10.0.3:13800\":0}" "value1"