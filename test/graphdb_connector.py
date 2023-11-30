from neo4j import GraphDatabase
from sshtunnel import SSHTunnelForwarder

from transformer.conf.config_reader import ConfigReader


class GraphDBConnector:
    def out_net_connect(self):
        self.server = SSHTunnelForwarder((ConfigReader.config["GRAPH_DATABASE"]["OUT_NET_IP"],
                                          int(ConfigReader.config["GRAPH_DATABASE"]["OUT_NET_PORT"])),
                                         ssh_username=ConfigReader.config["GRAPH_DATABASE"]["HOST_USER"],
                                         ssh_password=ConfigReader.config["GRAPH_DATABASE"]["HOST_PASSWORD"],
                                         remote_bind_address=(ConfigReader.config["GRAPH_DATABASE"]["DATABASE_IP"],
                                                              int(ConfigReader.config["GRAPH_DATABASE"][
                                                                      "DATABASE_PORT"])))
        self.server.start()
        self.driver = GraphDatabase.driver("bolt://127.0.0.1:" + str(self.server.local_bind_port),
                                           auth=(ConfigReader.config["GRAPH_DATABASE"]["DATABASE_USER"],
                                                 ConfigReader.config["GRAPH_DATABASE"]["DATABASE_PASSWORD"]))

    def close(self):
        if self.driver:
            self.driver.close()
        if self.server:
            self.server.close()
