from flask import Flask, request, render_template, jsonify, Response
from multiprocessing.dummy import Pool as ThreadPool
import os
import sys
import hashlib
import threading
import requests
import json
import operator
import math
import schedule
import random
import time
from http import HTTPStatus
# "Any node that does not respond within 5 seconds can broadly or generally be treated as 'failed'"
MAX_TIMEOUT=2

# update remaining requests (GET, PUT, DELETE) to use and update causal context and to gossip
# gossip implentation: on demand and periodically
# detecting partitions (some timeout less than 5 seconds (see spec), marking nodes as innactive and returning nacks to client)
	# only nack when you cannot reach any replicas from a given shard
# misc spec fulfillment (shard metadata, etc...)
# TESTTESTTESTTESTTESTTESTTESTTESTTESTTESTTESTTESTTESTTESTTESTTESTTESTTESTTESTTESTTESTTESTTESTTESTTESTTESTTESTTESTTESTTESTTESTTESTTESTTESTTESTTESTTESTTESTTESTTESTTESTTEST

# on gossip:
	# state machine replication
	# every time there's a change in state, place it in a list events mapping vector clock times to actions
	# when you gossip, take the combined list of all actions taken since last gossip and order them by causal relation
		# when two events are concurrent, order them by replica index
	# clear your list of actions and resume normal operation

class mainKeyVal:
	# managing up and down nodes
	# have a list of up nodes
		# nodes that have timed out recently are removed from list of up nodes
		# when receive gossip from down node, its up again

	def __init__(self, myView, repl_factor):
		self.dictionary = {} # Dictionary containing key-value pairs for this node
		
		self.configureNewView(myView.split(','), repl_factor)
		self.eventHistory = [] #storing a list of dictionaries representing put and delete events

		# initial setup to support a view change
		self.leadingViewChange = False # Is the current node the "leader" (initiating the view change)
		self.changingView = False # Is view currently being changed
		self.expectedReceiveCount = 0 # Number of keys this node is expected to have after a new view change
		self.receiveFinalMessageEvent = threading.Event() # Threading event to determine when node needs to wait before finalizing a view change
		
		self.gossipWait = random.randrange(1, max(len(self.view), 1))
		self.gossipThread = threading.Thread(target = self.runScheduledPoll)
		self.pollThread = threading.Thread(target = self.runScheduledGossip)

		self.gossipThread.start()
		self.pollThread.start()


	def runScheduledPoll(self):
		schedule.every(3).seconds.do(self.sendPoll)
		while True:
			schedule.run_pending()
			time.sleep(1)


	def runScheduledGossip(self):
		schedule.every(self.gossipWait).seconds.do(self.gossip)
		
		while True:
			schedule.run_pending()
			time.sleep(1)

	def sendPoll(self):
		for address in self.replicaStatus:
			if self.replicaStatus[address] == "unavailable":
				try:
					requests.post('http://'+ address + '/kv-store/poll', timeout = MAX_TIMEOUT)
				except TimeoutError:
					None
					#print("Failed to reach " + str(address))
				except:
					None
					#print("Failed to reach " + str(address))
				else:
					self.replicaStatus[address] = "available"
				

	def receivePoll(self, request):
		if self.replicaStatus[request.remote_addr] == "unavailable":
			self.replicaStatus[request.remote_addr] = "available"
		return 200

	# Returning key count has been removed from design doc
	# TODO: return actual causal-context
	def getShardMembership(self):
		shardCount = {}
		for shardId in self.shards:
			if shardId == self.myShard:
				shardCount[shardId] = len(self.dictionary)
			# "value from replica doesn't have to be most up to date
			else:
				shardData = self.getShardData(shardId)
				# Entire shard is down or something else went wrong
				if shardData[1] != HTTPStatus.OK:
					#print("Shard ID = " + str(shardId) + " failed to get shard data" , file = sys.stderr)
					None
				else:
					shardCount[shardId] = shardData[0].json["get-shard"]["key-count"]
		return jsonify({"shard-membership": {"message": "Shard membership retrieved successfully", "causal-context" : {}, "shards" : shardCount}}), 200

	# TODO: return actual causal-context
	# TODO: trigger gossip if inconsistency in key-counts/casual-contexts?
	# "dont service a newer context if you dont know about it"
	def getShardData(self, shard_id):
		if shard_id not in self.shards:
			return jsonify({"shard-membership": {"message": "Shard not found", "causal-context" : {}}}), 404
		shard = self.shards[shard_id]
		# I'm a node in the shard
		if os.environ['ADDRESS'] in shard:
			return jsonify({"get-shard": { "message" : "Shard information retrieved successfully", "shard-id": str(shard_id), "key-count": len(self.dictionary), "causal-context": {}, "replicas": shard }}), 200
		# Iterate over every node in the shard
		for node in shard:
			# Try nodes until 1 succeeds
			try:
				response = requests.get('http://'+ node + '/kv-store/key-count', timeout=MAX_TIMEOUT)
				jsonedResponse = response.json()
				keyCount = jsonedResponse["key-count"]
				return jsonify({"get-shard": { "message" : "Shard information retrieved successfully", "shard-id": str(shard_id), "key-count": keyCount, "causal-context": {}, "replicas": shard }}), 200
			except:
				return self.produceAvailabilityError("GET", causalContext)
				print(str(node) + "timedout when asked for key-count by" + os.environ['ADDRESS'] , file = sys.stderr)
		# NACK: All nodes timed out ...
		return jsonify({"get-shard": { "message" : "Shard down. All replicas timedout", "shard-id": str(shard_id)}}), 503

	def configureNewView(self, newView, repl_factor):
		self.view = newView
		self.view.sort() # Sort the view to ensure nodes can reference each other consistently

		# determine shards
		addresses = self.view

		# determine my shard
		self.numShards = len(newView)/int(repl_factor)

		self.shards = {}
		# #print("self.numShards " + str(self.numShards), file = sys.stderr)
		for i in range(0, int(self.numShards)):
			# empty list with repl_factor entries
			shard = [""]*int(repl_factor)
			# #print("shard" + str(shard), file = sys.stderr)
			self.shards[i] = shard
		# get my index in addresses, devide by repl_factor to select shard
		self.myShard = int(min(math.floor(addresses.index(os.environ['ADDRESS']) / int(repl_factor)), self.numShards-1))
		# #print("self.shards " + str(self.shards), file = sys.stderr)
		# #print("self.myShard " + str(self.myShard), file = sys.stderr)
		# populate shards the same way
		k = 0
		for address in newView:
			index = int(min(math.floor(addresses.index(address) / int(repl_factor)), self.numShards-1))
			self.shards[index][k%int(repl_factor)] = address
			k += 1

		print("shards", file=sys.stderr)
		print(self.shards, file=sys.stderr)

		self.replicaStatus = {} # values are "available" and "unavailable" 
		for address in self.shards[self.myShard]:
			if address != os.environ['ADDRESS']:
				self.replicaStatus[address] = "available"

		# prepare new vector clock
		# only set oldClock if we're not initialzing because oldClock doesn't exist in that case
		oldClock = {}
		if hasattr(self, 'vectorClock'):
			oldClock = self.vectorClock.copy()
		self.vectorClock = {}
		for address in self.view:
			if address in self.shards[self.myShard]:
				if address in oldClock:
					self.vectorClock[address] = oldClock[address]
				else:
					self.vectorClock[address] = 0
			
	def allReplicasAvailable(self):
		for address in self.replicaStatus:
			if self.replicaStatus[address] == "unavailable":
				return False

		return True

	def gossip(self):
		print("leading gossip", file=sys.stderr)
		eventLists = []
		eventLists.append(self.eventHistory)
		vectorClocks = {}

		# for each other replica
		for address in self.shards[self.myShard]:

			# send a message
			if address != os.environ['ADDRESS']:
				#print("gossiping with: " + address, file=sys.stderr)
				if self.replicaStatus[address] == "available":
					try:
						response = self.sendGossipMessage(address, self.eventHistory)
					except TimeoutError:
						# handle timeout case
						self.markUnavailable(address)
					except:
						self.markUnavailable(address)
					else:
						# #print("gossiped successfully:", file = sys.stderr)
						# #print(response, file = sys.stderr)
						# #print(response.json(), file = sys.stderr)
						# #print(type(response.text), file = sys.stderr)
						# receive list of events
						eventLists.append(response.json()["events"])
						# strip this list of values before my causal context
						vectorClocks[address] = response.json()["causal-context"]

		# merge all lists into single ordered list of events to apply
		finalList = self.mergeEventLists(eventLists)

		# then apply them
		self.applyEvents(finalList)

		# update vector clock for each available replica
		for address in vectorClocks:
			self.vectorClock = self.vectorClockMax(self.vectorClock, vectorClocks[address])

		# if all replicas were available, we can safely empty our event list, but should save it otherwise
		if self.allReplicasAvailable():
			#print("gossiped successfully with all peers, clearing event history", file=sys.stderr)
			self.eventHistory = []



	def applyEvents(self, eventList):
		for event in eventList:
			if event["type"] == "PUT":
				self.dictionary[event["key"]] = event["value"]
			elif event["type"] == "DELETE":
				if event["key"] in self.dictionary:
					del self.dictionary[event["key"]]
			


	def mergeEventLists(self, eventLists):
		finalList = []
		tempLists = []
		for eventList in eventLists:
			tempLists.append(eventList.copy())
		while self.someListHasValue(tempLists):
			# get starting value
			for eventList in tempLists:
				if len(eventList) > 0:
					bestEventList = eventList
					bestEvent = eventList[0]
					break
			
			# select a value
			for eventList in tempLists:
				for event in eventList:
					if self.eventABeforeEventB(event["causal-context"], tempLists.index(eventList), bestEvent["causal-context"], tempLists.index(bestEventList)):
						bestEventList = eventList
						bestEvent = event
			
			# add value to list
			tempLists[tempLists.index(bestEventList)].remove(bestEvent)
			finalList.append(bestEvent)

		return finalList


	def someListHasValue(self, eventLists):
		for eventList in eventLists:
			if len(eventList) > 0:
				return True
		return False

	# returns whether event A should be applied before event B
	def eventABeforeEventB(self, A, aReplica, B, bReplica):
		aLessThanB = self.vcLessThan(A, B)
		bLessThanA = self.vcLessThan(B, A)
		
		if not aLessThanB and not bLessThanA:
			# they're concurrent, resolve using replica id
			return aReplica < bReplica
		else:
			return aLessThanB

	def markUnavailable(self, address):
		self.replicaStatus[address] = "unavailable"
		#schedule polling

	def sendGossipMessage(self, address, history):
		try:
			response = requests.get('http://'+ address + '/kv-store/gossip', json={"events" : history, "causal-context" : self.vectorClock}, timeout=MAX_TIMEOUT)
		except TimeoutError:
			raise TimeoutError
		else:
			return response

	def respondToGossip(self, request):
		#print("Servicing gossip request:", file = sys.stderr)
		data = request.get_json()
		# update vector clock, but JUST THE ENTRY FOR THE SENDER
		address = request.remote_addr + ":13800"
		
		if address in self.shards[self.myShard]:
			#print("Request data:", file = sys.stderr)
			#print(data, file = sys.stderr)

			# combine message histories and apply
			if data["causal-context"][address] > self.vectorClock[address]:
				eventLists = []
				eventLists.append(self.eventHistory)
				eventLists.append(data["events"])
				self.applyEvents(self.mergeEventLists(eventLists))

				self.vectorClock[address] = data["causal-context"][address]

			return jsonify({"events" : self.eventHistory, "causal-context" : self.vectorClock}), 200
		else:
			return jsonify({"events" : [], "causal-context" : data["causal-context"]}), 200


	# Hash partitioning
	# Given a key, function returns the IP address of the node that key will be stored on
	def determineDestination(self, key_value):
		# determine shard
		shardDesination = self.determineShardDestination(key_value)
		# it it's my shard, return my address
		if shardDesination == self.myShard:
			return os.environ['ADDRESS']
		# if it's another shard, select an address from that shard and return it
		else:
			# find one known up node
				
			return self.shards[shardDesination][0]
		# hashVal = int(hashlib.sha1(key_value.encode('utf-8')).hexdigest(), 16) # First hash is returned as hex value, then converted
		# return self.view[hashVal % len(self.view)]

	def determineShardDestination(self, key_value):
		return int(hashlib.sha1(key_value.encode('utf-8')).hexdigest(), 16) % self.numShards

	# returns whether the vector clock A is less than the vector clock B
	def vcLessThan(self, A, B):
		existsElementLessThan = False
		for address in A:
			if address in B and A[address] < B[address]:
				existsElementLessThan = True
		
		noneGreater = True
		for address in A:
			if address in B and A[address] > B[address]:
				noneGreater = False
		return existsElementLessThan and noneGreater

	# returns the element-wise max of the two vectors A and B
	def vectorClockMax(self, A, B):
		# create composite vector
		composite = {}
		for address in A:
			composite[address] = A[address]
		for address in B:
			composite[address] = B[address]

		# save max for each element
		for address in composite:
			# if there's competition
			if address in A and address in B:
				composite[address] = max(A[address], B[address])
			# otherwise we already have the correct value
		return composite


	def outOfDateWRT(self, causalContext):
		if not bool(causalContext):
			return False

		#print("comparing contexts, mine:", file=sys.stderr)
		#print(self.vectorClock, file=sys.stderr)
		#print("comparing contexts, thiers:", file=sys.stderr)
		#print(causalContext, file=sys.stderr)
		
		isEqual = True
		for node in self.shards[self.myShard]:
			if node in causalContext and causalContext[node] != self.vectorClock[node]:
				isEqual = False
				break
		
		if isEqual:
			return False

		return not self.vcLessThan(causalContext, self.vectorClock)

	# Fulfills client GET requests
	def get(self, request, key_name):
		# check causal context
		req_data = request.get_json()
		causalContext = dict(req_data["causal-context"])

		#print("server: getting " + key_name, file = sys.stderr)

		shard_location = self.determineShardDestination(key_name)
		shard = self.shards[shard_location]
		
		# if I'm a replica in the target shard
		if os.environ['ADDRESS'] in shard:
			# if I have a vector clock that is out of date in comparison to the message
			if self.outOfDateWRT(causalContext):
				# gossip to make sure this read is causaly consistant
				self.gossip()

			# if, after gossiping, we still don't have a vector clock that's up to date, return a nack
			if self.outOfDateWRT(causalContext):
				return self.produceAvailabilityError("GET", causalContext)
				
			# increment my vector clock and return the requested value
			self.vectorClock[os.environ['ADDRESS']] += 1
			#print("getting " + key_name + " locally", file = sys.stderr)

			if key_name in self.dictionary:
				return jsonify({"doesExist":True, "message":"Retrieved successfully", "value":self.dictionary[key_name], "causal-context": self.vectorClockMax(self.vectorClock, causalContext)}), 200
			else:
				return jsonify({"doesExist":False, "message":"Error in GET", "error" : "Key does not exist", "causal-context" : self.vectorClockMax(self.vectorClock, causalContext)}), 404	
		# otherwise I need to forward the request to nodes in the target shard
		else:
			# Iterate over every node in the shard
			for node in shard:
				# Try nodes until 1 succeeds
				try:
					req_data = request.get_json(silent=True)
					# update timeouts
					if req_data is not None:
						response = requests.get('http://'+ node + '/kv-store/keys/' + key_name, data=json.dumps(req_data), headers=dict(request.headers), timeout=MAX_TIMEOUT)
					else:
						response = requests.get('http://'+ node + '/kv-store/keys/' + key_name, headers=dict(request.headers), timeout=MAX_TIMEOUT)
					json_response = response.json()
					json_response.update({'address': node})
					#print("forwarding " + key_name, file = sys.stderr)

					return json_response, response.status_code
					# return jsonify({"get-shard": { "message" : "Shard information retrieved successfully", "shard-id": str(shard_id), "key-count": keyCount, "causal-context": {}, "replicas": shard }}), 200
				except requests.exceptions.Timeout:
					return self.produceAvailabilityError("GET", causalContext)
					#print(str(node) + "timedout when asked for key=" + key_name + " by" + os.environ['ADDRESS'] , file = sys.stderr)
				except Exception as e:
					return self.produceAvailabilityError("GET", causalContext)
					#print(str(node) + "something else went wrong for key=" + key_name + " by" + os.environ['ADDRESS'] , file = sys.stderr)
			# NACK: All nodes timed out ...
			return self.produceAvailabilityError("GET", causalContext)#jsonify({"get": { "message" : "Shard down. All replicas timedout", "shard-id": str(shard_location)}}), 503
			
	# Fulfills client PUT requests
	def put(self, request, key_name):
		# check causal context
		req_data = request.get_json()
		causalContext = dict(req_data["causal-context"])
		
		if len(key_name) > 50:
			actual_dest = self.determineDestination(key_name[:50])
			if os.environ['ADDRESS'] == actual_dest: 
				return jsonify({"error":"Key is too long", "message":"Error in PUT", "causal-context" : self.vectorClockMax(self.vectorClock, causalContext)}), 400
			else: 
				return jsonify({"error":"Key is too long", "message":"Error in PUT", "causal-context" : self.vectorClockMax(self.vectorClock, causalContext), "address" : actual_dest}), 400
		shard_location = self.determineShardDestination(key_name)
		shard = self.shards[shard_location]

		if 'value' in req_data:
			#print("request had value", file=sys.stderr)
			shard_location = self.determineShardDestination(key_name)
			shard = self.shards[shard_location]
			# I'm a replica in target shard, just put/update locally
			if os.environ['ADDRESS'] in shard:
				# if I have a vector clock that is out of date in comparison to the message
				if self.outOfDateWRT(causalContext):
					# gossip to make sure this read is causaly consistant
					self.gossip()

				# if, after gossiping, we still don't have a vector clock that's up to date, return a nack
				if self.outOfDateWRT(causalContext):
					return self.produceAvailabilityError("PUT", causalContext)
					
				data = req_data['value']
				#print("saving value", file=sys.stderr)
				replaced = key_name in self.dictionary
				self.dictionary[key_name] = data
				if replaced:
					message = "Updated successfully"
					code = 200
				else:
					message = "Added successfully"
					code = 201
				# increment my vector clock
				self.vectorClock[os.environ['ADDRESS']] += 1
				event = {}
				event["type"] = "PUT"
				event["causal-context"] = self.vectorClock
				event["key"] = key_name
				event["value"] = data

				#print("Event:", file=sys.stderr)
				#print(event, file=sys.stderr)

				self.eventHistory.append(event)
				#print("History:", file=sys.stderr)
				#print(self.eventHistory, file=sys.stderr)

				return jsonify({"doesExist":True, "message":message, "replaced":replaced, "causal-context": self.vectorClockMax(self.vectorClock, causalContext)}), code
			else:
				# Iterate over every node in the shard
				# TODO: Update vector clock everytime a message is sent???
				for node in shard:
					print("trying node:" + str(node), file = sys.stderr)
					# Try nodes until 1 succeeds
					try:
						response = requests.put('http://'+ node + '/kv-store/keys/' + key_name, data=json.dumps(req_data), headers=dict(request.headers), timeout=MAX_TIMEOUT)
						json_response = response.json()
						json_response.update({'address': node})
						return json_response, response.status_code
					except requests.exceptions.Timeout:
						return self.produceAvailabilityError("PUT", causalContext)
						print(str(node) + "timedout when asked for key=" + key_name + " by" + os.environ['ADDRESS'] , file = sys.stderr)
					except Exception as e:
						return self.produceAvailabilityError("PUT", causalContext)
						print(e)
						print(str(node) + "something else went wrong for key=" + key_name + " by" + os.environ['ADDRESS'] , file = sys.stderr)
				# NACK: All nodes timed out ...
				return self.produceAvailabilityError("PUT", causalContext)#jsonify({"put": { "message" : "Shard down. All replicas timedout", "shard-id": str(shard_location)}}), 503
			# return jsonify({"doesExist":True, "message":message, "replaced":replaced, "causal-context": self.vectorClockMax(self.vectorClock, causalContext)}), 200
		# Forward request to nodes in target shard
		else:
			print("request had no value", file=sys.stderr)
			responseData = {"error":"Value is missing", "message":"Error in PUT", "causal-context" : causalContext}
			
			key_hash = self.determineDestination(key_name)
			if key_hash != os.environ['ADDRESS']:
				responseData['address'] = key_hash

			return jsonify(responseData), 400

			
			

		# if req_data is not None and 'value' in req_data:
		# 	if len(self.view) != 0: # Make sure list is non empty
		# 		key_hash = self.determineDestination(key_name)
		# 		if os.environ['ADDRESS'] == key_hash:
		# 			data = req_data['value']
		# 			replaced = key_name in self.dictionary
		# 			self.dictionary[key_name] = data
		# 			if replaced:
		# 				message = "Updated successfully"
		# 				code = 200
		# 			else:
		# 				message = "Added successfully"
		# 				code = 201
		# 			self.vectorClock[os.environ['ADDRESS']] += 1
		# 			return jsonify({"message":message, "replaced":replaced}), code
		# 		else:
		# 			try:
		# 				response = requests.put('http://'+ key_hash + '/kv-store/keys/' + key_name, data=json.dumps(req_data), headers=dict(request.headers), timeout=MAX_TIMEOUT)
		# 			except requests.exceptions.Timeout:
		# 				return self.produceTimeoutError('PUT')
		# 			except:
		# 				return jsonify({'error': 'Node in view (' + key_hash + ') does not exist', 'message': 'Error in PUT'}), 503
		# 			json_response = response.json()
		# 			json_response.update({'address': key_hash})
		# 			return json_response, response.status_code
		# 	else:
		# 		return jsonify({"error:":"List is empty", "message":"Error in PUT"}), 400
		# else:
		# 	return jsonify({"error:":"Value is missing", "message":"Error in PUT"}), 400
	
	# Fulfills client DELETE requests
	def delete(self, request, key_name):
		# check causal context
		req_data = request.get_json()
		causalContext = dict(req_data["causal-context"])
		
		if key_name in self.dictionary:
			# if I have a vector clock that is out of date in comparison to the message
			if self.outOfDateWRT(causalContext):
				# gossip to make sure this read is causaly consistant
				self.gossip()

			# if, after gossiping, we still don't have a vector clock that's up to date, return a nack
			if self.outOfDateWRT(causalContext):
				return self.produceAvailabilityError("DELETE", causalContext)
				
			del self.dictionary[key_name]
			self.vectorClock[os.environ['ADDRESS']] += 1
			event = {}
			event["type"] = "DELETE"
			event["causal-context"] = self.vectorClock
			event["key"] = key_name
			self.eventHistory.append(event)

			return jsonify({"doesExist":True, "message":"Deleted successfully", "causal-context" : self.vectorClockMax(self.vectorClock, causalContext)}), 200
		else:
			if len(self.view) != 0: # Make sure list is non empty
				key_hash = self.determineDestination(key_name)
				if os.environ['ADDRESS'] == key_hash:
					return jsonify({"doesExist":False, "error":"Key does not exist", "message":"Error in DELETE"}), 404    
				else:
					try:
						if req_data is not None:
							response = requests.delete('http://'+ key_hash + '/kv-store/keys/' + key_name, data=json.dumps(req_data), headers=dict(request.headers), timeout=MAX_TIMEOUT)
						else:
							response = requests.delete('http://'+ key_hash + '/kv-store/keys/' + key_name, headers=dict(request.headers), timeout=MAX_TIMEOUT)
					except requests.exceptions.Timeout:
						return self.produceAvailabilityError('DELETE', causalContext)
					except:
						return jsonify({'error': 'Node in view (' + key_hash + ') does not exist', 'message': 'Error in DELETE', 'causal-context': causalContext}), 503
					json_response = response.json()
					json_response.update({'address': key_hash})
					return json_response, response.status_code
			else:
				return jsonify({'error': 'Missing VIEW environmental variable', 'message': 'Error in GET', 'causal-context': causalContext}), 503

	# Initiate a view change
	# Function is called by the node that received the view change request 
	def viewChange(self, request):
		# send prime message with view to other ip address in view 
		
		# I'm changing the view, and I'm the leader
		self.changingView = True
		self.leadingViewChange = True

		# retrieve the new view from the request
		req_data = request.get_json()
		newView = req_data["view"] # Variable containing the new view
		repl_factor = req_data["repl-factor"]

		# retrieve my own address
		myAddress = os.environ['ADDRESS']
		#print("myAddress", file=sys.stderr)
		#print(myAddress, file=sys.stderr)

		# create a list of everyone in the view except me
		receivers = newView.copy()
		receivers.remove(myAddress)

		# Create multiple threads to send a prime message to all other nodes in the view
		pool = ThreadPool(len(receivers))

		arguments = []

		for receiver in receivers:
			arguments.append((receiver, newView, repl_factor))#(",".join(newView))

		resultingMsgVectors = pool.starmap(self.sendPrimeMessage, arguments)
		pool.close()

		self.totalMsgVector = self.prime(myAddress, (",".join(newView)), repl_factor)[0].get_json()

		pool.join()

		# Add message vector to our running total, to keep track of how many keys each node will have
		for response in resultingMsgVectors:
			vectorResponse = response.json()
			for address in self.totalMsgVector:
				self.totalMsgVector[address] += vectorResponse[address]

		self.receiveFinalMessageEvent = threading.Event() 
		# If we've received the last one, send start message with final total
		# each element should be of format i.e. { "address": "10.10.0.2:13800", "key-count": 5 },

		hostShard = self.startChange(self.totalMsgVector[myAddress]).get_json() # Leading node send out its keys first
		#print("hostShard", file=sys.stderr)
		#print(hostShard, file=sys.stderr)
		hostShard["address"] = os.environ["ADDRESS"]
		shardPool = ThreadPool(len(receivers))
		shards = shardPool.map(self.sendStartMessage, receivers) # Signal other nodes to send keys
		shardPool.close()

		# Leading node waits to receive all its keys
		if self.expectedReceiveCount > 0:
			self.receiveFinalMessageEvent.wait()

		shardPool.join()

		# Loop through shards to get all key counts and construct JSON response
		for idx, shard in enumerate(shards):
			shards[idx] = {"address": shard.json()["address"], "key-count": shard.json()["key-count"]}
		hostShard['key-count'] = len(self.dictionary)
		shards.append(hostShard) # Append the leading node's shard
		self.changingView = False
		self.leadingViewChange = False

		return jsonify({"message": "View change successful", "shards": shards, "causal-context": self.vectorClock}), 200 

	# Leading node send prime message to all nodes in view
	def sendPrimeMessage(self, address, newView, repl_factor):
		#print("sent prime message to " + address, file=sys.stderr)
		#print(newView, file=sys.stderr)
		response = requests.get('http://'+ address + '/kv-store/view-change/receive?view='+ (",".join(newView) + "&repl-factor=" + str(repl_factor)),timeout=MAX_TIMEOUT)
		#print("received prime response from " + address, file=sys.stderr)
		return response

	# Leading node send start message to all nodes in view
	def sendStartMessage(self, address):
		return requests.post('http://'+ address + '/kv-store/view-change/receive?count=' + str(self.totalMsgVector[address]), timeout=MAX_TIMEOUT)

	# followers
	# Prepare for a view change by determining how many keys will be sent to each node
	def prime(self, host, newView, repl_factor):

		self.gossip()

		self.changingView = True
		self.stagedMessages = {}

		#print("NEW VIEW REPLFACTOR: " + str(repl_factor), file=sys.stderr)

		self.configureNewView(newView.split(','), repl_factor)
		self.expectedReceiveCount = 0 # Number of keys a node is expected to receive

		# Initialize message vector
		messageVector = {}
		for address in self.view:
			messageVector[address] = 0

		# Determine how many keys need to be sent to each node
		for key in self.dictionary:
			destinationShard = self.determineShardDestination(key)
			if destinationShard != self.myShard:
				myIndexInShard = self.shards[self.myShard].index(os.environ['ADDRESS'])
				messageVector[self.shards[destinationShard][myIndexInShard]] += 1
				self.stagedMessages[key] = self.shards[destinationShard][myIndexInShard]

		#print("priming", file = sys.stderr)

		return jsonify(messageVector), 200

	# Send out all keys that do not belong to the current node
	def startChange(self, receiveCount):
		# Store message vector
		self.expectedReceiveCount += receiveCount

		# Send staged messages, if any
		if len(self.stagedMessages) > 0:
			messagePool = ThreadPool(len(self.stagedMessages))
			messagePool.map(self.sendKeyValue, self.stagedMessages)
			messagePool.close()
			messagePool.join()

		# Block if not the leading node and this node is still expecting a key (to be sent from another node)
		if self.leadingViewChange == False and self.expectedReceiveCount > 0:
			self.receiveFinalMessageEvent.wait()

		# Delete all keys that have been sent
		for key in self.stagedMessages:
			del self.dictionary[key]

		self.changingView = False
		return jsonify({"address": request.host, "key-count": len(self.dictionary)})


	# store that dang thing and decrement the correct element of the message vector
	# if all elements of the vector are zero, send done message with my final message total 
	# set change view to false here only if not arbiter
	def receiveValue(self, key, value, sender):

		self.dictionary[key] = value
		self.expectedReceiveCount -= 1

		if self.expectedReceiveCount == 0:
			self.receiveFinalMessageEvent.set() # Signal threading event to stop blocking (all expected keys received)
		return jsonify({"message":"Success"}), 200

	def clear(self):
		#print("WARNING: CLEARING ALL KEYS", file = sys.stderr)
		deletedElementCount = len(self.dictionary)
		self.dictionary = {}
		return jsonify({"message":"Success", "keys deleted" : deletedElementCount}), 200

	# Send a key to another node
	def sendKeyValue(self, key):
		return requests.put('http://'+ self.stagedMessages[key] + '/kv-store/view-change/receive?key=' + key + '&value=' + self.dictionary[key],timeout=20)

	# return jsonify of dict size 
	def getKeyCount(self, request):
		data = request.get_json()
		causalContext = data['causal-context']

		# if I have a vector clock that is out of date in comparison to the message
		if self.outOfDateWRT(causalContext):
			# gossip to make sure this read is causaly consistant
			self.gossip()

		# if, after gossiping, we still don't have a vector clock that's up to date, return a nack
		if self.outOfDateWRT(causalContext):
			return self.produceAvailabilityError("DELETE", causalContext)

		self.vectorClock[os.environ['ADDRESS']] += 1

		return jsonify({"message": "Key count retrieved successfully", "key-count": len(self.dictionary), "causal-context": self.vectorClockMax(causalContext, self.vectorClock)}), 200 

	def produceAvailabilityError(self, httpMethod, clientCausalContext):
		return jsonify({'error': 'Unable to satisfy request', 'message': 'Error in ' + httpMethod, 'causal-context' : clientCausalContext}), 503