from unittest import TestCase

from test.graphdb_connector import GraphDBConnector
from transformer.s_transformer import STransformer


class TestDelete(TestCase):
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

    def test_delete_1(self):
        s_cypher = """
        MATCH (n {name: "Pauline Boutler"})
        DELETE n
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    def test_delete_2(self):
        s_cypher = """
        MATCH (n {name: "Pauline Boutler"})
        DELETE n.name
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    def test_delete_3(self):
        s_cypher = """
        MATCH (n {name: "Pauline Boutler"})
        DELETE n.name#Value
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    def test_delete_4(self):
        s_cypher = """
        MATCH (a:Person {name: "Pauline Boutler"})-[e:LIVE_IN]->(b:City {name: "London"})
        DELETE e
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()
