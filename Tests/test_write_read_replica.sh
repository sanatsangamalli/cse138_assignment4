#!/bin/bash
# $1 = replica1 address
# $2 = replica2 address
set -x

# write sampleKey1 = value1 to replica1
#./Tests/put.sh 127.0.0.1:13802 "sampleKey1" "value10" "{}"
# read sampleKey1 from replica2 to make sure it's correct
#./Tests/get.sh 127.0.0.1:13802 "sampleKey1" "{\"10.10.0.2:13800\":1,\"10.10.0.3:13800\":0,\"10.10.0.4:13800\":0}"
#./Tests/put.sh 127.0.0.1:13803 "sampleKey1" "value5" "{\"10.10.0.2:13800\":2,\"10.10.0.3:13800\":0,\"10.10.0.4:13800\":0}"
./Tests/get.sh 127.0.0.1:13802 "sampleKey1" "{\"10.10.0.2:13800\":2,\"10.10.0.3:13800\":1,\"10.10.0.4:13800\":0}"