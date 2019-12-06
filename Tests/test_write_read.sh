#!/bin/bash
set -x
# $1 = node address

# write a value and make sure it sticks
# write testKey1=value1

echo "putting testKey1 = value1 on $1"
./Tests/put.sh $1 "testKey1" "value1" "{}"
# # confirm readValue = value1
./Tests/get_expected.sh $1 "testKey1" "{}" "value1"

# write a value to a different key and make sure that both keys are still in there
# write testKey2=value2
echo "putting testKey2 = value2 on $1"
./Tests/put.sh $1 "testKey2" "value2" "{}"

# read testKey1
# confirm readValue = value1
./Tests/get_expected.sh $1 "testKey1" "{}" "value1"

# read testKey2
# confirm readValue = value2
./Tests/get_expected.sh $1 "testKey2" "{}" "value2"

# overwrite the first key with a new value and make sure it sticks and that the other value is unaffected
# write testKey1=value3
echo "replacing testKey1 = value3 on $1"
./Tests/put.sh $1 "testKey1" "value3" "{}"

# read testKey1
# confirm readValue = value3
./Tests/get_expected.sh $1 "testKey1" "{}" "value3"

# read testKey2
# confirm readValue = value2
./Tests/get_expected.sh $1 "testKey2" "{}" "value2"