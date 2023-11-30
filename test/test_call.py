from unittest import TestCase

from test.graphdb_connector import GraphDBConnector
from transformer.s_transformer import STransformer


class TestCall(TestCase):
    graphdb_connector = None

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.graphdb_connector = GraphDBConnector()
        cls.graphdb_connector.out_net_connect()

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        cls.graphdb_connector.close()

    def test_call_1(self):
        s_cypher = """
        CALL db.labels
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    def test_call_2(self):
        s_cypher = """
        CALL dbms.info()
        YIELD id, name, createDate
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    def test_call_3(self):
        s_cypher = """
        CALL org.opencypher.procedure.example.addNodeToIndex("users", 0, "name")
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    def test_call_4(self):
        s_cypher = """
        MATCH (n1:Person {name: "Nick"})-[:FRIEND*2]->(n2:Person)
        RETURN max(n1.ege, n2.ege) as max_edge
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()
