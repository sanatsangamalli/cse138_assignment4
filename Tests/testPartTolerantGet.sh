#!/bin/bash


./Tests/put.sh $1 sampleKey sampleValue {}
./Tests/put.sh $2 sampleKey sampleValue {}
./Tests/get.sh $3 sampleKey  "{}"
./Tests/get.sh $4 sampleKey  "{}"
 docker network disconnect kv_subnet node1
./Tests/get.sh $3 sampleKey "{}"
docker network disconnect kv_subnet node2
 ./Tests/get.sh $3 sampleKey "{}"
docker network connect kv_subnet node1
docker network connect kv_subnet node2