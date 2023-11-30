from unittest import TestCase

from test.graphdb_connector import GraphDBConnector
from transformer.s_transformer import STransformer


class TestWith(TestCase):
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

    def test_with_1(self):
        s_cypher = """
        MATCH (n:Person{name: "Pauline Boutler"})
        WITH n AS person
        RETURN person.name@T
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    def test_with_2(self):
        s_cypher = """
        MATCH (n:Person{name: "Pauline Boutler"})
        WITH n.name + "000" as name
        RETURN name
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    def test_with_3(self):
        s_cypher = """
        MATCH (n:Brand)
        WHERE n.name CONTAINS 'Samsung'
        WITH n AS brand
        RETURN brand.name@T;
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    def test_with_4(self):
        s_cypher = """
        MATCH (n:Person{name: 'Daniel Yang'})
        WITH n.name + 'Justin' as name
        RETURN name;
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

## WITH date({year: 1984, month: 10, day: 11}) AS dd

# 修改或转换结果：
# 进行计算或使用函数：
# 进行排序和限制：
# 进行过滤
# 多步骤查询中的连接
