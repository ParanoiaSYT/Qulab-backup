"""
Package for interacting on the network at a high level.
"""
import asyncio
import errno
import logging
import pickle
import random
import sys

from qulab._config import config
from qulab.dht.crawling import NodeSpiderCrawl, ValueSpiderCrawl
from qulab.dht.node import Node
from qulab.dht.protocol import KademliaProtocol
from qulab.dht.utils import digest
from qulab.storage.memstorage import ForgetfulStorage

cfg = config.get('dht', dict())
DEFALT_PORT = cfg.get('default_port', 8987)

log = logging.getLogger(__name__)  # pylint: disable=invalid-name


# pylint: disable=too-many-instance-attributes
class Server:
    """
    High level view of a node instance.  This is the object that should be
    created to start listening as an active node on the network.
    """

    protocol_class = KademliaProtocol

    def __init__(self, ksize=20, alpha=3, node_id=None, storage=None):
        """
        Create a server instance.  This will start listening on the given port.
        Args:
            ksize (int): The k parameter from the paper
            alpha (int): The alpha parameter from the paper
            node_id: The id for this node on the network.
            storage: An instance that implements
                     :interface:`~kademlia.storage.IStorage`
        """
        self.ksize = ksize
        self.alpha = alpha
        self.storage = storage or ForgetfulStorage()
        self.node = Node(node_id or digest(random.getrandbits(255)))
        self.transport = None
        self.protocol = None
        self.refresh_loop = None
        self.save_state_loop = None
        self.port = None

    async def start(self, bootstrap_nodes=None, port=None):
        if port is None:
            self.port = await self.listen_on_random_port()
        else:
            await self.listen(port)
            self.port = port
        if bootstrap_nodes is not None:
            await self.bootstrap(bootstrap_nodes)

    def stop(self):
        if self.transport is not None:
            self.transport.close()

        if self.refresh_loop:
            self.refresh_loop.cancel()

        if self.save_state_loop:
            self.save_state_loop.cancel()

    def _create_protocol(self):
        return self.protocol_class(self.node, self.storage, self.ksize)

    async def listen(self, port, interface='0.0.0.0'):
        """
        Start listening on the given port.
        Provide interface="::" to accept ipv6 address
        """
        loop = asyncio.get_event_loop()
        listen = loop.create_datagram_endpoint(self._create_protocol,
                                               local_addr=(interface, port),
                                               reuse_address=False,
                                               reuse_port=False,
                                               allow_broadcast=False)
        log.info("Node %i try to listen on %s:%i", self.node.long_id,
                 interface, port)
        self.transport, self.protocol = await listen
        log.info("Node %i listening on %s:%i succeed.", self.node.long_id,
                 interface, port)
        # finally, schedule refreshing table
        self.refresh_table()

    async def listen_on_random_port(self,
                                    interface='0.0.0.0',
                                    min_port=49152,
                                    max_port=65536,
                                    max_tries=100):
        """Bind socket to a random port in a range.
        If the port range is unspecified, the system will choose the port.

        Args:
            addr : str
                The address string without the port to pass to ``Socket.bind()``.
            min_port : int, optional
                The minimum port in the range of ports to try (inclusive).
            max_port : int, optional
                The maximum port in the range of ports to try (exclusive).
            max_tries : int, optional
                The maximum number of bind attempts to make.

        Returns:
            port : int
                The port the socket was bound to.
    
        Raises:
            OSError
                if `max_tries` reached before successful bind
        """
        ports = random.sample(range(min_port, max_port), max_tries)
        ports.insert(0, DEFALT_PORT)
        for port in ports:
            try:
                await self.listen(port, interface)
            except OSError as exception:
                en = exception.errno
                if en == errno.EADDRINUSE:
                    continue
                elif sys.platform == 'win32' and en == errno.EACCES:
                    continue
                else:
                    raise
            break
        else:
            raise OSError("Could not bind socket to random port. %d" % port)
        return port

    def refresh_table(self):
        log.debug("Refreshing routing table")
        asyncio.ensure_future(self._refresh_table())
        loop = asyncio.get_event_loop()
        self.refresh_loop = loop.call_later(3600, self.refresh_table)

    async def _refresh_table(self):
        """
        Refresh buckets that haven't had any lookups in the last hour
        (per section 2.3 of the paper).
        """
        results = []
        for node_id in self.protocol.get_refresh_ids():
            node = Node(node_id)
            nearest = self.protocol.router.find_neighbors(node, self.alpha)
            spider = NodeSpiderCrawl(self.protocol, node, nearest, self.ksize,
                                     self.alpha)
            results.append(spider.find())

        # do our crawling
        await asyncio.gather(*results)

        # now republish keys older than one hour
        for dkey, value in self.storage.iter_older_than(3600):
            await self.set_digest(dkey, value)

    def bootstrappable_neighbors(self):
        """
        Get a :class:`list` of (ip, port) :class:`tuple` pairs suitable for
        use as an argument to the bootstrap method.
        The server should have been bootstrapped
        already - this is just a utility for getting some neighbors and then
        storing them if this server is going down for a while.  When it comes
        back up, the list of nodes can be used to bootstrap.
        """
        neighbors = self.protocol.router.find_neighbors(self.node)
        return [tuple(n)[-2:] for n in neighbors]

    async def bootstrap(self, addrs):
        """
        Bootstrap the server by connecting to other known nodes in the network.
        Args:
            addrs: A `list` of (ip, port) `tuple` pairs.  Note that only IP
                   addresses are acceptable - hostnames will cause an error.
        """
        log.debug("Attempting to bootstrap node with %i initial contacts",
                  len(addrs))
        cos = list(map(self.bootstrap_node, addrs))
        gathered = await asyncio.gather(*cos)
        nodes = [node for node in gathered if node is not None]
        spider = NodeSpiderCrawl(self.protocol, self.node, nodes, self.ksize,
                                 self.alpha)
        return await spider.find()

    async def bootstrap_node(self, addr):
        result = await self.protocol.ping(addr, self.node.id)
        return Node(result[1], addr[0], addr[1]) if result[0] else None

    async def get(self, key):
        """
        Get a key if the network has it.
        Returns:
            :class:`None` if not found, the value otherwise.
        """
        log.info("Looking up key %s", key)
        dkey = digest(key)
        return await self.get_digest(dkey)

    async def get_digest(self, dkey):
        """
        Get a given SHA1 digest key (bytes) if the network has it.
        Returns:
            :class:`None` if not found, the value otherwise.
        """
        # if this node has it, return it
        if self.storage.get(dkey) is not None:
            return self.storage.get(dkey)
        node = Node(dkey)
        nearest = self.protocol.router.find_neighbors(node)
        if not nearest:
            log.warning("There are no known neighbors to get dkey %s",
                        dkey.hex())
            return None
        spider = ValueSpiderCrawl(self.protocol, node, nearest, self.ksize,
                                  self.alpha)
        return await spider.find()

    async def set(self, key, value):
        """
        Set the given string key to the given value in the network.
        """
        if not check_dht_value_type(value):
            raise TypeError(
                "Value must be of type int, float, bool, str, or bytes")
        log.info("setting '%s' = '%s' on network", key, value)
        dkey = digest(key)
        return await self.set_digest(dkey, value)

    async def set_digest(self, dkey, value):
        """
        Set the given SHA1 digest key (bytes) to the given value in the
        network.
        """
        self.storage[dkey] = value
        node = Node(dkey)

        nearest = self.protocol.router.find_neighbors(node)
        if not nearest:
            log.warning("There are no known neighbors to set dkey %s",
                        dkey.hex())
            return False

        spider = NodeSpiderCrawl(self.protocol, node, nearest, self.ksize,
                                 self.alpha)
        nodes = await spider.find()
        log.info("setting '%s' on %s", dkey.hex(), list(map(str, nodes)))

        # if this node is close too, then store here as well
        #biggest = max([n.distance_to(node) for n in nodes])
        #if self.node.distance_to(node) < biggest:
        #    self.storage[dkey] = value
        results = [self.protocol.call_store(n, dkey, value) for n in nodes]
        # return true only if at least one store call succeeded
        return any(await asyncio.gather(*results))

    def save_state(self, fname):
        """
        Save the state of this node (the alpha/ksize/id/immediate neighbors)
        to a cache file with the given fname.
        """
        log.info("Saving state to %s", fname)
        data = {
            'ksize': self.ksize,
            'alpha': self.alpha,
            'id': self.node.id,
            'neighbors': self.bootstrappable_neighbors()
        }
        if not data['neighbors']:
            log.warning("No known neighbors, so not writing to cache.")
            return
        with open(fname, 'wb') as file:
            pickle.dump(data, file)

    @classmethod
    def load_state(cls, fname):
        """
        Load the state of this node (the alpha/ksize/id/immediate neighbors)
        from a cache file with the given fname.
        """
        log.info("Loading state from %s", fname)
        with open(fname, 'rb') as file:
            data = pickle.load(file)
        svr = Server(data['ksize'], data['alpha'], data['id'])
        if data['neighbors']:
            asyncio.ensure_future(svr.start(data['neighbors']))
        return svr

    def save_state_regularly(self, fname, frequency=600):
        """
        Save the state of node with a given regularity to the given
        filename.
        Args:
            fname: File name to save retularly to
            frequency: Frequency in seconds that the state should be saved.
                        By default, 10 minutes.
        """
        self.save_state(fname)
        loop = asyncio.get_event_loop()
        self.save_state_loop = loop.call_later(frequency,
                                               self.save_state_regularly,
                                               fname, frequency)


def check_dht_value_type(value):
    """
    Checks to see if the type of the value is a valid type for
    placing in the dht.
    """
    typeset = [int, float, bool, str, bytes]
    return type(value) in typeset  # pylint: disable=unidiomatic-typecheck
