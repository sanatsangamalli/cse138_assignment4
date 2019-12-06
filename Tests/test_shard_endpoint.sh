#!/bin/bash
# $1 = node1 address
# $2 = node2 address
# $3 = node3 address
# $4 = node4 address

# TEST1: Test without any data in shards (immediately after running after all 4 nodes)
echo "TEST1: Testing shard membership when all shards are empty"
echo "Testing endpoint http://$4/kv-store/shards"
echo "Confirm node 4 sees all shards (was given full view)"
./Tests/get_shard_membership.sh $4 "{}"

# TEST2: Add data to shard1 and test shard endpoints
echo "TEST2: Add data to shard0 and test shard endpoints"

echo "PUT testKey1 = value1 on node1"
./Tests/put.sh $1 "testKey1" "value1" "{}"

echo "PUT testKey2 = value2 on node1"
./Tests/put.sh $2 "testKey2" "value2" "{}"

echo "Testing endpoint http://$4/kv-store/shards"
echo "Confirm shard membership views updated data"
./Tests/get_shard_membership.sh $4 "{}"
# TEST3: Add data to shard2 and test shard endpoints

# TEST4: Remove nodes until only 1 node is up per shard 

# TEST5: Kill 1 shard and test shard membership

localhost:13802