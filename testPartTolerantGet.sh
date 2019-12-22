./Tests/put.sh localhost:13802 sampleKey sampleValue {}
#./Tests/put.sh localhost:13803 sampleKey sampleValue {}
#./Tests/get.sh localhost:13804 sampleKey
./Tests/get.sh localhost:13805 sampleKey {}
 docker network disconnect kv_subnet node4
./Tests/get.sh localhost:13804 sampleKey {}
#docker network disconnect kv_subnet node2
 #./Tests/get.sh localhost:13804 sampleKey
./Tests/get.sh localhost:13807 sampleKey "{\"10.10.0.5:13800\":2,\"10.10.0.6:13800\":0,\"10.10.0.7:13800\":0}"