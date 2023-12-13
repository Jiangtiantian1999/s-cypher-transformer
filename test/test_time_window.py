from unittest import TestCase

from test.graphdb_connector import GraphDBConnector
from transformer.s_transformer import STransformer


class TestTimeWindow(TestCase):
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

    # 测试AT TIME
    def test_at_time(self):
        s_cypher = """
            MATCH (n:Person)
            AT TIME date("2015202T21+18:00")
            WHERE n.name STARTS WITH "Mary"
            RETURN n.name as person_name
            """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"person_name": "Mary Smith Taylor"}]

        s_cypher = """
            MATCH (n:Person)
            AT TIME date("1950")
            WHERE n.name STARTS WITH "Mary"
            RETURN n.name as person_name
            """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"person_name": "Mary Smith"}]

    # 测试BETWEEN
    def test_between(self):
        s_cypher = """
            MATCH (n:Person @T("1950", NOW))
            BETWEEN interval(timePoint("1978"), "1980")
            RETURN n.name as person_name
            """
        cypher_query = STransformer.transform(s_cypher)
        print(cypher_query)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"person_name": ["Mary Smith", "Mary Smith Taylor"]}]

        s_cypher = """
            MATCH (n:Person)
            BETWEEN interval("1940", NOW)
            RETURN n.name as person_name limit 10
            """
        cypher_query = STransformer.transform(s_cypher)
        print(cypher_query)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"person_name": ["Mary Smith", "Mary Smith Taylor"]}]

        s_cypher = """
               MATCH (n:Person {name: "Cathy Van"})
               BETWEEN interval(n.name#Value@T.from, n@T.to)
               RETURN n.name as person_name
               """
        cypher_query = STransformer.transform(s_cypher)
        print(cypher_query)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"person_name": "Cathy Van"}]

    # 测试SNAPSHOT
    def test_snapshot_1(self):
        s_cypher = """
            SNAPSHOT date('1999')
            MATCH (n:City)
            AT_TIME date("2000")
            WHERE n.spot STARTS WITH "West"
            RETURN n.name;
            """
        cypher_query = STransformer.transform(s_cypher)
        print(cypher_query)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"person_name": "Cathy Van"}]

        s_cypher = """
                SNAPSHOT date('2023')
                MATCH path = (a:Person)-[*1..5]->(b:Brand)
                WHERE a.name ENDS WITH 'Van'
                RETURN path;
                """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    # TODO: SCOPE
