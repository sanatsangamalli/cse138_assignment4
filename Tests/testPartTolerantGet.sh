./Tests/put.sh localhost:13802 sampleKey sampleValue {}
./Tests/put.sh localhost:13803 sampleKey sampleValue {}
./Tests/get.sh localhost:13804 sampleKey
./Tests/get.sh localhost:13805 sampleKey
 docker network disconnect kv_subnet node1
./Tests/get.sh localhost:13804 sampleKey
docker network disconnect kv_subnet node2
 ./Tests/get.sh localhost:13804 sampleKey