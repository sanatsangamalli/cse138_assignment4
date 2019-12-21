# ------------------------------
# Run Docker containers
echo "clearing all previous containers..."

echo "stop first:"
docker stop $(docker ps -a -q)
echo "then remove:"
docker rm $(docker ps -a -q)

echo "done"

path_to_dockerfile="."

echo "creating docker subnet..."
docker network create --subnet=10.10.0.0/16 kv_subnet
echo "done"

echo "rebuilding Dockerfile"
docker build -t kv-store:4.0 $path_to_dockerfile
echo "done"


# example node addresses
addr1="10.10.0.2:13800"
addr2="10.10.0.3:13800"
addr3="10.10.0.4:13800"
addr4="10.10.0.5:13800"
addr5="10.10.0.6:13800"
addr6="10.10.0.7:13800"

#host="192.168.99.100"
host="127.0.0.1"
#host="localhost"
externalAddr1="$host:13802"
externalAddr2="$host:13803"
externalAddr3="$host:13804"
externalAddr4="$host:13805"
externalAddr5="$host:13806"
externalAddr6="$host:13807"

# convenience variables
initial_full_view="${addr1},${addr2}"
full_view=${initial_full_view},${addr3},${addr4}
full_view2=${full_view},${addr5},${addr6}

read -d '' view_change_data << "VIEW_STR"
{
    "causal-context": {},
    "repl-factor"   : 2,
    "view"          : [
        "10.10.0.2:13800",
        "10.10.0.3:13800",
        "10.10.0.4:13800",
        "10.10.0.5:13800"
    ]
}
VIEW_STR

echo "running first two nodes with initial full view: ${initial_full_view}" 

docker run --name="node1"        --net=kv_subnet     \
           --ip=10.10.0.2        -p 13802:13800      \
           -e ADDRESS="${addr1}"                     \
           -e VIEW=${initial_full_view}              \
           -e REPL_FACTOR=2                          \
           -d                                       \
           kv-store:4.0

echo "ran node1"
echo "creating terminal for node1..."
#mintty -h always -D ./attach.sh node1
mintty -h always -D ./attach.sh node1
# OSX only: launch new terminal window, at that path, and run ./attach.sh 
#osascript -e 'tell app "Terminal" to do script "cd '/Users/edgarh/Code/CSE138/cse138_assignment4' && ./attach.sh node1" '

echo "done"

docker run --name="node2"        --net=kv_subnet     \
           --ip=10.10.0.3        -p 13803:13800      \
           -e ADDRESS="${addr2}"                     \
           -e VIEW=${initial_full_view}              \
           -e REPL_FACTOR=2                          \
            -d                                       \
           kv-store:4.0

echo "ran node2"
echo "creating terminal for node2..."
 mintty -D ./attach.sh node2
#osascript -e 'tell app "Terminal" to do script "cd '/Users/edgarh/Code/CSE138/cse138_assignment4' && ./attach.sh node2" '


echo "done"

# ------------------------------
# add a key

# echo "PUT request on node2, sampleKey=sampleValue"
# curl --request PUT                                                \
#      --header    "Content-Type: application/json"                 \
#      --data      "{'value': 'sampleValue'}" \
#      --write-out "%{http_code}\n"                                 \
#      -v -4\
#      http://${externalAddr1}/kv-store/keys/sampleKey
# echo "done"
# #, 'causal-context': {}
# <<'expected_response'
# {
#     "message" : "Added successfully",
#     "replaced": "false"
# }
# status code: 201
# expected_response


# curl --request GET                             \
#      --header "Content-Type: application/json" \
#      --write-out "%{http_code}\n"              \
#      --data      '{"causal-context": {}}'      \
#      http://${externalAddr2}/kv-store/keys/sampleKey # should be externalAddr1


# <<'expected_response'
# {
#     "doesExist": "true",
#     "message"  : "Retrieved successfully",
#     "value"    : "sampleValue",
#     "address"  : "10.10.0.3:13800"
# }

# status code: 200
# expected_response


# ------------------------------
# Now we start a new node and add it to the existing store

docker run --name="node3" --net=kv_subnet                          \
           --ip=10.10.0.4  -p 13804:13800                          \
           -e ADDRESS="${addr3}"                                   \
           -e VIEW="${full_view}"                                  \
           -e REPL_FACTOR=2                                        \
            -d                                                     \
           kv-store:4.0

echo "ran node3"
echo "creating terminal for node3..."
mintty -D ./attach.sh node3
#osascript -e 'tell app "Terminal" to do script "cd '/Users/edgarh/Code/CSE138/cse138_assignment4' && ./attach.sh node3" '

echo "done"

docker run --name="node4" --net=kv_subnet                          \
           --ip=10.10.0.5  -p 13805:13800                          \
           -e ADDRESS="${addr4}"                                   \
           -e VIEW="${full_view}"                                  \
           -e REPL_FACTOR=2                                        \
            -d                                                     \
           kv-store:4.0

echo "ran node4"
echo "creating terminal for node4..."
mintty -D ./attach.sh node4
#osascript -e 'tell app "Terminal" to do script "cd '/Users/edgarh/Code/CSE138/cse138_assignment4' && ./attach.sh node4" '

echo "done"
echo "all 4 nodes running"
# curl --request PUT                                                \
#      --header    "Content-Type: application/json"                 \
#      --data      '{"value": "sampleValue"}' \
#      --write-out "%{http_code}\n"                                 \
#      -v -4\
#      http://${externalAddr4}/kv-store/keys/sampleKey

sleep 2
echo "changing view to include node3 and node4"
curl --request PUT                                                 \
     --header "Content-Type: application/json"                     \
     --data "$view_change_data"                                      \
     --write-out "%{http_code}\n"                                  \
     http://${externalAddr3}/kv-store/view-change

sleep 2
docker run --name="node5" --net=kv_subnet                          \
           --ip=10.10.0.6  -p 13806:13800                          \
           -e ADDRESS="${addr5}"                                   \
           -e VIEW="${full_view2}"                                  \
           -e REPL_FACTOR=2                                        \
            -d                                                     \
           kv-store:4.0
		   
		   
mintty -D ./attach.sh node5

docker run --name="node6" --net=kv_subnet                          \
           --ip=10.10.0.7  -p 13807:13800                          \
           -e ADDRESS="${addr6}"                                   \
           -e VIEW="${full_view2}"                                  \
           -e REPL_FACTOR=2                                        \
            -d                                                     \
           kv-store:4.0
		   
mintty -D ./attach.sh node6

read -d '' view_change_data2 << "VIEW_STR"
{
    "causal-context": {},
    "repl-factor"   : 3,
    "view"          : [
        "10.10.0.2:13800",
        "10.10.0.3:13800",
        "10.10.0.4:13800",
        "10.10.0.5:13800",
		"10.10.0.6:13800",
        "10.10.0.7:13800"
    ]
}
VIEW_STR

sleep 2

curl --request PUT                                                 \
     --header "Content-Type: application/json"                     \
     --data "$view_change_data2"                                      \
     --write-out "%{http_code}\n"                                  \
     http://${externalAddr1}/kv-store/view-change

# echo "done"
# curl --request GET                                                 \
#      --header "Content-Type: application/json"                     \
#      --write-out "%{http_code}\n"                                  \
#      --data "{\"causal-context\": {}}"                             \
#      http://${externalAddr3}/kv-store/keys/sampleKey

# <<'expected_response'
# {
#     "doesExist": "true",
#     "message"  : "Retrieved successfully",
#     "value"    : "sampleValue",
#     "address"  : "10.10.0.2:13800"
# }

# status code: 200
# expected_response

#./Tests/test_all.sh $externalAddr1 $externalAddr2 $externalAddr3 $externalAddr4
# dummyAddress="10.10.0.9:13800"

# docker run --name="dummyNode" --net=kv_subnet                          \
#             -d                                                     \
#            --ip=10.10.0.9  -p 13809:13800                          \
#            -e ADDRESS="${dummyAddress}"                            \
#            -e VIEW="${dummyAddress}"                                  \
#            -e REPL_FACTOR=1                                        \
#            kv-store:4.0

# mintty -h always -D ./attach.sh dummyNode


#docker exec node1 ./Tests/test_all.sh $addr1 $addr2 $addr3 $addr4
#./Tests/test_all.sh $externalAddr1 $externalAddr2 $externalAddr3 $externalAddr4
#./Tests/test_shard_endpoint.sh $externalAddr1 $externalAddr2 $externalAddr3 $externalAddr4
#./Tests/test_write_read_replica.sh $externalAddr1 $externalAddr2
#./Tests/test_partition_recovery.sh $externalAddr1 $externalAddr2
#docker exec dummyNode ./Tests/test_write_read.sh $addr4