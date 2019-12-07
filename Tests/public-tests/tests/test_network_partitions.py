import time
import logging
import unittest

import requests

from public_tests.tools import NodeNetwork, NodeContainer


logger = logging.getLogger('{}.{}'.format('tests', 'sharded-simple'))
logger.setLevel(logging.INFO)


class NetworkPartitionTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Build docker image and create subnet
        """

        # TODO: change this or parameterize it
        cls.image_name = 'cse138/kv-store:4.0'

        # clear subnets we want to create in case they exist
        NodeNetwork.remove_subnets_by_name(['kv_subnet', 'partition_subnet'])

        # create desired subnets
        cls.kv_subnet        = NodeNetwork.for_subnet('kv_subnet', '10.10.0.0/16')
        cls.partition_subnet = NodeNetwork.for_subnet('partition_subnet', '10.11.0.0/16')

    @classmethod
    def tearDownClass(cls):
        cls.kv_subnet.remove()
        cls.partition_subnet.remove()

    def setUp(self):
        """
        setUp runs before every test case, so this is where we make sure nodes aren't running (just
        in case tearDown didn't run or we have a "dirty" state), and then we start the nodes we
        want to run.
        """

        self.path_to_logfile = None

        # ------------------------------
        # Container management (we use 6 nodes, IDs range from 1 to 6 and IP addresses from 2 to 7)

        # clean possibly existing containers
        node_names = ['node{}'.format(node_id) for node_id in range(1, 7)]
        NodeContainer.clean_containers_by_name(node_names)

        # start desired containers
        cluster_view    = ['10.10.0.{}:13800'.format(node_id) for node_id in range(2, 8)]
        self.core_nodes = {
            'node{}'.format(node_id): NodeContainer.run(
                                          image=self.__class__.image_name,
                                          name='node{}'.format(node_id),
                                          ip='10.10.0.{}'.format(node_id + 1),
                                          view=','.join(cluster_view),
                                          command='run_sharded_server',
                                          port='13800'
                                      )
            for node_id in range(1, 7)
        }

        # connect container to desired subnet (start with primary subnet)
        for node_name, node_container in self.core_nodes.items():
            self.__class__.kv_subnet.connect(node_container, ip=node_container.ip)

    def tearDown(self):
        """
        tearDown runs after every test case, so this is where we shutdown nodes.
        """

        # iterate over each running node
        for node_name, node_container in self.core_nodes.items():

            # write container's logs to a file for the test, if one was set
            if self.path_to_logfile:
                with open(self.path_to_logfile, 'a') as log_handle:
                    log_handle.write(node_container.container.logs().decode(encoding='utf-8'))

            # disconnect the node from the subnet
            self.__class__.kv_subnet.disconnect(node_container)

            # cleanup the node
            node_container.stop()
            node_container.remove()

    # ------------------------------
    # Unit test definitions
    def test_partition_one_node(self):
        """
        This is a simple test to try and add a flavor of network partitions to causally ordered
        writes (the example from the assignment spec).
        """

        self.path_to_logfile = 'partition.1.test.log'

        # variable setup
        uri_template      = 'http://{}:{}/kv-store/keys/{}'
        partition_node    = self.core_nodes['node4']
        causal_context    = {}
        key_name, key_val = 'sampleKey', 10

        # partition the node
        self.__class__.kv_subnet.disconnect(partition_node)
        self.__class__.partition_subnet.connect(partition_node)

        # write a value for a key
        response = requests.put(
            uri_template.format(partition_node.ip, '13800', key_name),
            json={'value': key_val, 'causal-context': causal_context}
        )

        causal_context = response.json().get('causal-context', {})

        # read from a different node
        response = requests.get(
            uri_template.format(partition_node.ip, '13800', key_name),
            json={'causal-context': causal_context}
        )
        causal_context = response.json().get('causal-context', {})

        # heal partition
        self.__class__.partition_subnet.disconnect(partition_node)
        self.__class__.kv_subnet.connect(partition_node)

        # wait a number of seconds equal to number of replicas for gossip and then try reading
        time.sleep(partition_node.repl_factor)
        response = requests.get(
            uri_template.format(partition_node.ip, '13800', key_name),
            json={'causal-context': causal_context}
        )
        causal_context = response.json().get('casual-context', {})


if __name__ == '__main__':
    unittest.main()
