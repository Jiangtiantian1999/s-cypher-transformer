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

    # 独立CALL查询
    def test_call_1(self):
        # 无参不指定返回值查询
        s_cypher = """
        CALL db.info
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"id": "E620AA48E32C3591A6711DA1F2530AFBD68AE541D41ABB20244BF0A7469D039F", "name": "neo4j",
                            "creationDate": "2023-11-02T13:45:01.51Z"}]

        # 无参指定返回值查询
        s_cypher = """
        CALL db.info()
        YIELD name
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"name": "neo4j"}]

        # 带参不指定返回值查询
        s_cypher = """
        CALL apoc.when(true, 'RETURN $a + 7 as b', 'RETURN $a as b', {a:3})
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"value": {"b": 10}}]

        # 带参指定返回值查询
        s_cypher = """
        CALL apoc.when(true, 'RETURN $a + 7 as b', 'RETURN $a as b',{a:3})
        YIELD value
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"value": {"b": 10}}]

    # 内部CALL查询
    def test_call_2(self):
        s_cypher = """
        MATCH (n:Person {name:"Pauline Boutler"})-[:LIVE@T(NOW)]->(m:City)
        CALL apoc.when(m.name = "London", 'RETURN true as living_in_london', 'RETURN false as living_in_london')
        YIELD value
        RETURN value
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"value": {"living_in_london": True}}]
