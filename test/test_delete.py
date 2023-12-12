from datetime import timezone
from unittest import TestCase

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

    def test_delete_object_node(self):
        # 对象节点的物理删除
        s_cypher = """
                CREATE (n: Person{name: "test delete"})
                """
        cypher_query = STransformer.transform(s_cypher)
        print(cypher_query)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        s_cypher = """
                MATCH (n: Person{name: "test delete"})
                DELETE n
                RETURN n
                """
        cypher_query = STransformer.transform(s_cypher)
        print(cypher_query)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert len(records) != 0

        # 对象节点的逻辑删除，包含节点和其所有关系
        s_cypher = """
                MATCH (n {name: "Pauline Boutler"})
                DETACH DELETE n
                RETURN n
                """
        cypher_query = STransformer.transform(s_cypher)
        print(cypher_query)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert len(records) != 0

        # 多个对象节点的物理删除
        s_cypher = """
                MATCH (n1:Person), (n2:City)
                WHERE n1.name = "Pauline Boutler" AND n2.name = "London"
                DETACH DELETE n1, n2
                RETURN n1, n2
                """
        cypher_query = STransformer.transform(s_cypher)
        print(cypher_query)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert len(records) != 0

    def test_delete_property_node(self):
        # 属性节点的物理删除
        s_cypher = """
        MATCH (n {name: "Pauline Boutler"})
        DELETE n.name
        RETURN n
        """
        cypher_query = STransformer.transform(s_cypher)
        print(cypher_query)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert len(records) != 0

    # 值节点的物理删除
    def test_delete_value_node(self):
        s_cypher = """
        MATCH (n {name: "Pauline Boutler"})
        DELETE n.name#Value
        RETURN n
        """
        cypher_query = STransformer.transform(s_cypher)
        print(cypher_query)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert len(records) != 0

    # 边的物理删除
    def test_delete_relationship(self):
        s_cypher = """
        MATCH (a:Person {name: "Pauline Boutler"})-[e:LIVE_IN]->(b:City {name: "London"})
        DELETE e
        RETURN e
        """
        cypher_query = STransformer.transform(s_cypher)
        print(cypher_query)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert len(records) != 0

    def test_delete_time(self):
        # 节点属性删除
        s_cypher = """
               MATCH (n:Person {name@T("1960", NOW): "Mary Smith"})
               DELETE n.name
               BETWEEN interval(n.name@T.from, date("2000"))
               RETURN n.name@T.from as effective_time
               """
        cypher_query = STransformer.transform(s_cypher)
        print(cypher_query)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"effective_time": DateTime(2001, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc)}]

        # 多个对象节点的物理删除，带有效时间
        s_cypher = """
                MATCH (n1:Person), (n2:City)
                WHERE n1.name = "Pauline Boutler" AND n2.name = "London"
                DETACH DELETE n1, n2
                AT TIME date("2000")
                RETURN n1, n2
                """
        cypher_query = STransformer.transform(s_cypher)
        print(cypher_query)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert len(records) == 0

        s_cypher = """
                MATCH (n1:Person), (n2:City)
                WHERE n1.name = "Pauline Boutler" AND n2.name = "London"
                DETACH DELETE n1, n2
                BETWEEN interval(datetime("2000"), datetime("2004"))
                RETURN n1, n2
                """
        cypher_query = STransformer.transform(s_cypher)
        print(cypher_query)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert len(records) == 0

        # 关系删除
        s_cypher = """
                MATCH (n1:Person)-[e:LIVE@T("2000", "2004")]->(n2:City {name: "Brussels"})
                DELETE e
                BETWEEN interval(datetime("2000"), datetime("2002"))
                RETURN e@T.from as effective_time
                """
        cypher_query = STransformer.transform(s_cypher)
        print(cypher_query)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"effective_time": DateTime(2003, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc)}]

        # 路径删除
        s_cypher = """
                MATCH path = (a:Person{name:"Mary Smith Taylor"})-[e:FRIEND*1..2]->(b:Person)
                DELETE path
                RETURN path
                """
        cypher_query = STransformer.transform(s_cypher)
        print(cypher_query)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert len(records) != 0



