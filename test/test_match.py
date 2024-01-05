import os
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from unittest import TestCase

from graphdb_connector import GraphDBConnector
from transformer.s_transformer import STransformer


class TestMatch(TestCase):
    graphdb_connector = None

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.graphdb_connector = GraphDBConnector()
        cls.graphdb_connector.local_connect()

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        cls.graphdb_connector.close()

    # 匹配对象节点
    def test_match_object_node(self):
        s_cypher = """
        MATCH (n:Person@T("1938", "1960"))
        RETURN n.name#T(NOW) as person_name
        ORDER BY person_name
        LIMIT 3
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"person_name": "Cathy Van"}, {"person_name": "Mary Smith Taylor"},
                           {"person_name": "Peter Burton"}]

    # 匹配属性节点
    def test_match_property_node(self):
        s_cypher = """
        MATCH (n:Person {name@T("1950"): "Mary Smith"})
        RETURN n.name#T(NOW) as person_name
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"person_name": "Mary Smith Taylor"}]

        s_cypher = """
        MATCH (n:Person {name@T("1960", NOW): "Mary Smith"})
        RETURN n.name#T(NOW) as person_name
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"person_name": "Mary Smith Taylor"}]

    # 匹配值节点
    def test_match_value_node(self):
        s_cypher = """
        MATCH (n:Person {name:"Mary Smith"@T("1950")})
        RETURN n.name#T(NOW) as person_name
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"person_name": "Mary Smith Taylor"}]

        s_cypher = """
        MATCH (n:Person {name: "Mary Smith"@T("1960", NOW) })
        RETURN n.name#T(NOW) as person_name
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert len(records) == 0

    # 匹配关系
    def test_match_relationship(self):
        s_cypher = """
        MATCH (n1:Person)-[:LIVE@T("2000")]->(n2:City {name: "Brussels"})
        RETURN n1.name as person_name
        ORDER BY person_name
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"person_name": "Cathy Van"}, {"person_name": "Pauline Boutler"}]

        s_cypher = """
        MATCH (n1:Person)-[:LIVE@T("2001","2003")]->(n2:City {name: "Brussels"})
        RETURN n1.name as person_name
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"person_name": "Pauline Boutler"}]

    # 匹配路径
    def test_match_path(self):
        s_cypher = """
        MATCH path = (a:Person{name:"Mary Smith Taylor"})-[e:FRIEND*1..2]->(b:Person)
        RETURN [node in nodes(path) | node.name#T(NOW)] as path
        ORDER BY path
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"path": ["Mary Smith Taylor", "Pauline Boutler"]},
                           {"path": ["Mary Smith Taylor", "Pauline Boutler", "Cathy Van"]},
                           {"path": ["Mary Smith Taylor", "Peter Burton"]},
                           {"path": ["Mary Smith Taylor", "Peter Burton", "Cathy Van"]},
                           {"path": ["Mary Smith Taylor", "Peter Burton", "Daniel Yang"]}]

        s_cypher = """
        MATCH path = (a:Person{name:"Mary Smith Taylor"})-[e:FRIEND*1..2@T("2000")]->(b:Person)
        RETURN [node in nodes(path) | node.name#T("2000")] as path
        ORDER BY path
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"path": ["Mary Smith Taylor", "Peter Burton"]},
                           {"path": ["Mary Smith Taylor", "Peter Burton", "Cathy Van"]}]

    # 匹配连续有效路径
    def test_match_cpath(self):
        s_cypher = """
        MATCH path = cPath((n1:Person)-[:FRIEND*2]->(n2:Person))
        RETURN [node in nodes(path) | node.name#T(NOW)] as path
        ORDER BY path
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"path": ["Mary Smith Taylor", "Pauline Boutler", "Cathy Van"]},
                           {"path": ["Mary Smith Taylor", "Peter Burton", "Cathy Van"]},
                           {"path": ["Mary Smith Taylor", "Peter Burton", "Daniel Yang"]}]

        s_cypher = """
        MATCH path = cPath((n1:Station)-[*2..3]->(n2:Station))
        RETURN [relationship in relationships(path) | type(relationship)] as path
        ORDER BY path
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"path": ["G7349", "G116"]}]

    # 匹配成对连续有效路径
    def test_match_pair_cpath(self):
        s_cypher = """
        MATCH path = pairCPath((n1:Person)-[:FRIEND*2]->(n2:Person))
        RETURN [node in nodes(path) | node.name#T(NOW)] as path
        ORDER BY path
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"path": ["Mary Smith Taylor", "Pauline Boutler", "Cathy Van"]},
                           {"path": ["Mary Smith Taylor", "Peter Burton", "Cathy Van"]},
                           {"path": ["Mary Smith Taylor", "Peter Burton", "Daniel Yang"]}]

        s_cypher = """
        MATCH path = pairCPath((n1:Station)-[*2..3]->(n2:Station))
        RETURN [relationship in relationships(path) | type(relationship)] as path
        ORDER BY path
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"path": ["G7349", "G116"]}]

    # 匹配最早顺序有效路径
    def test_match_earliest_spath(self):
        s_cypher = """
        MATCH path = earliestSPath((n1:Station {name: "Hangzhoudong Railway Station"})-[*]->(n2:Station {name: "Xuzhoudong Railway Station"}))
        RETURN [relationship in relationships(path) | type(relationship)] as path
        ORDER BY path
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"path": ["G7372", "G116"]}]

        s_cypher = """
        MATCH path = earliestSPath((n1:Station {name: "Hangzhoudong Railway Station"})-[*]->(n2:Station {name: "Lianyungang Railway Station"}))
        RETURN [relationship in relationships(path) | type(relationship)] as path
        ORDER BY path
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"path": ["G7349", "G1204", "G178", "G289"]}, {"path": ["G7372", "G116", "G289"]},
                           {"path": ["G7372", "G1204", "G178", "G289"]}]

    # 匹配最迟顺序有效路径
    def test_match_latest_spath(self):
        s_cypher = """
        MATCH path = latestSPath((n1:Station {name: "Hangzhoudong Railway Station"})-[*]->(n2:Station {name: "Xuzhoudong Railway Station"}))
        RETURN [relationship in relationships(path) | type(relationship)] as path
        ORDER BY path
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"path": ["G7349", "G1204", "G178"]}]

        s_cypher = """
        MATCH path = latestSPath((n1:Station {name: "Hangzhoudong Railway Station"})-[*]->(n2:Station {name: "Lianyungang Railway Station"}))
        RETURN [relationship in relationships(path) | type(relationship)] as path
        ORDER BY path
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"path": ["G7349", "G1204", "G178", "G289"]}, {"path": ["G7349", "G7540"]}]

    # 查询最快顺序有效路径
    def test_match_fastest_spath(self):
        s_cypher = """
        MATCH path = fastestSPath((n1:Station {name: "Hangzhoudong Railway Station"})-[*]->(n2:Station {name: "Xuzhoudong Railway Station"}))
        RETURN [relationship in relationships(path) | type(relationship)] as path
        ORDER BY path
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"path": ["G7349", "G1204", "G178"]}]

        s_cypher = """
        MATCH path = fastestSPath((n1:Station {name: "Hangzhoudong Railway Station"})-[*]->(n2:Station {name: "Lianyungang Railway Station"}))
        RETURN [relationship in relationships(path) | type(relationship)] as path
        ORDER BY path
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"path": ["G7349", "G1204", "G178", "G289"]}]

    # 查询最短顺序有效路径
    def test_match_shortest_spath(self):
        s_cypher = """
        MATCH path = shortestSPath((n1:Station {name: "Hangzhoudong Railway Station"})-[*]->(n2:Station {name: "Xuzhoudong Railway Station"}))
        RETURN [relationship in relationships(path) | type(relationship)] as path
        ORDER BY path
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"path": ["G7372", "G116"]}]

        s_cypher = """
        MATCH path = shortestSPath((n1:Station {name: "Hangzhoudong Railway Station"})-[*3..]->(n2:Station {name: "Xuzhoudong Railway Station"}))
        RETURN [relationship in relationships(path) | type(relationship)] as path
        ORDER BY path
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"path": ["G7349", "G1204", "G178"]}, {"path": ["G7372", "G1204", "G178"]}]

        s_cypher = """
        MATCH path = shortestSPath((n1:Station {name: "Hangzhoudong Railway Station"})-[*]->(n2:Station {name: "Lianyungang Railway Station"}))
        RETURN [relationship in relationships(path) | type(relationship)] as path
        ORDER BY path
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"path": ["G7349", "G7540"]}, {"path": ["G7372", "G7540"]}]
