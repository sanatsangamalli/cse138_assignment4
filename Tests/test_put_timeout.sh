#!/bin/bash
echo "Putting sampleKey2 into some node1"
./Tests/put.sh 10.10.0.4:13800 sampleKey2 sampleValue2
echo "Disconnecting node1"
./Tests/disconnect_node.sh node1
echo "Attempting to put sampleKey2 into some node1. Should timeout"
./Tests/put.sh 10.10.0.4:13800 sampleKey2 sampleValue2

./Tests/connect_node.sh node1