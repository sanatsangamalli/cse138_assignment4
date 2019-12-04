#!/bin/bash
# $1 = node address

# write a value and make sure it sticks
# write testKey1=value1
result=$(./Tests/put.sh $1 "testKey1" "value1")
echo ${result}
# confirm readValue = value1
resultValue=$(./Tests/get.sh $1 "testKey1" | jq '.value')

if [ $resultValue = "\"value1\"" ]; then
    echo "success: expected \"value1\", got $resultValue"
else
    echo "Failure: expected \"value1\", got $resultValue"
fi


# write a value to a different key and make sure that both keys are still in there
# write testKey2=value2
./Tests/put.sh $1 "testKey2" "value2"
# read testKey1
# confirm readValue = value1
./Tests/get.sh $1 "testKey1"

# read testKey2
# confirm readValue = value2
./Tests/get.sh $1 "testKey2"

# overwrite the first key with a new value and make sure it sticks and that the other value is unaffected
# write testKey1=value3
./Tests/put.sh $1 "testKey1" "value3"

# read testKey1
# confirm readValue = value3
./Tests/get.sh $1 "testKey1" "value1" 

# read testKey2
# confirm readValue = value2
./Tests/get.sh $1 "testKey2" "value2" 