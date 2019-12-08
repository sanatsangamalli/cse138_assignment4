#!/bin/bash

#./Tests/put.sh localhost:13802 "sampleKey1" "value1" "{}"

#./Tests/get.sh localhost:13805 "sampleKey1" "{\"10.10.0.2:13800\":0,\"10.10.0.3:13800\":2}"

#./Tests/get.sh localhost:13805 "sampleKey1" "{\"10.10.0.2:13800\":0,\"10.10.0.3:13800\":2}"

#./Tests/put.sh localhost:13805 "sampleKey1" "value1" "{\"10.10.0.2:13800\":0,\"10.10.0.3:13800\":1}"

./Tests/put.sh localhost:13804 "sampleKey1" "value1" "{}"

./Tests/put.sh localhost:13804 "sampleKey1" "value1" "{}"