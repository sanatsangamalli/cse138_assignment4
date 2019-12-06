#!/bin/bash
# $1 = node name

docker network connect kv_subnet $1
