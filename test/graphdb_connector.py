from neo4j import GraphDatabase
from sshtunnel import SSHTunnelForwarder
import paramiko
from transformer.conf.config_reader import ConfigReader


class GraphDBConnector:
    def out_net_connect_pwd(self):
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

    def out_net_connect_pkey(self):
        self.server = SSHTunnelForwarder((ConfigReader.config["graph_database"]["out_net_ip"],
                                          ConfigReader.config["graph_database"]["out_net_port"]),
                                         ssh_username=ConfigReader.config["graph_database"]["host_user"],
                                         ssh_pkey=paramiko.RSAKey.from_private_key_file(
                                             ConfigReader.config["graph_database"]["host_private_key"]),
                                         remote_bind_address=(ConfigReader.config["graph_database"]["database_ip"],
                                                              ConfigReader.config["graph_database"]["database_port"])
                                         )
        self.server.start()
        self.driver = GraphDatabase.driver("bolt://127.0.0.1:" + str(self.server.local_bind_port),
                                           auth=(ConfigReader.config["graph_database"]["database_user"],
                                                 ConfigReader.config["graph_database"]["database_password"]))

    def local_connect(self):
        self.server = None
        self.driver = GraphDatabase.driver("bolt://" + str(ConfigReader.config["graph_database"]["database_ip"]) + ":"
                                           + str(ConfigReader.config["graph_database"]["database_port"]),
                                           auth=(ConfigReader.config["graph_database"]["database_user"],
                                                 ConfigReader.config["graph_database"]["database_password"]))

    def close(self):
        if self.driver:
            self.driver.close()
        if self.server:
            self.server.close()
