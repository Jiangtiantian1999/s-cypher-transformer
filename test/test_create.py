from datetime import timezone
from unittest import TestCase
import pytz

from neo4j.exceptions import ClientError
from neo4j.time import DateTime

from test.dataset_initialization import DataSet1
from test.graphdb_connector import GraphDBConnector
from transformer.s_transformer import STransformer


class TestCreate(TestCase):
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

    def test_create_node(self):
        # 对象节点创建
        s_cypher = """
                CREATE (n:Person@T("1938", NOW))
                RETURN n@T.from as effective_time
                """
        cypher_query = STransformer.transform(s_cypher)
        print(cypher_query, '\n')
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"effective_time": DateTime(1938, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc)}]

        s_cypher = """
                CREATE (n:City)
                AT TIME date("1688")
                RETURN n@T.from as effective_time
                """
        cypher_query = STransformer.transform(s_cypher)
        print(cypher_query, '\n')
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        print(records)
        self.dataset1.rebuild()
        assert records == [{"effective_time": DateTime(1688, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc)}]

        # 属性节点创建: 单属性创建
        s_cypher = """
                CREATE (n:Person{name@T("1960", NOW): "London"})
                RETURN n.name as name
                """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"name": "London"}]
        self.dataset1.rebuild()

        # 属性节点创建: 多属性创建
        s_cypher = """
                CREATE (n:City {name@T("1690", NOW): "London"@T("1690", NOW), spot: "BigBen"})
                AT TIME date("1688")
                RETURN n.name as name, n.spot as spot
                """
        cypher_query = STransformer.transform(s_cypher)
        print(cypher_query, '\n')
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"name": "London"}, {"spot": "BigBen"}]

        # 值节点创建: 不同时间区间
        s_cypher = """
                CREATE (n:Person {name@T("1950"): "Mary Smith"})
                RETURN n.name@T.from as effective_time
                """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"effective_time": DateTime(1950, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc)}]

        s_cypher = """
                CREATE (n:Person {name@T("1960", NOW): "Mary Smith"})
                RETURN n.name@T.from as effective_time
                """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"effective_time": DateTime(1960, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc)}]

        s_cypher = """
                CREATE (n:Person {name: "Mary Smith" @T("1950")})
                RETURN n.name#Value@T.from as effective_time
                """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"effective_time": DateTime(1950, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc)}]

        s_cypher = """
                CREATE (n:Person {name: "Mary Smith" @T("1960", NOW)})
                RETURN n.name as name
                """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"name": "Mary Smith"}]

        s_cypher = """
                CREATE (n:City@T("1688", NOW) {name@T("1690", NOW): "London"})
                RETURN n@T.from as object_time, n.name@T.from as property_time
                """
        cypher_query = STransformer.transform(s_cypher)
        print(cypher_query)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        self.dataset1.rebuild()
        assert records == [{"object_time": DateTime(1688, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc)},
                           {"property_time": DateTime(1690, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc)}]

        s_cypher = """
                CREATE (n:City@T("1688", NOW) {name@T("1690", NOW): "London"@T("1690", NOW)})
                RETURN n@T.from as object_time, n.name@T.from as property_time, n.name#Value@T.from as value_time
                """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"object_time": DateTime(1688, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc)},
                           {"property_time": DateTime(1690, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc)},
                           {"value_time": DateTime(1690, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc)}]

        # 对象节点时间使用AT_TIME
        s_cypher = """
                CREATE (n:City {name@T("1690", NOW): "London"@T("1690", NOW)})
                AT_TIME date("1688");
                RETURN n@T.from as effective_time
                """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"effective_time": DateTime(1688, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc)}]

        s_cypher = """
                CREATE (n:City {name@T("1688", NOW): "London"@T("1690", NOW)})
                AT TIME date("1688")
                RETURN n.name@T.from as effective_time
                """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"effective_time": DateTime(1688, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc)}]

    # 创建不同时间格式的节点
    def test_create_time(self):
        s_cypher = """
                CREATE (n:City{name: "London"})
                AT TIME datetime("1600-07-21T21:40:32.142+0100")
                RETURN n@T.from as effective_time
                """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"effective_time": DateTime(1600, 7, 21, 21, 40, 32, 142000000, tzinfo=pytz.FixedOffset(60))}]

    def test_create_relationship(self):
        s_cypher = """
                MATCH (n1:Person), (n2:City)
                WHERE n1.name = "Pauline Boutler" AND n2.name = "London"
                CREATE (n1)-[e:LIVE_IN@T("2004", NOW)]->(n2)
                AT TIME date("2023")
                RETURN e@T.from as effective_time
                        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"effective_time": DateTime(2004, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc)}]

        # s_cypher = """
        #         MATCH (n1:Person), (n2:City)
        #         WHERE n1.name = "Pauline Boutler" AND n2.name = "London"
        #         CREATE (n1)-[e:LIVE_IN@T(datetime("20150721T21:40-01:30"), NOW)]->(n2)
        #         AT TIME date("2023")
        #         """
        # cypher_query = STransformer.transform(s_cypher)
        # records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        # self.dataset1.rebuild()
        # # TODO assert
        # assert len(records) == 0
        #
        # s_cypher = """
        #         MATCH (n1:Person), (n2:City)
        #         WHERE n1.name = "Pauline Boutler" AND n2.name = "London"
        #         CREATE (n1)-[e:LIVE_IN@T(datetime("20150721T21:40-01:30"), NOW)]->(n2)
        #         AT TIME datetime("20110721T21:40-01:30")
        #         """
        # cypher_query = STransformer.transform(s_cypher)
        # records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        # self.dataset1.rebuild()
        # # TODO assert
        # assert len(records) == 0

        # s_cypher = """
        # MATCH (n1:Person), (n2:City)
        # WHERE n1.name = "Pauline Boutler" AND n2.name = "London"
        # CREATE (n1)-[e:LIVE_IN@T(datetime("20150721T21:40-01:30"), datetime("20130721T21:40-01:30"))]->(n2)
        # AT TIME datetime("20110721T21:40-01:30")
        # RETURN e@T as effective_time
        # """
        # cypher_query = STransformer.transform(s_cypher)
        # records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        # self.dataset1.rebuild()
        # # TODO assert
        # assert len(records) == 0

    # 非法有效时间
    def test_create_illegal_interval(self):
        # 值节点时间不在属性节点时间内
        s_cypher = """
                CREATE (n:City@T("1688", NOW) {name@T("1690", NOW): "London"@T("1650", NOW)})
                AT TIME date("1688")
                RETURN n
                """
        cypher_query = STransformer.transform(s_cypher)
        print(cypher_query, '\n')
        self.dataset1.rebuild()
        with self.assertRaises(ClientError):
            self.graphdb_connector.driver.execute_query(cypher_query)

        # 属性节点时间不在对象节点时间内
        s_cypher = """
                CREATE (n:City@T("1688", NOW) {name@T("1650", NOW): "London"@T("1690", NOW)})
                AT TIME date("1688")
                RETURN n
                """
        cypher_query = STransformer.transform(s_cypher)
        print(cypher_query, '\n')
        self.dataset1.rebuild()
        with self.assertRaises(ClientError):
            self.graphdb_connector.driver.execute_query(cypher_query)

        # 值节点不在对象节点有效时间区间内
        s_cypher = """
                CREATE (n:City {name@T("1690", NOW): "London"@T("1611", "1632")})
                AT TIME date("1688")
                """
        cypher_query = STransformer.transform(s_cypher)
        print(cypher_query, '\n')
        self.dataset1.rebuild()
        with self.assertRaises(ClientError):
            self.graphdb_connector.driver.execute_query(cypher_query)

        # 值节点、属性节点、对象节点的时间均不满足有效时间区间内
        s_cypher = """
                CREATE (n:City@T("1688", NOW) {name@T("1650", NOW): "London"@T("1640", NOW)})
                AT TIME date("1688")
                RETURN n
                """
        cypher_query = STransformer.transform(s_cypher)
        print(cypher_query, '\n')
        self.dataset1.rebuild()
        with self.assertRaises(ClientError):
            self.graphdb_connector.driver.execute_query(cypher_query)

        # 时间区间的intervalFrom晚于intervalTo
        s_cypher = """
                CREATE (n:City {name@T("1690", NOW): "London"@T("1699", "1690")})
                AT TIME date("1688")
                RETURN n
                """
        cypher_query = STransformer.transform(s_cypher)
        print(cypher_query, '\n')
        self.dataset1.rebuild()
        with self.assertRaises(ClientError):
            self.graphdb_connector.driver.execute_query(cypher_query)

        # 时间格式非法
        s_cypher = """
                CREATE (n:City {name@T("16ss", NOW): "London"@T("1690", NOW)})
                AT TIME date("1688")
                """
        cypher_query = STransformer.transform(s_cypher)
        print(cypher_query, '\n')
        self.dataset1.rebuild()
        with self.assertRaises(ClientError):
            self.graphdb_connector.driver.execute_query(cypher_query)

    def test_create_nodes_with_operator(self):
        # 多节点创建
        s_cypher = """
                CREATE
                  (a:City {name: 'Washington', country: 'America'}),
                  (b:City {name: 'New York', country: 'America'}),
                  (c:City {name: 'Beijing', country: 'China'})
                WITH [a, b, c] AS ps
                UNWIND ps AS p
                RETURN DISTINCT p.country as country
                """
        cypher_query = STransformer.transform(s_cypher)
        print(cypher_query)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"country": "America"}, {"country": "China"}]

