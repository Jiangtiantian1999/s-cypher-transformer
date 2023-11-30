from unittest import TestCase

from test.graphdb_connector import GraphDBConnector
from transformer.s_transformer import STransformer


class TestMatch(TestCase):
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

    # 匹配节点
    def test_match_1(self):
        # 匹配对象节点
        s_cypher = """
        MATCH (n:Person@T("1938", NOW))
        RETURN n.name@T(NOW) as person_name
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()
        assert results == [{"person_name": "Mary Smith Taylor"}]

        # 匹配属性节点
        s_cypher = """
        MATCH (n:Person {name@T("1950"): "Mary Smith"})
        RETURN n.name@T(NOW) as person_name
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()
        assert results == [{"person_name": "Mary Smith Taylor"}]

        s_cypher = """
        MATCH (n:Person {name@T("1960", NOW): "Mary Smith"})
        RETURN n.name@T(NOW) as person_name
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()
        assert len(results) == 0

        # 匹配值节点
        s_cypher = """
        MATCH (n:Person {name: "Mary Smith"@T("1950")})
        RETURN n.name@T(NOW) as person_name
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()
        assert results == [{"person_name": "Mary Smith Taylor"}]

        s_cypher = """
        MATCH (n:Person {name: "Mary Smith"@T("1960", NOW)})
        RETURN n.name@T(NOW) as person_name
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()
        assert len(results) == 0

    # 匹配边
    def test_match_2(self):
        s_cypher = """
        MATCH (n1:Person)-[:LIVED@T("2000")]->(n2:City {name: "Brussels"})
        RETURN n1.name as person_name
        ORDER BY person_name
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()
        assert results == [{"person_name": "Cathy Van"}, {"person_name": "Pauline Boutler"}]

        s_cypher = """
        MATCH (n1:Person)-[:LIVED@T("2000","2003")]->(n2:City {name: "Brussels"})
        RETURN n1.name as person_name
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()
        assert results == [{"person_name": "Pauline Boutler"}]

    # 匹配路径
    def test_match_3(self):
        s_cypher = """
        MATCH path = (a:Person{name:"Mary Smith Taylor"})-[*2..5]->(b:Person)
        RETURN path
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    # 匹配连续有效路径
    def test_match_4(self):
        s_cypher = """
        MATCH path = cPath((n1:Person)-[:FRIEND*2]->(n2:Person))
        RETURN path
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

        s_cypher = """
                MATCH path = cPath((n1:Person)-[:LIVE*2]->(n2:City))
                RETURN path;
                """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

        s_cypher = """
        MATCH path = cPath((n1:Person)-[:LIKE*2]->(n2:Brand))
        RETURN path;
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    # 匹配成对连续有效路径
    def test_match_5(self):
        s_cypher = """
        MATCH path = pairCPath((n1:Person)-[:FRIEND*1..2]->(n2:Person))
        RETURN path;
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

        s_cypher = """
        MATCH path = pairCPath((n1:Person)-[:FRIEND*2..3]->(n2:Person))
        RETURN path
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

        s_cypher = """
        MATCH path = pairCPath((n1:Person)-[:LIVE*1..2]->(n2:City))
        RETURN path
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

        s_cypher = """
        MATCH path = pairCPath((n1:Person)-[:LIVE*2..3]->(n2:City))
        RETURN path
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

        s_cypher = """
        MATCH path = pairCPath((n1:Person)-[:LIKE*1..2]->(n2:Brand))
        RETURN path
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

        s_cypher = """
        MATCH path = pairCPath((n1:Person)-[:LIKE*2..3]->(n2:Brand))
        RETURN path;
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    # 匹配最早顺序有效路径
    def test_match_6(self):
        s_cypher = """
        MATCH path = earliestSPath((n1:Station {name: "HangZhou East"})-[:route*]->(n2:Station {name: "XvZhou North"}))
        RETURN path
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

        s_cypher = """
        MATCH path = earliestSPath((n1:Station {name: "HangZhou East"})-[:route*]->(n2:Station {name: "Ning Bo"}))
        RETURN path
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    # 匹配最迟顺序有效路径
    def test_match_7(self):
        s_cypher = """
        MATCH path = latestSPath((n1:Station {name: "HangZhou East"})-[:route*]->(n2:Station {name: "XvZhou North"}))
        RETURN path
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

        s_cypher = """
        MATCH path = latestSPath((n1:Station {name: "HangZhou East"})-[:route*]->(n2:Station {name: "Ning Bo"}))
        RETURN path
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    # 查询最快顺序有效路径
    def test_match_8(self):
        s_cypher = """
        MATCH path = fastestSPath((n1:Station {name: "HangZhou East"})-[:route*]->(n2:Station {name: "XiAn North"}))
        RETURN path
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

        s_cypher = """
        MATCH path = fastestSPath((n1:Station {name: "HangZhou East"})-[:route*2..3]->(n2:Station {name: "Ning Bo"}))
        RETURN path
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    # 查询最短顺序有效路径
    def test_match_9(self):
        s_cypher = """
        MATCH path = shortestSPath((n1:Station {name: "HangZhou East"})-[:route*]->(n2:Station {name: "XiAn North"}))
        RETURN path
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

        s_cypher = """
        MATCH path = shortestSPath((n1:Station {name: "HangZhou East"})-[:route*]->(n2:Station {name: "Ning Bo"}))
        RETURN path
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

        s_cypher = """
        MATCH path = shortestSPath((n1:Station {name: "HangZhou East"})-[:route*2]->(n2:Station {name: "Ning Bo"}))
        RETURN path
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()
