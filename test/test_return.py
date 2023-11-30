from unittest import TestCase

from test.graphdb_connector import GraphDBConnector
from transformer.s_transformer import STransformer


class TestReturn(TestCase):
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

    # 返回属性
    def test_return_1(self):
        s_cypher = """
        MATCH (n1:Person)-[e:FRIEND]->(n2:Person)
        RETURN n1.name, e.name
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    # 返回有效时间
    def test_return_2(self):
        s_cypher = """
        MATCH (n:Person{name: 'Pauline Boutler'})
        WITH n.name AS name
        RETURN name@T;
        """
        cypher_query = STransformer.transform(s_cypher)
        with self.assertRaises(Exception):  # 捕获类型随便写的，最好改成对应异常类
            tx = self.graphdb_connector.driver.session().begin_transaction()
            tx.run(cypher_query)

    # 返回时间类型数据
    def test_return_3(self):
        s_cypher = """
        RETURN datetime({epochSeconds: timestamp() / 1000, nanosecond: 23}) AS theDate;
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    def test_return_4(self):
        # TODO: make sure that the object a have several properties
        s_cypher = """
        MATCH (a:Person)
        RETURN DISTINCT a.country;
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    def test_return_5(self):
        # TODO: is the interval sortable?
        s_cypher = """
        MATCH (p:Person)
        RETURN p@T as n
        ORDER BY n DESC
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    def test_return_6(self):
        # TODO: test collect
        s_cypher = """
        MATCH (a:Person)-[:FRIENDS_WITH]->(b)
        RETURN a.name, collect(b.name) AS Friends;
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    def test_return_7(self):
        # TODO: test aggregate functions
        s_cypher = """
        MATCH (p:Person)
        RETURN avg(p.age) AS AverageAge, max(p.age) AS Oldest, min(p.age) AS Youngest;
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    def test_return_8(self):
        # TODO: test aggregate functions for interval
        s_cypher = """
        MATCH (p:Person)
        RETURN avg(p@T.from) AS AverageBirth, min(p@T.from) AS Oldest;
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    def test_return_9(self):
        # TODO: test aggregate functions for 'Now' with other timestamp
        s_cypher = """
        MATCH (p:Person)
        RETURN max(p@T.to) AS Oldest;
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    def test_return_10(self):
        # TODO: test calculation for interval
        s_cypher = """
        MATCH (p:Person)-[:FRIENDS_WITH]->(b:Person)
        WHERE p.name STARTS WITH "Mary"
        RETURN p,b, p@T.from-b@T.from AS AgeDiff;
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()
