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

    # 指定实体的有效时间创建节点
    def test_create_object_node(self):
        # 在图模式中指定对象节点的有效时间
        # 指定有效时间区间
        s_cypher = """
        CREATE (n:Person@T("1938", "1980"))
        RETURN n@T as effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"effective_time": {"from": DateTime(1938, 1, 1, tzinfo=timezone.utc),
                                               "to": DateTime(1980, 1, 1, tzinfo=timezone.utc)}}]

        # 指定开始时间（结束时间为NOW）
        s_cypher = """
        CREATE (n:Person@T("1938"))
        RETURN n@T as effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{
            "effective_time": {"from": DateTime(1938, 1, 1, tzinfo=timezone.utc),
                               "to": DateTime(9999, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)}}]

        # 使用AT TIME指定对象节点的开始时间（结束时间为NOW）
        s_cypher = """
        CREATE (n:City)
        AT TIME datetime("1688")
        RETURN n@T as effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{
            "effective_time": {"from": DateTime(1688, 1, 1, tzinfo=timezone.utc),
                               "to": DateTime(9999, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)}}]

        s_cypher = """
        CREATE (n:City{name: "London"})
        AT TIME datetime("1600-07-21T21:40:32.142+0100")
        RETURN n@T as effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{
            "effective_time": {"from": DateTime(1600, 7, 21, 21, 40, 32, 142000000, tzinfo=pytz.FixedOffset(60)),
                               "to": DateTime(9999, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)}}]

        # 有效时间的时间类型必须与图数据库预设的时间粒度一致
        s_cypher = """
        CREATE (n:City)
        AT TIME date("1688")
        RETURN n@T as effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        with self.assertRaises(ClientError):
            self.graphdb_connector.driver.execute_query(cypher_query)
            self.dataset1.rebuild()

    # 指定属性节点和值节点的有效时间创建节点
    def test_create_property_node(self):
        # 在图模式中指定属性节点和值节点的有效时间
        # 指定有效时间区间
        s_cypher = """
        CREATE (n:Person{name@T("1980", "2000"): "Nick"@T("1980", "2000")})
        AT TIME timePoint("1960")
        RETURN n.name as name, n.name@T as property_effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{
            "name": "Nick", "property_effective_time": {"from": DateTime(1980, 1, 1, tzinfo=timezone.utc),
                                                        "to": DateTime(2000, 1, 1, tzinfo=timezone.utc)}}]

        # 指定开始时间（结束时间为NOW）
        s_cypher = """
        CREATE (n:Person{name@T("1980"): "Nick"@T("1980")})
        AT TIME timePoint("1960")
        RETURN n.name as name, n.name@T as property_effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{
            "name": "Nick",
            "property_effective_time": {"from": DateTime(1980, 1, 1, tzinfo=timezone.utc),
                                        "to": DateTime(9999, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)}}]

        # 使用AT TIME指定属性节点和值节点的开始时间（结束时间为NOW）（指定多个属性）
        s_cypher = """
        CREATE (n:City {name@T("1690", NOW): "London"@T("1690", NOW), spot: "BigBen"})
        AT TIME timePoint("1688")
        RETURN n.name as name, n.spot as spot, n.name@T as name_effective_time, n.spot@T as spot_effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{
            "name": "London", "spot": "BigBen",
            "name_effective_time": {"from": DateTime(1690, 1, 1, tzinfo=timezone.utc),
                                    "to": DateTime(9999, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)},
            "spot_effective_time": {"from": DateTime(1688, 1, 1, tzinfo=timezone.utc),
                                    "to": DateTime(9999, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)}}]

        # 优先使用图模式指定的有效时间
        s_cypher = """
        CREATE (n:City {name@T("1690", NOW): "London"@T("1690", NOW)})
        AT TIME timePoint("1688")
        RETURN n.name@T as effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{
            "effective_time": {"from": DateTime(1690, 1, 1, tzinfo=timezone.utc),
                               "to": DateTime(9999, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)}}]

    # 指定值节点的有效时间创建节点
    def test_create_value_node(self):
        # 在图模式中指定值节点的有效时间
        # 指定有效时间区间
        s_cypher = """
        CREATE (n:Person {name: "Nick" @T("1960", "1980")})
        AT TIME timePoint("1950")
        RETURN n.name#Value@T as effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"effective_time": {"from": DateTime(1960, 1, 1, tzinfo=timezone.utc),
                                               "to": DateTime(1980, 1, 1, tzinfo=timezone.utc)}}]

        # 指定开始时间（结束时间为NOW）
        s_cypher = """
        CREATE (n:Person {name: "Nick" @T("1960")})
        AT TIME timePoint("1950")
        RETURN n.name#Value@T as effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{
            "effective_time": {"from": DateTime(1960, 1, 1, tzinfo=timezone.utc),
                               "to": DateTime(9999, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)}}]

        # 使用AT TIME指定值节点的开始时间（结束时间为NOW）
        s_cypher = """
        CREATE (n:Person {name: "Nick"})
        AT TIME timePoint("1950")
        RETURN n.name#Value@T as effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{
            "effective_time": {"from": DateTime(1950, 1, 1, tzinfo=timezone.utc),
                               "to": DateTime(9999, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)}}]

    # 组合指定对象节点、属性节点和值节点的有效时间创建节点
    def test_create_mix_node(self):
        s_cypher = """
        CREATE (n:City@T("1221", NOW) {name@T("1927", NOW): "Hangzhou"@T("1927", NOW)})
        RETURN n@T.from as object_start_time, n.name@T.from as property_start_time, n.name#Value@T.from as value_start_time
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"object_start_time": DateTime(1221, 1, 1, tzinfo=timezone.utc),
                            "property_start_time": DateTime(1927, 1, 1, tzinfo=timezone.utc),
                            "value_start_time": DateTime(1927, 1, 1, tzinfo=timezone.utc)}]

        s_cypher = """
        CREATE (n:City@T("1221", NOW) {name@T("1927"): "Hangzhou"})
        AT TIME timePoint("1928")
        RETURN n@T.from as object_start_time, n.name@T.from as property_start_time, n.name#Value@T.from as value_start_time
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"object_start_time": DateTime(1221, 1, 1, tzinfo=timezone.utc),
                            "property_start_time": DateTime(1927, 1, 1, tzinfo=timezone.utc),
                            "value_start_time": DateTime(1928, 1, 1, tzinfo=timezone.utc)}]

        s_cypher = """
        CREATE (n:City@T("1221", NOW) {name: "Hangzhou"})
        AT TIME timePoint("1927")
        RETURN n@T.from as object_start_time, n.name@T.from as property_start_time, n.name#Value@T.from as value_start_time
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"object_start_time": DateTime(1221, 1, 1, tzinfo=timezone.utc),
                            "property_start_time": DateTime(1927, 1, 1, tzinfo=timezone.utc),
                            "value_start_time": DateTime(1927, 1, 1, tzinfo=timezone.utc)}]

        s_cypher = """
        CREATE (n:City {name@T("1927", NOW): "Hangzhou"@T("1928")})
        AT TIME timePoint("1221")
        RETURN n@T.from as object_start_time, n.name@T.from as property_start_time, n.name#Value@T.from as value_start_time
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"object_start_time": DateTime(1221, 1, 1, tzinfo=timezone.utc),
                            "property_start_time": DateTime(1927, 1, 1, tzinfo=timezone.utc),
                            "value_start_time": DateTime(1928, 1, 1, tzinfo=timezone.utc)}]

    # 对象节点、属性节点或值节点的有效时间非法的情况
    def test_create_illegal_node(self):
        # 值节点时间不在属性节点时间内
        s_cypher = """
        CREATE (n:City@T("1688", NOW) {name@T("1690", NOW): "London"@T("1650", NOW)})
        RETURN n
        """
        cypher_query = STransformer.transform(s_cypher)
        with self.assertRaises(ClientError):
            self.graphdb_connector.driver.execute_query(cypher_query)
            self.dataset1.rebuild()

        s_cypher = """
        CREATE (n:City {name: "London"@T("1650", NOW)})
        RETURN n
        """
        cypher_query = STransformer.transform(s_cypher)
        with self.assertRaises(ClientError):
            self.graphdb_connector.driver.execute_query(cypher_query)
            self.dataset1.rebuild()

        # 属性节点时间不在对象节点时间内
        s_cypher = """
        CREATE (n:City@T("1688", NOW) {name@T("1650", NOW): "London"@T("1690", NOW)})
        RETURN n
        """
        cypher_query = STransformer.transform(s_cypher)
        with self.assertRaises(ClientError):
            self.graphdb_connector.driver.execute_query(cypher_query)
            self.dataset1.rebuild()

        s_cypher = """
        CREATE (n:City {name@T("1650", NOW): "London"@T("1690", NOW)})
        RETURN n
        """
        cypher_query = STransformer.transform(s_cypher)
        with self.assertRaises(ClientError):
            self.graphdb_connector.driver.execute_query(cypher_query)
            self.dataset1.rebuild()

        # 值节点不在对象节点有效时间区间内
        s_cypher = """
        CREATE (n:City {name@T("1690", NOW): "London"@T("1611", "1632")})
        AT TIME date("1688")
        """
        cypher_query = STransformer.transform(s_cypher)
        with self.assertRaises(ClientError):
            self.graphdb_connector.driver.execute_query(cypher_query)
            self.dataset1.rebuild()

        # 属性节点和对象节点的时间均不在其父节点的有效时间区间内
        s_cypher = """
        CREATE (n:City@T("1688", NOW) {name@T("1650", NOW): "London"@T("1640", NOW)})
        RETURN n
        """
        cypher_query = STransformer.transform(s_cypher)
        with self.assertRaises(ClientError):
            self.graphdb_connector.driver.execute_query(cypher_query)
            self.dataset1.rebuild()

        # 时间区间的开始时间晚于结束时间
        s_cypher = """
        CREATE (n:City {name@T("1690", NOW): "London"@T("1699", "1690")})
        AT TIME date("1688")
        RETURN n
        """
        cypher_query = STransformer.transform(s_cypher)
        with self.assertRaises(ClientError):
            self.graphdb_connector.driver.execute_query(cypher_query)
            self.dataset1.rebuild()

        # 时间格式非法
        s_cypher = """
        CREATE (n:City {name@T("16ss", NOW): "London"@T("1690", NOW)})
        AT TIME date("1688")
        """
        cypher_query = STransformer.transform(s_cypher)
        with self.assertRaises(ClientError):
            self.graphdb_connector.driver.execute_query(cypher_query)
            self.dataset1.rebuild()

    # 创建关系
    def test_create_relationship(self):
        # 在图模式中指定关系的有效时间
        # 指定有效时间区间
        s_cypher = """
        MATCH (n1:Person), (n2:City)
        WHERE n1.name = "Cathy Van" AND n2.name = "London"
        CREATE (n1)-[e:LIVE@T("1960", "1970")]->(n2)
        RETURN e@T as effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"effective_time": {"from": DateTime(1960, 1, 1, tzinfo=timezone.utc),
                                               "to": DateTime(1970, 1, 1, tzinfo=timezone.utc)}}]

        # 指定开始时间（结束时间为NOW）
        s_cypher = """
        MATCH (n:City{name:"London"})
        CREATE (m:Person{name:"Nick"})-[e:LIVE@T("2000")]->(n)
        AT TIME timePoint("1990")
        RETURN e@T as effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{
            "effective_time": {"from": DateTime(2000, 1, 1, tzinfo=timezone.utc),
                               "to": DateTime(9999, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)}}]

        # 使用AT TIME指定关系的开始时间（结束时间为NOW）
        s_cypher = """
        MATCH (n:City{name:"London"})
        CREATE (m:Person{name:"Nick"})-[e:LIVE]->(n)
        AT TIME timePoint("1990")
        RETURN e@T as effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{
            "effective_time": {"from": DateTime(1990, 1, 1, tzinfo=timezone.utc),
                               "to": DateTime(9999, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)}}]

        # 关系的有效时间必须同时落在其出点和入点的有效时间内
        s_cypher = """
        MATCH (n1:Person{name:"Mary Smith Taylor"}),(n2:Person{name:"Daniel Yang"})
        CREATE (n1)-[e:FRIEND@T("1937", "1990")]->(n2)
        RETURN e@T as effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        with self.assertRaises(ClientError):
            self.graphdb_connector.driver.execute_query(cypher_query)
            self.dataset1.rebuild()

        # 同出入点和内容的关系的有效时间不能重合
        s_cypher = """
        MATCH (n1:Person{name:"Cathy Van"}), (n2:City{name:"Paris"})
        CREATE (n1)-[e:LIVE@T("2000", "2001")]->(n2)
        RETURN e@T as effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        with self.assertRaises(ClientError):
            self.graphdb_connector.driver.execute_query(cypher_query)
            self.dataset1.rebuild()
