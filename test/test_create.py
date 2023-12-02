from unittest import TestCase

from test.graphdb_connector import GraphDBConnector
from transformer.s_transformer import STransformer


# TODO：更改assert
class TestCreate(TestCase):
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

    # 对象节点创建
    def test_create_object_node(self):
        s_cypher = """
                CREATE (n:Person@T("1938", NOW))
                RETURN n@T.from as t
                """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()
        assert results == [{"t": "1938"}]

        s_cypher = """
                CREATE (n:City)
                AT TIME date("1688")
                RETURN n
                """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        assert len(results) == 0

    # 属性节点创建
    def test_create_property_node(self):
        # ---------------------------------------------------------------------------
        # 单属性创建
        s_cypher = """
                CREATE (n:Person {name@T("1950")})
                RETURN n
                """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()
        assert len(results) == 0

        s_cypher = """
                CREATE (n:Person {name@T("1960", NOW)})
                RETURN n
                """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()
        assert len(results) == 0
        # ---------------------------------------------------------------------------
        # 多属性创建
        s_cypher = """
                CREATE (n:City {name@T("1690", NOW): "London"@T("1690", NOW), spot: "BigBen"})
                AT TIME date("1688")
                """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    # 值节点创建
    def test_create_value_node(self):
        s_cypher = """
                CREATE (n:Person {name@T("1950"): "Mary Smith"})
                RETURN n
                """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()
        assert len(results) == 0

        s_cypher = """
                CREATE (n:Person {name@T("1960", NOW): "Mary Smith"})
                RETURN n
                """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()
        assert len(results) == 0

        s_cypher = """
                CREATE (n:Person {name: "Mary Smith" @T("1950")})
                RETURN n
                """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()
        assert len(results) == 0

        s_cypher = """
                CREATE (n:Person {name: "Mary Smith" @T("1960", NOW)})
                RETURN n
                """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()
        assert len(results) == 0

        s_cypher = """
                CREATE (n:City@T("1688", NOW) {name@T("1690", NOW): "London"})
                RETURN n
                """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        assert len(results) == 0

        s_cypher = """
                CREATE (n:City@T("1688", NOW) {name@T("1690", NOW): "London"@T("1690", NOW)})
                RETURN n
                """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()
        assert len(results) == 0

        s_cypher = """
                CREATE (n:Station {name@T("2013", NOW): "HangZhou East"@T("2013", NOW)})
                """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()
        # ---------------------------------------------------------------------------
        # 对象节点时间使用AT_TIME
        s_cypher = """
                CREATE (n:City {name@T("1690", NOW): "London"@T("1690", NOW)})
                AT_TIME date("1688");
                RETURN n
                """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()
        assert len(results) == 0

        s_cypher = """
                CREATE (n:City {name@T("1688", NOW): "London"@T("1690", NOW)})
                AT TIME date("1688")
                """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

        s_cypher = """
                CREATE (n:Station {name@T("2014", NOW): "Ning Bo"@T("2014", NOW)}
                At TIME date("2014")
                """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

        s_cypher = """
                CREATE (n:City {name@T("1589", NOW): "HangZhou East"@T("2013", NOW), spot: "West Lake"}
                At TIME date("1589")
                """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    # TODO:匹配节点创建
    def test_create_match_node(self):

        s_cypher = """
                MATCH(n: Person {name: "Mary Smith"})
                CREATE(m: Person {name: n.name @ T("1950", NOW）(@ T("1960", NOW}))
                RETURN m
               """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()
        assert len(results) == 0

        s_cypher = """
                MATCH (n1:Person), (n2:City)
                WHERE n1.name = "Pauline Boutler" AND n2.name = "London"
                CREATE (n1)-[e:LIVE_IN@T("2004", NOW)]->(n2)
                AT TIME date("2023")
                """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    # TODO:创建不同时间格式的节点
    def test_create_time(self):
        s_cypher = """
                CREATE (n:City {name@T(datetime("2015-07-21T21:40:32.142+0100"), NOW): "London"@T(datetime("1690-07-21T21:40:32.142+0100", NOW)})
                AT TIME datetime("1600-07-21T21:40:32.142+0100")
                """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    # TODO:边创建
    def test_create_relationship(self):
        # 用户创建边e，
        # 首先通过MATCH指定e的出点src和入点dst，
        # 再指定边e的内容（content），
        # 可以选择指定e的有效时间、e的属性和当前操作时间t（默认为now()）。
        # 边e的内容不得为“OBJECT_PROPERTY”或“PROPERTY_VALUE”
        pass

    def test_create_match_relationship(self):
        s_cypher = """
                MATCH (n1:Person), (n2:City)
                WHERE n1.name = "Pauline Boutler" AND n2.name = "London"
                CREATE (n1)-[e:LIVE_IN@T(datetime("20150721T21:40-01:30"), NOW)]->(n2)
                AT TIME date("2023")
                """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

        s_cypher = """
                MATCH (n1:Person), (n2:City)
                WHERE n1.name = "Pauline Boutler" AND n2.name = "London"
                CREATE (n1)-[e:LIVE_IN@T(datetime("20150721T21:40-01:30"), NOW)]->(n2)
                AT TIME datetime("20110721T21:40-01:30")
                """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

        s_cypher = """
        MATCH (n1:Person), (n2:City)
        WHERE n1.name = "Pauline Boutler" AND n2.name = "London"
        CREATE (n1)-[e:LIVE_IN@T(datetime("20150721T21:40-01:30"), datetime("20130721T21:40-01:30"))]->(n2)
        AT TIME datetime("20110721T21:40-01:30")
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

# 非法有效时间，应报错
    def test_create_illegal_interval(self):
        # ---------------------------------------------------------------------------
        # 值节点时间不在属性节点时间内
        s_cypher = """
                CREATE (n:City@T("1688", NOW) {name@T("1690", NOW): "London"@T("1650", NOW)})
                AT_TIME date("1688");
                RETURN n
                """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()
        assert len(results) == 0
        # ---------------------------------------------------------------------------
        # 属性节点时间不在对象节点时间内
        s_cypher = """
                CREATE (n:City@T("1688", NOW) {name@T("1650", NOW): "London"@T("1690", NOW)})
                AT_TIME date("1688");
                RETURN n
                """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()
        assert len(results) == 0
        # ---------------------------------------------------------------------------
        # 值节点不在对象节点有效时间区间内
        s_cypher = """
                CREATE (n:City {name@T("1690", NOW): "London"@T("1611", "1632")})
                AT TIME date("1688")
                """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()
        # ---------------------------------------------------------------------------
        # 值节点、属性节点、对象节点的时间均不满足有效时间区间内
        s_cypher = """
                CREATE (n:City@T("1688", NOW) {name@T("1650", NOW): "London"@T("1640", NOW)})
                AT_TIME date("1688");
                RETURN n
                """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()
        assert len(results) == 0
        # ---------------------------------------------------------------------------
        # 时间区间的intervalFrom晚于intervalTo
        s_cypher = """
                CREATE (n:City {name@T("1690", NOW): "London"@T("1699", "1690")})
                AT TIME date("1688")
                RETURN n
                """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()
        # ---------------------------------------------------------------------------
        # 时间格式非法
        s_cypher = """
                CREATE (n:City {name@T("16ss", NOW): "London"@T("1690", NOW)})
                AT TIME date("1688")
                """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()
