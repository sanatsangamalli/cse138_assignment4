#!/bin/bash
echo $1
echo "Putting sampleKey into some node1"
./Tests/put.sh $1 "sampleKey" "sampleValue" "{}"
echo "Disconnecting node1 ..."
./Tests/disconnect_node.sh node1
echo "Attempting to get sampleKey from disconnected node1. Should timeout"
./Tests/get.sh $1 "sampleKey" "{}"
echo "Attempting to delete sampleKey from disconnected node1. Should timeout"
./Tests/delete.sh $1 "sampleKey" "{}"
echo "Attempting to update sampleKey with updatedKey in disconnected node1. Should timeout"
./Tests/put.sh $1 "newKey" "updatedKey" "{}"
echo "Reconnecting node1 ..."
./Tests/connect_node.sh node1
echo "Attempting to get sampleKey into node1. Should return sampleValue"
./Tests/get.sh $1 "sampleKey" "{}"
echo "Attempting to update sampleKey with updatedKey into node1."
./Tests/put.sh $1 "sampleKey" "updatedKey" "{}"
echo "Attempting to delete sampleKey into node1. Should delete"
./Tests/delete.sh $1 "sampleKey" "{}"