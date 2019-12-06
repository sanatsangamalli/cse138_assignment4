echo "Putting sampleKey2 into some node1"
./Tests/put.sh localhost:13805 sampleKey2 sampleValue2
echo "Disconnecting node1"
./Tests/disconnect_node.sh node1
echo "Attempting to put sampleKey2 into some node1. Should timeout"
./Tests/put.sh localhost:13805 sampleKey2 sampleValue2