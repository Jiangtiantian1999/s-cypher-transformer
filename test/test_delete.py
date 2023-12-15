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

        # 物理删除属性节点和值节点时，DETACH不起作用
        s_cypher = """
        MATCH (n {name: "Pauline Boutler"})
        DETACH DELETE n.name
        RETURN n@T.from as start_time, n.name as name
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"start_time": DateTime(1978, 1, 1, tzinfo=timezone.utc), "name": None}]

    # 物理删除值节点
    def test_delete_value_node(self):
        # 物理删除某个属性节点下的所有值节点
        s_cypher = """
        MATCH (n {name: "Mary Smith Taylor"})
        DELETE n.name#Value
        RETURN n.name as name                              
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"name": None}]

        # 物理删除某个属性节点下的指定时间区间下的所有值节点
        # 在DELETE子句中指定删除值节点的范围（此时间区间优先于AT TIME和BETWEEN指定的时间窗口）
        s_cypher = """
        MATCH (n {name: "Mary Smith Taylor"})
        DELETE n.name@T("1959", "1960")
        RETURN n.name as name
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"name": None}]

        # 使用BETWEEN指定删除值节点的范围
        s_cypher = """
        MATCH (n {name: "Mary Smith Taylor"})
        DELETE n.name#Value
        BETWEEN interval("1960", "2022")
        RETURN n.name as name
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"name": "Mary Smith"}]

        # 物理删除某个属性节点下的指定时间点下的值节点
        # 在DELETE子句中指定删除值节点的范围（此时间点优先于AT TIME和BETWEEN指定的时间窗口）
        s_cypher = """
        MATCH (n {name: "Mary Smith Taylor"})
        DELETE n.name@T("1959")
        RETURN n.name as name
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"name": "Mary Smith Taylor"}]

        # 使用AT TIME指定删除值节点的范围
        s_cypher = """
        MATCH (n {name: "Mary Smith Taylor"})
        DELETE n.name#Value
        AT TIME timePoint("1959")
        RETURN n.name as name
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"name": "Mary Smith Taylor"}]

    # 物理删除关系
    def test_delete_relationship(self):
        s_cypher = """
        MATCH (a:Person {name: "Pauline Boutler"})-[e:LIVE]->(b:City)
        DELETE e
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
