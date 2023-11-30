from unittest import TestCase

from test.graphdb_connector import GraphDBConnector
from transformer.s_transformer import STransformer


class TestStale(TestCase):
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

    def test_stale_1(self):
        s_cypher = """
        MATCH (n {name: "Pauline Boutler"})
        STALE n
        AT TIME date("2023")
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    def test_stale_2(self):
        s_cypher = """
        MATCH (:Person {name: "Pauline Boutler"})-[e:LIVE_IN]->(:City {name: "London"})
        STALE e
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    def test_stale_3(self):
        s_cypher = """
        MATCH (n {name: "Pauline Boutler"})
        STALE n.name
        AT TIME date("2023")
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    def test_stale_4(self):
        s_cypher = """
        MATCH (n {name: "Pauline Boutler"})
        STALE n.name#Value
        AT TIME date("2023")
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    def test_stale_5(self):
        # test if @T.to is not NOW
        s_cypher = """
        MATCH (n:City@T("1690", "1999") {name@T("1900", "1999"): "London"@T("1900", "1999")})
        STALE n
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()
