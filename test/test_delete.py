from datetime import timezone
from unittest import TestCase

from neo4j.exceptions import ClientError
from neo4j.time import DateTime

from test.dataset_initialization import DataSet1
from test.graphdb_connector import GraphDBConnector
from transformer.s_transformer import STransformer


class TestDelete(TestCase):
    graphdb_connector = None
    dataset1 = None

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.graphdb_connector = GraphDBConnector()
        cls.graphdb_connector.out_net_connect()
        cls.dataset1 = DataSet1(cls.graphdb_connector.driver)

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        cls.graphdb_connector.close()

    # 对象节点的物理删除
    def test_delete_object_node(self):
        s_cypher = """
        MATCH (n {name: "Pauline Boutler"})
        DELETE n
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        # TODO assert
        self.dataset1.rebuild()

    # 属性节点的物理删除
    def test_delete_property_node(self):
        s_cypher = """
        MATCH (n {name: "Pauline Boutler"})
        DELETE n.name
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        # TODO assert
        self.dataset1.rebuild()

    # 值节点的物理删除
    def test_delete_value_node(self):
        s_cypher = """
        MATCH (n {name: "Pauline Boutler"})
        DELETE n.name#Value
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        # TODO assert
        self.dataset1.rebuild()

    # 边的物理删除
    def test_delete_relationship(self):
        s_cypher = """
        MATCH (a:Person {name: "Pauline Boutler"})-[e:LIVE_IN]->(b:City {name: "London"})
        DELETE e
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        # TODO assert
        self.dataset1.rebuild()
