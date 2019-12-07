"""
CSE 138 - Fall 2019
Author(s): Aldrin Montana
Email(s) : akmontan@ucsc.edu

This is a module that wraps various external tools in a nicer API. Primarily for Docker and git at
the moment.
"""

import logging
import ipaddress
import docker

from docker.types import LogConfig


class NodeContainer(object):
    """
    This is an abstraction over Docker containers to coalesce container functionality and key-value
    store nodes into a single object. Note that when we first create a container, the IP address
    needs to be provided as an environment variable. We never need to update this IP address again,
    because it's always maintained in memory afterwards.
    """

    # a client that communicates with the docker daemon
    docker_client = docker.from_env()

    @classmethod
    def list_containers(cls, **kwargs):
        return cls.docker_client.containers.list(**kwargs)

    @classmethod
    def clean_containers_by_name(cls, container_names):
        existing_containers = NodeContainer.list_containers(
            filters={'name': container_names}
        )

        for existing_container in existing_containers:
            existing_container.stop()
            existing_container.remove()

    @classmethod
    def run(cls, image, name, ip, view, port='13800', repl_factor=2, command=None):
        container_obj = cls.docker_client.containers.run(
            image,
            name=name,
            detach=True,
            command=command,
            log_config=LogConfig(type=LogConfig.types.JSON),
            environment={
                'REPL_FACTOR': repl_factor,
                'VIEW'       : view,
                'ADDRESS'    : '{}:{}'.format(ip, port)
            }
        )

        return cls(ip, view, repl_factor, container_obj)

    def __init__(self, ip, view, repl_factor, docker_container):
        self.ip          = ip
        self.view        = view
        self.repl_factor = repl_factor
        self.container   = docker_container

    def stop(self):   self.container.stop()
    def remove(self): self.container.remove()

    def name(self): return self.container.name

    def set_ip(self, ip):
        """
        This method tracks the given IP address. This is acceptable because after the container is
        already run, we don't need to maintain consistency between this object's IP address and the
        IP address of the container's environment.
        """

        self.ip = ip


class NodeNetwork(object):
    """
    This is an abstraction over Docker networks that can add NodeContainers (connect to this
    network) or remove them (disconnect from this network) to represent network partitions.
    """

    # logger for the class
    logger = logging.getLogger('{}.{}'.format(__module__, 'NodeNetwork'))

    # a client that communicates with the docker daemon
    docker_client = docker.from_env()

    @classmethod
    def remove_subnets_by_name(cls, subnet_names):
        for docker_network in cls.docker_client.networks.list(names=subnet_names):
            cls.logger.info('clearing subnet: "{}"'.format(docker_network.attrs['Name']))

            # reload info to make sure we see the connected containers
            docker_network.reload()

            for connected_container in docker_network.containers:
                cls.logger.info('cleaning container: "{}"'.format(connected_container.name))

                connected_container.stop()
                connected_container.remove()

            cls.logger.info('removing subnet: "{}"'.format(docker_network.attrs['Name']))
            docker_network.remove()

    @classmethod
    def for_subnet(cls, name, subnet):
        ipam_config = docker.types.IPAMConfig(
            pool_configs=[docker.types.IPAMPool(subnet=subnet)]
        )

        return cls(
            cls.docker_client.networks.create(name, driver='bridge', ipam=ipam_config),
            subnet
        )

    def __init__(self, docker_network, subnet=None):
        self.network         = docker_network
        self.free_addrs      = {}
        self.assigned_addrs  = {}

        # an ip_network object for book keeping of IP assignment
        self.subnet          = ipaddress.ip_network(subnet)
        self.remaining_addrs = self.subnet.hosts()

        # and then we just pop off the first address taken by the host OS
        next(self.remaining_addrs)

    def containers(self):
        self.network.reload()

        return self.network.containers

    def connect(self, node_container, ip=None):
        """
        Connect a container to this network. The primary network that the node is added to will be
        provided an IP address. If this network represents a partition, then we don't particularly
        care about the IP address, except as a way to still send messages to the container.
        """

        # ip_addr should be set to ip
        ip_addr = ip

        # but if ip is not provided
        if not ip_addr:
            # then set ip_addr to the previously assigned addr or the next available addr
            ip_addr = (
                self.free_addrs.get(node_container.name())
                or str(next(self.remaining_addrs))
            )

        # connect container
        self.assigned_addrs[node_container.name()] = ip_addr
        self.network.connect(node_container.container, ipv4_address=ip_addr)

        node_container.set_ip(ip_addr)

    def disconnect(self, node_container):
        """
        Disconnect a container from this network. In order to make sure that the container gets the
        same IP address as it was first assigned (specifically, for correctness in the primary
        subnet), this moves the associated IP address for the container to a dictionary of freed
        addresses.
        """

        # move assigned addr for the container to free addresses
        self.free_addrs[node_container.name()] = self.assigned_addrs[node_container.name()]
        del self.assigned_addrs[node_container.name()]

        # disconnect container
        self.network.disconnect(node_container.container)

    def remove(self):
        for connected_container in self.containers():
            self.__class__.logger.info('cleaning container: "{}"'.format(connected_container.name))

            connected_container.stop()
            connected_container.remove()

        self.network.remove()
