#!/bin/bash
# $1 = node1 address
# $2 = node2 address
# $3 = node3 address
# $4 = node4 address

echo "TESTING ALL"

# this tests basic read-write functionality, and also tests replication and sharding for reads and writes
./Tests/test_write_read.sh $1
./Tests/clear_all_keys.sh $1 $2 $3 $4

./Tests/test_write_read.sh $2
#./Tests/clear_all_keys.sh $1 $2 $3 $4

./Tests/test_write_read.sh $3
#./Tests/clear_all_keys.sh $1 $2 $3 $4

./Tests/test_write_read.sh $4
#./Tests/clear_all_keys.sh $1 $2 $3 $4

# clear all
#./Tests/clear_all_keys.sh $1 $2 $3 $4

#echo "test_put_timeout"
#./Tests/test_put_timeout.sh

#./Tests/clear_all_keys.sh $1 $2 $3 $4

echo "test_timeout"
./Tests/test_timeout.sh $4

#./Tests/clear_all_keys.sh $1 $2 $3 $4

echo "testPartTolerantGet"
./Tests/testPartTolerantGet.sh $1 $2 $3 $4