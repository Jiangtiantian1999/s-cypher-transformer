from datetime import timezone
from unittest import TestCase

from neo4j.exceptions import ClientError
from neo4j.time import DateTime

from test.dataset_initialization import DataSet1
from test.graphdb_connector import GraphDBConnector
from transformer.s_transformer import STransformer


class TestTimeWindow(TestCase):
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
    def test_snapshot(self):
        # 全局声明时间,限制当前操作时间点
        s_cypher = """
                SNAPSHOT datetime('2023')
                """
        cypher_query = STransformer.transform(s_cypher)
        print(cypher_query)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert len(records) == 0

        s_cypher = """
                MATCH (n:Person)
                WHERE n.name STARTS WITH "Mary"
                RETURN n.name as person_name
                """
        cypher_query = STransformer.transform(s_cypher)
        print(cypher_query)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"person_name": "Mary Smith Taylor"}]

        self.dataset1.rebuild()

    # 测试SCOPE
    def test_scope(self):
        # 全局声明时间，限制后续所有查询的时间区间
        s_cypher = """
                SCOPE interval("1960", "1990")
                """
        cypher_query = STransformer.transform(s_cypher)
        print(cypher_query)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert len(records) == 0

        s_cypher = """
                MATCH (n1:Person)-[:LIVE@T("1995",NOW)]->(n2:City {name: "Antwerp"})
                RETURN n1.name as person_name
                """
        cypher_query = STransformer.transform(s_cypher)
        print(cypher_query)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert len(records) == 0

        self.dataset1.rebuild()

    # 测试同时声明的优先级
    def test_priority(self):
        # TODO
        pass
