from unittest import TestCase

from neo4j.exceptions import ClientError

from test.dataset_initialization import DataSet1
from test.graphdb_connector import GraphDBConnector
from transformer.s_transformer import STransformer


class TestRemove(TestCase):
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

    # 删除边的属性
    def test_remove_relationship(self):
        s_cypher = """
        MATCH (:Person {name: "Pauline Boutler"})-[e:LIVE_IN]->(:City {name: "London"})
        REMOVE e.code
        RETURN e.code
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"e.code": None}]

    def test_remove_rel_obj(self):
        s_cypher = """
        MATCH (n1:Person {name: "Pauline Boutler"})-[e:LIVE_IN]->(n2:City {name: "London"})
        REMOVE e.code, n2.spot
        RETURN n2.name, e.code, n2.spot
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"n2.name": "London"}, {"e.code": None}, {"n2.spot": None}]

        s_cypher = """
        MATCH (n1:Person {name: "Pauline Boutler"})-[e:LIVE_IN]->(n2:City {name: "London"})
        WHERE n1@T.from >= date("2004") and n1.name STARTS WITH "Pauline"
        REMOVE e.code, n2.spot
        RETURN n1.name, e.code, n2.spot
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"n1.name": "Pauline Boutler"}, {"e.code": None}, {"n2.spot": None}]

    # 标签的删除
    def test_remove_labels(self):
        s_cypher = """
        MATCH (n {name: 'London'})
        REMOVE n:City:Object
        RETURN n.name as name, labels(n) as labels
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"name": "London"}, {"labels": []}]

    # 带有效时间
    def test_remove_time(self):
        s_cypher = """
        MATCH (n1:Person@T("1978", NOW) {name@T("1978", NOW): "Pauline Boutler"(@T("1978", "1988"))})-[e:LIVE_IN@T("2004", "NOW")]->(n2:City {name: "London"})
        WHERE n1@T.from <= date("1980") and n1.name ENDS WITH "Boutler"
        REMOVE e.code, n2.name
        RETURN e.code, n2.name
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"e.code": None}, {"n2.name": None}]
