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

    # 逻辑删除实体，同时逻辑删除对象节点、属性节点、值节点和实体的相连关系
    def test_stale_object_node(self):
        s_cypher = """
        MATCH (n {name: "Pauline Boutler"})-[e:LIVE]->(:City {name: "London"})
        STALE n
        AT TIME timePoint("2023")
        RETURN n@T as object_effective_time, n.name@T as property_effective_time, n.name#Value@T as value_effective_time, e@T as relationship_effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{
            "object_effective_time": {"from": DateTime(1978, 1, 1, tzinfo=timezone.utc),
                                      "to": DateTime(2022, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)},
            "property_effective_time": {"from": DateTime(1978, 1, 1, tzinfo=timezone.utc),
                                        "to": DateTime(2022, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)},
            "value_effective_time": {"from": DateTime(1978, 1, 1, tzinfo=timezone.utc),
                                     "to": DateTime(2022, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)},
            "relationship_effective_time": {"from": DateTime(2004, 1, 1, tzinfo=timezone.utc),
                                            "to": DateTime(2022, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)}}]

        # 不能逻辑删除历史实体，STALE不生效但也不报错
        s_cypher = """
        CREATE (n:Person@T("1990", "2010"){name@T("1990", "2010"): "Nick"@T("1990", "2010")})
        STALE n
        RETURN n@T as object_effective_time, n.name@T as property_effective_time, n.name#Value@T as value_effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"object_effective_time": {"from": DateTime(1990, 1, 1, tzinfo=timezone.utc),
                                                      "to": DateTime(2010, 1, 1, tzinfo=timezone.utc)},
                            "property_effective_time": {"from": DateTime(1990, 1, 1, tzinfo=timezone.utc),
                                                        "to": DateTime(2010, 1, 1, tzinfo=timezone.utc)},
                            "value_effective_time": {"from": DateTime(1990, 1, 1, tzinfo=timezone.utc),
                                                     "to": DateTime(2010, 1, 1, tzinfo=timezone.utc)}}]

        # 逻辑删除时间必须晚于待逻辑删除实体的开始时间
        s_cypher = """
        MATCH (n {name: "Pauline Boutler"})
        STALE n
        AT TIME timePoint("1978")
        """
        cypher_query = STransformer.transform(s_cypher)
        with self.assertRaises(ClientError):
            self.graphdb_connector.driver.execute_query(cypher_query)
            self.dataset1.rebuild()

    # 逻辑删除属性节点（及其值节点）
    def test_stale_property(self):
        s_cypher = """
        MATCH (n {name: "Pauline Boutler"})
        STALE n.name
        AT TIME timePoint("2023")
        RETURN n@T.to as object_end_time, n.name@T.to as property_end_time, n.name#Value@T.to as value_end_time
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"object_end_time": DateTime(9999, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc),
                            "property_end_time": DateTime(2022, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc),
                            "value_end_time": DateTime(2022, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)}]

        # 不能逻辑删除历史实体下的属性节点，STALE不生效但也不报错
        s_cypher = """
        CREATE (n:Person@T("1990", "2010"){name@T("1990", "2010"): "Nick"@T("1990", "2010")})
        STALE n.name
        RETURN n@T.to as object_end_time, n.name@T.to as property_end_time, n.name#Value@T.to as value_end_time
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"object_end_time": DateTime(2010, 1, 1, tzinfo=timezone.utc),
                            "property_end_time": DateTime(2010, 1, 1, tzinfo=timezone.utc),
                            "value_end_time": DateTime(2010, 1, 1, tzinfo=timezone.utc)}]

        # 不能逻辑删除历史属性节点，STALE不生效但也不报错
        s_cypher = """
        CREATE (n:Person@T("1990", NOW){name@T("1990", "2010"): "Nick"@T("1990", "2010")})
        STALE n.name
        RETURN n@T.to as object_end_time, n.name@T.to as property_end_time, n.name#Value@T.to as value_end_time
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"object_end_time": DateTime(9999, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc),
                            "property_end_time": DateTime(2010, 1, 1, tzinfo=timezone.utc),
                            "value_end_time": DateTime(2010, 1, 1, tzinfo=timezone.utc)}]

        # 逻辑删除时间必须晚于待逻辑删除属性节点的开始时间
        s_cypher = """
        MATCH (n {name: "Pauline Boutler"})
        STALE n.name
        AT TIME timePoint("1978")
        """
        cypher_query = STransformer.transform(s_cypher)
        with self.assertRaises(ClientError):
            self.graphdb_connector.driver.execute_query(cypher_query)
            self.dataset1.rebuild()

    # 逻辑删除值节点
    def test_stale_value(self):
        s_cypher = """
        MATCH (n {name: "Pauline Boutler"})
        STALE n.name#Value
        AT TIME timePoint("2023")
        RETURN n@T.to as object_end_time, n.name@T.to as property_end_time, n.name#Value@T.to as value_end_time
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"object_end_time": DateTime(9999, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc),
                            "property_end_time": DateTime(9999, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc),
                            "value_end_time": DateTime(2022, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)}]

        # 不能逻辑删除历史实体或历史属性节点下的值节点，STALE不生效但也不报错
        s_cypher = """
        CREATE (n:Person@T("1990", "2010"){name@T("1990", "2010"): "Nick"@T("1990", "2010")})
        STALE n.name#Value
        RETURN n@T.to as node_end_time, n.name@T.to as property_end_time, n.name#Value@T.to as value_end_time
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"node_end_time": DateTime(2010, 1, 1, tzinfo=timezone.utc),
                            "property_end_time": DateTime(2010, 1, 1, tzinfo=timezone.utc),
                            "value_end_time": DateTime(2010, 1, 1, tzinfo=timezone.utc)}]

        # 不能逻辑删除历史值节点，STALE不生效但也不报错
        s_cypher = """
        CREATE (n:Person@T("1990", NOW){name@T("1990", "2010"): "Nick"@T("1990", "2010")})
        STALE n.name
        RETURN n@T.to as node_end_time, n.name@T.to as property_end_time, n.name#Value@T.to as value_end_time
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"node_end_time": DateTime(9999, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc),
                            "property_end_time": DateTime(2010, 1, 1, tzinfo=timezone.utc),
                            "value_end_time": DateTime(2010, 1, 1, tzinfo=timezone.utc)}]

        # 逻辑删除时间必须晚于待逻辑删除值节点的开始时间
        s_cypher = """
        MATCH (n {name: "Pauline Boutler"})
        STALE n.name#Value
        AT TIME timePoint("1978")
        """
        cypher_query = STransformer.transform(s_cypher)
        with self.assertRaises(ClientError):
            self.graphdb_connector.driver.execute_query(cypher_query)
            self.dataset1.rebuild()

    # 逻辑删除关系
    def test_stale_relationship(self):
        s_cypher = """
        MATCH (:Person {name: "Pauline Boutler"})-[e:LIVE]->(:City {name: "London"})
        STALE e
        AT TIME timePoint("2023")
        RETURN e@T as effective
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"effective": {"from": DateTime(2004, 1, 1, tzinfo=timezone.utc),
                                          "to": DateTime(2022, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)}}]

        # 不能逻辑删除历史关系，STALE不生效但也不报错
        s_cypher = """
        MATCH (:Person {name: "Peter Burton"})-[e:FRIEND]->(:Person {name: "Daniel Yang"})
        STALE e
        RETURN e@T as effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{
            "effective_time": {"from": DateTime(2015, 1, 1, tzinfo=timezone.utc),
                               "to": DateTime(2018, 1, 1, tzinfo=timezone.utc)}}]

        # 逻辑删除时间必须晚于待逻辑删除关系的开始时间
        s_cypher = """
        MATCH (:Person {name: "Pauline Boutler"})-[e:LIVE]->(:City {name: "London"})
        STALE e
        AT TIME timePoint("2004")
        RETURN e@T as effective
        """
        cypher_query = STransformer.transform(s_cypher)
        with self.assertRaises(ClientError):
            self.graphdb_connector.driver.execute_query(cypher_query)
            self.dataset1.rebuild()
