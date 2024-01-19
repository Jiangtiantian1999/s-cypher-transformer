import os
import sys

from test.dataset.person_dataset import PersonDataSet

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from unittest import TestCase

from graphdb_connector import GraphDBConnector
from transformer.s_transformer import STransformer


class TestRemove(TestCase):
    graphdb_connector = None
    person_dataset = None

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.graphdb_connector = GraphDBConnector()
        cls.graphdb_connector.default_connect()
        cls.person_dataset = PersonDataSet(cls.graphdb_connector.driver)

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        cls.graphdb_connector.close()

    # 删除边的属性
    def test_remove_property(self):
        s_cypher = """
        MATCH (:Person {name: "Pauline Boutler"})-[e:LIVE]->(:City {name: "London"})
        SET e.code = "255389"
        RETURN e.code as code
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"code": "255389"}]
        s_cypher = """
        MATCH (:Person {name: "Pauline Boutler"})-[e:LIVE]->(:City {name: "London"})
        REMOVE e.code
        RETURN e.code as code
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.person_dataset.rebuild()
        assert records == [{"code": None}]

        # 不能使用REMOVE删除实体的属性
        s_cypher = """
        MATCH (n:Person {name: "Pauline Boutler"})
        REMOVE n.name
        RETURN n.name as name
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.person_dataset.rebuild()
        assert records == [{"name": "Pauline Boutler"}]

        # 不能REMOVE属性intervalFrom和intervalTo
        s_cypher = """
        MATCH (:Person {name: "Pauline Boutler"})-[e:LIVE]->(:City {name: "London"})
        REMOVE e.intervalFrom
        """
        with self.assertRaises(SyntaxError):
            STransformer.transform(s_cypher)

        s_cypher = """
        MATCH (n:Person {name: "Pauline Boutler"})
        REMOVE n.intervalTo
        """
        with self.assertRaises(SyntaxError):
            STransformer.transform(s_cypher)

    # 移除实体标签
    def test_remove_labels(self):
        s_cypher = """
        MATCH (n:City {name: 'London'})
        REMOVE n:City
        RETURN labels(n) as labels
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.person_dataset.rebuild()
        assert records == [{"labels": ["Object"]}]

        # 不能移除标签Object、Property和Value
        s_cypher = """
        MATCH (n:City {name: 'London'})
        REMOVE n:Object
        RETURN labels(n) as labels
        """
        with self.assertRaises(SyntaxError):
            STransformer.transform(s_cypher)
