#!/bin/bash
# $1 = replica1 address
# $2 = replica2 address
set -x

# write sampleKey1 = value1 to replica1
./Tests/put.sh $1 "sampleKey1" "value1" "{}"
# read sampleKey1 from replica2 to make sure it's correct
./Tests/get_expected.sh $2 "sampleKey1" "{\"10.10.0.2:13800\":1,\"10.10.0.3:13800\":0}" "value1"

