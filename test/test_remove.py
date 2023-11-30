from unittest import TestCase

from test.graphdb_connector import GraphDBConnector
from transformer.s_transformer import STransformer


class TestRemove(TestCase):
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

    def test_remove_1(self):
        s_cypher = """
        MATCH (:Person {name: "Pauline Boutler"})-[e:LIVE_IN]->(:City {name: "London"})
        REMOVE e.code
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    def test_remove_2(self):
        s_cypher = """
        MATCH (n1:Person {name: "Pauline Boutler"})-[e:LIVE_IN]->(n2:City {name: "London"})
        REMOVE e.code, n2.spot
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    def test_remove_3(self):
        s_cypher = """
        MATCH (n1:City)
        WHERE n1.spot is NULL
        REMOVE n1
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    def test_remove_4(self):
        s_cypher = """
        MATCH (n1:Person {name: "Pauline Boutler"})-[e:LIVE_IN]->(n2:City {name: "London"})
        WHERE n1@T.from >= date("2004") and n1.name STARTS WITH "Pauline"
        REMOVE e.code, n2.spot
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    def test_remove_5(self):
        s_cypher = """
        MATCH (p:Person)
        WHERE n1@T.from < date("1988")
        WITH p
        REMOVE p.name;
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()
