from unittest import TestCase
from datetime import timezone
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
        cls.dataset1.rebuild()
        super().tearDownClass()
        cls.graphdb_connector.close()

    # 物理删除实体，同时删除对象节点、属性节点和值节点
    def test_delete_object_node(self):
        # 物理删除单个实体
        s_cypher = """
        CREATE (n: Person{name: "Nick"})
        RETURN n
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert len(records) == 1
        s_cypher = """
        MATCH (n: Person{name: "Nick"})
        DELETE n
        """
        cypher_query = STransformer.transform(s_cypher)
        self.graphdb_connector.driver.execute_query(cypher_query)
        s_cypher = """
        MATCH (n: Person{name: "Nick"})
        RETURN n
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert len(records) == 0

        # DETACH DELETE物理删除单个实体及其所有关系
        s_cypher = """
        MATCH (n {name: "Pauline Boutler"})
        DETACH DELETE n
        """
        cypher_query = STransformer.transform(s_cypher)
        self.graphdb_connector.driver.execute_query(cypher_query)
        s_cypher = """
        MATCH (n:Person)-[e:LIVE]->(m:City)
        RETURN count(e) as count
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"count": 7}]

        # 物理删除多个实体及其所有关系
        s_cypher = """
        MATCH (n1:Person{name: "Pauline Boutler"}), (n2:City{name: "Brussels"})
        DETACH DELETE n1, n2
        """
        cypher_query = STransformer.transform(s_cypher)
        self.graphdb_connector.driver.execute_query(cypher_query)
        s_cypher = """
        MATCH (n:Person)-[e:LIVE]->(m:City)
        RETURN count(e) as count
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"count": 5}]

    # 物理删除属性节点（及其值节点）
    def test_delete_property_node(self):
        # 物理删除属性节点，并删除属性节点下的所有值节点
        s_cypher = """
        MATCH (n {name: "Pauline Boutler"})
        DELETE n.name
        RETURN n.name as name
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"name": None}]

        # 物理删除属性节点时，DETACH无影响
        s_cypher = """
        MATCH (n {name: "Pauline Boutler"})
        DETACH DELETE n.name
        RETURN n.name as name
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"name": None}]

    # 物理删除值节点
    def test_delete_value_node(self):
        # 物理删除某个属性节点下的所有值节点
        s_cypher = """
        MATCH (n {name: "Pauline Boutler"})
        DELETE n.name#Value
        RETURN n.name as name
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"name": None}]

        # 物理删除某个属性节点下的指定时间区间下的所有值节点

        # 物理删除某个属性节点下的指定时间点下的值节点

    # 物理删除关系
    def test_delete_relationship(self):
        # 物理删除关系
        s_cypher = """
        MATCH (a:Person {name: "Pauline Boutler"})-[e:LIVE_IN]->(b:City {name: "London"})
        DELETE e
        RETURN e
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert len(records) == 0

        # 物理删除某时间区间下的关系
        s_cypher = """
        MATCH (n1:Person)-[e:LIVE@T("2000", "2004")]->(n2:City {name: "Brussels"})
        DELETE e
        BETWEEN interval(datetime("2000"), datetime("2002"))
        RETURN e@T.from as effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert len(records) == 0

        # 物理删除某时间点下的关系
