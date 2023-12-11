from neo4j import GraphDatabase
from sshtunnel import SSHTunnelForwarder

from transformer.conf.config_reader import ConfigReader


class GraphDBConnector:
    def out_net_connect(self):
        self.server = SSHTunnelForwarder((ConfigReader.config["graph_database"]["out_net_ip"],
                                          ConfigReader.config["graph_database"]["out_net_port"]),
                                         ssh_username=ConfigReader.config["graph_database"]["host_user"],
                                         ssh_password=ConfigReader.config["graph_database"]["host_password"],
                                         remote_bind_address=(ConfigReader.config["graph_database"]["database_ip"],
                                                              ConfigReader.config["graph_database"]["database_port"]))
        self.server.start()
        self.driver = GraphDatabase.driver("bolt://127.0.0.1:" + str(self.server.local_bind_port),
                                           auth=(ConfigReader.config["graph_database"]["database_user"],
                                                 ConfigReader.config["graph_database"]["database_password"]))

    def close(self):
        if self.driver:
            self.driver.close()
        if self.server:
            self.server.close()
