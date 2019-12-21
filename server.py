# CSE 138 Assignment 4
from flask import Flask, request, render_template, jsonify
import os
import sys
from mainKeyVal import mainKeyVal

DEBUG = True

app = Flask(__name__)

@app.route("/")
def begin():
	return "welcome to the home page"

# Function to perform main key-value store operations (GET, PUT, DELETE)
@app.route("/kv-store/keys/<string:key_name>", methods = ["GET","PUT", "DELETE"])
def keyValStore(key_name):
	if request.method == "PUT":
		return server.put(request, key_name)
	elif request.method == "GET":
		#print("getting " + key_name, file = sys.stderr)
		return server.get(request, key_name)
	elif request.method == "DELETE":
		return server.delete(request, key_name)
	else:
		#print("Method not supported", file = sys.stderr)
		return jsonify({"message": "Method Not Supported"}), 404 

# Function to return the key-count
@app.route("/kv-store/key-count", methods = ["GET"])
def keyCount():
	if request.method == "GET":
		return server.getKeyCount()
	else:
		return jsonify({"message": "Method Not Supported"}), 404 

# Function to return the shard-membership. Every shard's id and the number of (unique) keys that each shard holds
@app.route("/kv-store/shards", defaults={'shard_id': None}, methods = ["GET"])
# Function to return the number of keys stored by a shard and replica ips
@app.route("/kv-store/shards/<int:shard_id>", methods = ["GET"])
def shards(shard_id): # shard_id optional
	# All shards
	if shard_id == None:
		return server.getShardMembership()
		# return jsonify({"message": "/kv-store/shards endpoint not implemented yet"}), 501 
	else:
		return server.getShardData(shard_id)


# Function called when a view change is requested
@app.route("/kv-store/view-change", methods = ["PUT", "prime",	"startChange", "receiveValue"])
def view_change():
	#print("processing view change?", file=sys.stderr)
	if request.method == "PUT":
		return server.viewChange(request)
	else:
		return jsonify({"message": "Method Not Supported"}), 404 

# Internal endpoint used between nodes in order to deal with the view change
# protocol (sends keys between nodes, messaging system between nodes)
@app.route("/kv-store/view-change/receive", methods = ["PUT", "GET", "POST"])
def receive():
	if request.method == "PUT":
		arguments = request.args.to_dict()
		new_key = arguments["key"]
		new_value = arguments["value"]
		address = request.remote_addr
		return server.receiveValue(new_key, new_value, address) # Node receives a key from another node
	elif request.method == "GET":
		arguments = request.args.to_dict() # Return vector of message counts
		#print("receiving request to prime: factor = " + str(arguments["repl-factor"]), file=sys.stderr)
		return server.prime(request.host, arguments["view"], arguments["repl-factor"])
	elif request.method == "POST":
		arguments = request.args.to_dict()
		count = int(arguments["count"])
		return server.startChange(count) # Node begins sending out its keys
	else:
		return jsonify({"message": "Method Not Supported"}), 404

@app.route("/kv-store/gossip", methods = ["GET"])
def gossip():
	#print(request, file = sys.stderr)
	return server.respondToGossip(request)

@app.route("/kv-store/poll")
def poll():
	return server.receivePoll(request)

@app.route("/kv-store/clear", methods = ["DELETE"])
def clear():
	return server.clear()

if __name__ == "__main__":
	if 'VIEW' in os.environ:
		server = mainKeyVal(os.environ['VIEW'], os.environ['REPL_FACTOR'])
	app.run(debug=True, host = '0.0.0.0', port = 13800, threaded = True)
