from unittest import TestCase

from test.graphdb_connector import GraphDBConnector
from transformer.s_transformer import STransformer


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

    # 节点创建
    def test_create_1(self):
        # 对象节点创建
        s_cypher = """
                CREATE (n:Person@T("1938", NOW))
                RETURN n@T.from as t
                """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()
        assert results == [{"t": "1938"}]

        # 属性节点创建
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

        # 值节点创建
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

        # 全部带时序信息
        s_cypher = """
                CREATE (n:City@T("1688", NOW) {name@T("1690", NOW): "London"@T("1690", NOW)})
                RETURN n
                """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()
        assert len(results) == 0

    # 边创建
    def test_create_2(self):
        pass

    def test_create_3(self):
        s_cypher = """
        CREATE (n:City@T("1688", NOW) {name@T("1690", NOW): "London"})
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    def test_create_4(self):
        s_cypher = """
        MATCH (n1:Person), (n2:City)
        WHERE n1.name = "Pauline Boutler" AND n2.name = "London"
        CREATE (n1)-[e:LIVE_IN@T("2004", NOW)]->(n2)
        AT TIME date("2023")
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    def test_create_5(self):
        s_cypher = """
        CREATE (n:City {name: "London"})
        AT TIME date("1688")
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    def test_create_6(self):
        s_cypher = """
        CREATE (n:City {name: "London"})
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    def test_create_7(self):
        s_cypher = """
        CREATE (n:City@T("1688", NOW) {name@T("1643", NOW): "London"@T("1690", NOW)})
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    def test_create_8(self):
        s_cypher = """
        CREATE (n:City {name@T("16ss", NOW): "London"@T("1690", NOW)})
        AT TIME date("1688")
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    def test_create_9(self):
        s_cypher = """
        CREATE (n:City {name@T("1690", NOW): "London"@T("1611", "1632")})
        AT TIME date("1688")
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    def test_create_10(self):
        s_cypher = """
        CREATE (n:City {name@T("1690", NOW): "London"@T("1699", "1690")})
        AT TIME date("1688")
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    def test_create_11(self):
        s_cypher = """
        CREATE (n:City {name@T(datetime("2015-07-21T21:40:32.142+0100"), NOW): "London"@T(datetime("1690-07-21T21:40:32.142+0100", NOW)})
        AT TIME datetime("1600-07-21T21:40:32.142+0100")
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    def test_create_12(self):
        s_cypher = """
        MATCH (n1:Person), (n2:City)
        WHERE n1.name = "Pauline Boutler" AND n2.name = "London"
        CREATE (n1)-[e:LIVE_IN@T(datetime("20150721T21:40-01:30"), NOW)]->(n2)
        AT TIME date("2023")
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    def test_create_13(self):
        s_cypher = """
        MATCH (n1:Person), (n2:City)
        WHERE n1.name = "Pauline Boutler" AND n2.name = "London"
        CREATE (n1)-[e:LIVE_IN@T(datetime("20150721T21:40-01:30"), NOW)]->(n2)
        AT TIME datetime("20110721T21:40-01:30")
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    def test_create_14(self):
        s_cypher = """
        MATCH (n1:Person), (n2:City)
        WHERE n1.name = "Pauline Boutler" AND n2.name = "London"
        CREATE (n1)-[e:LIVE_IN@T(datetime("20150721T21:40-01:30"), datetime("20130721T21:40-01:30"))]->(n2)
        AT TIME datetime("20110721T21:40-01:30")
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    def test_create_15(self):
        s_cypher = """
        CREATE (n:City {name@T("1690", NOW): "London"@T("1690", NOW), spot: "BigBen"})
        AT TIME date("1688")
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    def test_create_16(self):
        s_cypher = """
        CREATE (n:Station {name@T("2013", NOW): "HangZhou East"@T("2013", NOW)})
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    def test_create_17(self):
        s_cypher = """
        CREATE (n:City {name@T("1589", NOW): "HangZhou East"@T("2013", NOW), spot: "West Lake"}
        At TIME date("1589")
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    def test_create_18(self):
        s_cypher = """
        CREATE (n:Station {name@T("2014", NOW): "Ning Bo"@T("2014", NOW)}
        At TIME date("2014")
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()
