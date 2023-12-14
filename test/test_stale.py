from datetime import timezone
from unittest import TestCase

from neo4j.exceptions import ClientError
from neo4j.time import DateTime

from test.dataset_initialization import DataSet1
from test.graphdb_connector import GraphDBConnector
from transformer.s_transformer import STransformer


class TestStale(TestCase):
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

    # STALE子句用于逻辑删除对象节点、对象节点的属性和边

    # 对象节点的逻辑删除
    def test_stale_node(self):
        s_cypher = """
        MATCH (n {name: "Pauline Boutler"})
        STALE n
        AT TIME date("2023")
        RETURN n@T.to as effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"effective_time": DateTime(2022, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)}]

    # 边的逻辑删除
    def test_stale_relationship(self):
        s_cypher = """
        MATCH (:Person {name: "Pauline Boutler"})-[e:LIVE_IN]->(:City {name: "London"})
        STALE e
        RETURN e@T.to as effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        print(cypher_query, '\n')
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"effective_time": DateTime(2022, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)}]

    # 对象节点属性的逻辑删除
    def test_stale_property(self):
        s_cypher = """
        MATCH (n {name: "Pauline Boutler"})
        STALE n.name
        AT TIME date("2023")
        RETURN n.name@T.to as effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"effective_time": DateTime(2022, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)}]

    # 对象节点属性值的逻辑删除
    def test_stale_value(self):
        s_cypher = """
        MATCH (n {name: "Pauline Boutler"})
        STALE n.name#Value
        AT TIME date("2023")
        RETURN n.name#Value@T.to as effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"effective_time": DateTime(2022, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)}]

    # 时间区间@T.to is not NOW
    def test_stale_time(self):
        s_cypher = """
        MATCH (n:City@T("1690", "1999") {name@T("1900", "1999"): "London"(@T("1900", "1999"))})
        STALE n.name#Value
        AT TIME date("1999")
        RETURN n.name#Value@T.to as effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"effective_time": DateTime(1998, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)}]

        s_cypher = """
        MATCH (n:City@T("1690", "1999") {name@T("1900", "1999"): "London"(@T("1900", "1999"))})
        STALE n.name
        AT TIME date("1950")
        RETURN n.name@T.to as effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert len(records) != 0
