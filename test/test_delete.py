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
        super().tearDownClass()
        cls.graphdb_connector.close()

    # DELETE子句用于物理删除对象节点、属性节点、值节点和边
    def test_delete_object_node(self):
        # 对象节点的删除,仅删除单个节点
        s_cypher = """
        CREATE (n: Person{name: "test delete"})
        DELETE n
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert len(records) == 0

        # 对象节点的删除,同时删除其所有关系
        s_cypher = """
        MATCH (n {name: "Pauline Boutler"})
        DETACH DELETE n
        RETURN n
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert len(records[0]) == 1

        # 多个对象节点的删除,同时删除其所有关系
        s_cypher = """
        MATCH (n1:Person), (n2:City)
        WHERE n1.name = "Pauline Boutler" AND n2.name = "London"
        DETACH DELETE n1, n2
        RETURN n1, n2
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert len(records[0]) == 2

    # 属性节点的删除
    def test_delete_property_node(self):
        # 属性节点的删除,仅删除属性
        s_cypher = """
        MATCH (n {name: "Pauline Boutler"})
        DELETE n.name
        RETURN n.name as name
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"name": None}]

        # 属性节点的删除,同时删除其所有关系
        s_cypher = """
        MATCH (n {name: "Pauline Boutler"})
        DETACH DELETE n.name
        RETURN n.name as name
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert len(records[0]) == 1

    # 值节点的删除
    def test_delete_value_node(self):
        s_cypher = """
        MATCH (n {name: "Pauline Boutler"})
        DELETE n.name#Value
        RETURN n.name as name
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"name": None}]

    # 边的删除
    def test_delete_relationship(self):
        # 仅删除边
        s_cypher = """
        MATCH (a:Person {name: "Pauline Boutler"})-[e:LIVE_IN]->(b:City {name: "London"})
        DELETE e
        RETURN e
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert len(records) == 0

    # 带有效时间的删除
    def test_delete_time(self):
        # 节点属性删除
        s_cypher = """
        MATCH (n:Person {name@T("1960", NOW): "Mary Smith"})
        DELETE n.name
        BETWEEN interval(n.name@T.from, date("2000"))
        RETURN n.name@T.from as effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"effective_time": DateTime(2001, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc)}]

        # 多个对象节点的删除,同时删除其所有关系
        s_cypher = """
        MATCH (n1:Person), (n2:City)
        WHERE n1.name = "Pauline Boutler" AND n2.name = "London"
        DETACH DELETE n1, n2
        AT TIME date("2000")
        RETURN n1, n2
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert len(records[0]) == 2

        s_cypher = """
        MATCH (n1:Person), (n2:City)
        WHERE n1.name = "Pauline Boutler" AND n2.name = "London"
        DETACH DELETE n1, n2
        BETWEEN interval(datetime("2000"), datetime("2004"))
        RETURN n1, n2
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert len(records[0]) == 2

        # 关系删除
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

        # 路径删除
        s_cypher = """
        MATCH path = (a:Person{name:"Mary Smith Taylor"})-[e:FRIEND*1..2]->(b:Person)
        DETACH DELETE path
        RETURN path
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert len(records) == 5
