#!/bin/bash
# $1 = node address
# $2 = key
# $3 = causal-context
# $4 = expected value

echo "Checking key: $2 for expected value: $4 on node: $1"
echo "{\"causal-context\": $3}"

#./Tests/get.sh $1 $2 $3
output=$(./Tests/get.sh $1 $2 $3 )
echo $output
resultValue=$(echo $output | jq '.value')

if [[ $resultValue = "\"$4\"" ]]; then
    echo "Success: expected \"$4\", got $resultValue"
else
    echo "Failure: expected \"$4\", got $resultValue"
fi