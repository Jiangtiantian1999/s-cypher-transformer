from datetime import timezone
from unittest import TestCase

from neo4j.exceptions import ClientError
from neo4j.time import DateTime

from test.dataset_initialization import DataSet1
from test.graphdb_connector import GraphDBConnector
from transformer.s_transformer import STransformer


class TestSet(TestCase):
    graphdb_connector = None
    dataset1 = None

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.graphdb_connector = GraphDBConnector()
        cls.graphdb_connector.local_connect()
        cls.dataset1 = DataSet1(cls.graphdb_connector.driver)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.dataset1.rebuild()
        super().tearDownClass()
        cls.graphdb_connector.close()

    # 修改某个（些）值节点的内容，如果没有满足条件（在时间窗口内有效）的值节点，则将新建一个值节点（属性节点），该值节点的有效时间由限定的时间窗口确定
    # set n.property[@T(...)] = expression
    def test_set_node_value(self):
        # 若存在满足条件的值节点，则修改这些值节点的值
        s_cypher = """
        MATCH (n:Person{name: "Mary Smith Taylor"})
        SET n.name@T("2000") = "Mary Smith Brown"
        RETURN n.name as names, n.name#Value@T as effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"names": ["Mary Smith", "Mary Smith Brown"],
                            "effective_time": [{"from": DateTime(1937, 1, 1, tzinfo=timezone.utc),
                                                "to": DateTime(1959, 12, 31, 23, 59, 59, 999999999, timezone.utc)},
                                               {"from": DateTime(1960, 1, 1, tzinfo=timezone.utc),
                                                "to": DateTime(9999, 12, 31, 23, 59, 59, 999999999, timezone.utc)}]}]

        s_cypher = """
        MATCH (n:Person{name: "Mary Smith Taylor"})
        SET n.name@T("1940", NOW) = "Mary Smith Brown"
        RETURN n.name as names, n.name#Value@T as effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"names": ["Mary Smith Brown", "Mary Smith Brown"],
                            "effective_time": [{"from": DateTime(1937, 1, 1, tzinfo=timezone.utc),
                                                "to": DateTime(1959, 12, 31, 23, 59, 59, 999999999, timezone.utc)},
                                               {"from": DateTime(1960, 1, 1, tzinfo=timezone.utc),
                                                "to": DateTime(9999, 12, 31, 23, 59, 59, 999999999, timezone.utc)}]}]

        # 若不存在满足条件的值节点，则根据指定的时间点/时间区间创建值节点
        # 指定时间点
        s_cypher = """
        CREATE (n:Person{name: "Nick"@T("1998","2010")})
        AT TIME timePoint('1998')
        SET n.name@T("2023") = "Nick Brown"
        RETURN n.name as names, n.name#Value@T as effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"names": ["Nick", "Nick Brown"],
                            "effective_time": [{"from": DateTime(1998, 1, 1, tzinfo=timezone.utc),
                                                "to": DateTime(2010, 1, 1, tzinfo=timezone.utc)},
                                               {"from": DateTime(2023, 1, 1, tzinfo=timezone.utc),
                                                "to": DateTime(9999, 12, 31, 23, 59, 59, 999999999, timezone.utc)}]}]

        # 指定时间区间
        s_cypher = """
        CREATE (n:Person{name: "Nick"@T("1998","2010")})
        AT TIME timePoint('1998')
        SET n.name@T("2015", "2023") = "Nick Brown"
        RETURN n.name as names, n.name#Value@T as effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"names": ["Nick", "Nick Brown"],
                            "effective_time": [{"from": DateTime(1998, 1, 1, tzinfo=timezone.utc),
                                                "to": DateTime(2010, 1, 1, tzinfo=timezone.utc)},
                                               {"from": DateTime(2015, 1, 1, tzinfo=timezone.utc),
                                                "to": DateTime(2023, 1, 1, tzinfo=timezone.utc)}]}]

        # 值节点的内容不能为null
        s_cypher = """
        CREATE (n:Person{name: "Nick"})
        AT TIME timePoint('2023')
        SET n.name@T("2000") = null
        RETURN n.name as names, n.name#Value@T as effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        with self.assertRaises(ClientError):
            self.graphdb_connector.driver.execute_query(cypher_query)
            self.dataset1.rebuild()

        # 若不存在满足条件的值节点，则根据指定的时间点/时间区间创建值节点，若对象节点或属性节点的有效时间不包含待创建值节点的有效时间，则报错
        s_cypher = """
        CREATE (n:Person{name: "Nick"})
        AT TIME timePoint('2023')
        SET n.name@T("2000") = "Nick Brown"
        RETURN n.name as names, n.name#Value@T as effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        with self.assertRaises(ClientError):
            self.graphdb_connector.driver.execute_query(cypher_query)
            self.dataset1.rebuild()

    # 为实体设置单个属性
    # set n.property = expression
    def test_set_node_property(self):
        # 实体没有该属性时，若属性值不为null，创建属性节点和值节点，属性节点和值节点的有效时间均为[operation_time, NOW]（若属性值为null，不进行任何操作）
        s_cypher = """
        MATCH (n {name: "Pauline Boutler"})
        SET n.gender = "Male"
        AT TIME timePoint("2023")
        RETURN n@T as object_interval, n.gender@T as property_interval, n.gender#Value@T as value_interval
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{
            "object_interval": {"from": DateTime(1978, 1, 1, tzinfo=timezone.utc),
                                "to": DateTime(9999, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)},
            "property_interval": {"from": DateTime(2023, 1, 1, tzinfo=timezone.utc),
                                  "to": DateTime(9999, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)},
            "value_interval": {"from": DateTime(2023, 1, 1, tzinfo=timezone.utc),
                               "to": DateTime(9999, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)}}]

        # 实体存在该属性时，逻辑删除原有值节点（若有），若属性值不为null，创建值节点，值节点的有效时间为[operation_time, NOW]
        s_cypher = """
        MATCH (n {name: "Pauline Boutler"})
        SET n.name = "Pauline Boutler Brown"
        AT TIME timePoint("2023")
        RETURN n@T as object_interval, n.name@T as property_interval, n.name as property_value, n.name#Value@T as value_interval
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{
            "object_interval": {"from": DateTime(1978, 1, 1, tzinfo=timezone.utc),
                                "to": DateTime(9999, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)},
            "property_interval": {"from": DateTime(1978, 1, 1, tzinfo=timezone.utc),
                                  "to": DateTime(9999, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)},
            "property_value": ["Pauline Boutler", "Pauline Boutler Brown"],
            "value_interval": [{"from": DateTime(1978, 1, 1, tzinfo=timezone.utc),
                                "to": DateTime(2022, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)},
                               {"from": DateTime(2023, 1, 1, tzinfo=timezone.utc),
                                "to": DateTime(9999, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)}]}]

        # 实体存在该属性时，逻辑删除原有值节点（若有），若属性值为null，不创建值节点
        s_cypher = """
        MATCH (n {name: "Pauline Boutler"})
        SET n.name = null
        AT TIME timePoint("2023")
        RETURN n@T as object_interval, n.name@T as property_interval, n.name#T("2022") as property_value, n.name#Value@T as value_interval
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{
            "object_interval": {"from": DateTime(1978, 1, 1, tzinfo=timezone.utc),
                                "to": DateTime(9999, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)},
            "property_interval": {"from": DateTime(1978, 1, 1, tzinfo=timezone.utc),
                                  "to": DateTime(9999, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)},
            "property_value": "Pauline Boutler",
            "value_interval": {"from": DateTime(1978, 1, 1, tzinfo=timezone.utc),
                               "to": DateTime(2022, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)}}]

        # 只能为结束时间为NOW的实体设置属性，若实体存在该属性，该属性节点的结束时间也需为NOW
        s_cypher = """
        CREATE (n:Person@T("1999","2015") {name@T("1999","2015"): "Nick"@T("1999","2015")})
        SET n.name = "Nick Brown"
        AT TIME timePoint("2000")
        """
        cypher_query = STransformer.transform(s_cypher)
        with self.assertRaises(ClientError):
            self.graphdb_connector.driver.execute_query(cypher_query)
            self.dataset1.rebuild()

        # 若已存在该属性下的值节点，需逻辑删除原有值节点，操作时间需要晚于结束时间为NOW的值节点的开始时间，且操作时间不能与历史值节点的有效时间重合
        s_cypher = """
        CREATE (n:Person@T("2000", NOW) {name@T("2000", NOW): "Nick"@T("2000", NOW)})
        SET n.name = "Nick Brown"
        AT TIME timePoint("2000")
        """
        cypher_query = STransformer.transform(s_cypher)
        with self.assertRaises(ClientError):
            self.graphdb_connector.driver.execute_query(cypher_query)
            self.dataset1.rebuild()

        s_cypher = """
        CREATE (n:Person@T("2000", NOW) {name@T("2000", NOW): "Nick"@T("2000", "2015")})
        SET n.name = "Nick Brown"
        AT TIME timePoint("2003")
        """
        cypher_query = STransformer.transform(s_cypher)
        with self.assertRaises(ClientError):
            self.graphdb_connector.driver.execute_query(cypher_query)
            self.dataset1.rebuild()

    # 为实体设置一组属性，使用=赋值时需先逻辑删除实体原有的所有值节点
    # set n = {...}或set n += {...}
    def test_set_node_properties(self):
        # 实体没有该属性，且属性值不为null时，创建属性节点和值节点，属性节点和值节点的有效时间均为[operation_time, NOW]（属性值为null时不做任何操作）
        # 使用=赋值时需先逻辑删除实体原有的所有值节点
        s_cypher = """
        MATCH (n {name: "Pauline Boutler"})
        SET n = {gender: "Male"}
        AT TIME timePoint("2023")
        RETURN n@T as object_interval, n.gender@T as gender_property_interval, n.gender#Value@T as gender_value_interval, n.name#Value@T as name_value_interval
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{
            "object_interval": {"from": DateTime(1978, 1, 1, tzinfo=timezone.utc),
                                "to": DateTime(9999, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)},
            "gender_property_interval": {"from": DateTime(2023, 1, 1, tzinfo=timezone.utc),
                                         "to": DateTime(9999, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)},
            "gender_value_interval": {"from": DateTime(2023, 1, 1, tzinfo=timezone.utc),
                                      "to": DateTime(9999, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)},
            "name_value_interval": {"from": DateTime(1978, 1, 1, tzinfo=timezone.utc),
                                    "to": DateTime(2022, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)}}]

        # 使用+=赋值时不需逻辑删除实体原有的其他属性下的值节点
        s_cypher = """
        MATCH (n {name: "Pauline Boutler"})
        SET n += {gender: "Male"}
        AT TIME timePoint("2023")
        RETURN n@T as object_interval, n.gender@T as gender_property_interval, n.gender#Value@T as gender_value_interval, n.name#Value@T as name_value_interval
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{
            "object_interval": {"from": DateTime(1978, 1, 1, tzinfo=timezone.utc),
                                "to": DateTime(9999, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)},
            "gender_property_interval": {"from": DateTime(2023, 1, 1, tzinfo=timezone.utc),
                                         "to": DateTime(9999, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)},
            "gender_value_interval": {"from": DateTime(2023, 1, 1, tzinfo=timezone.utc),
                                      "to": DateTime(9999, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)},
            "name_value_interval": {"from": DateTime(1978, 1, 1, tzinfo=timezone.utc),
                                    "to": DateTime(9999, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)}}]

        # 实体存在该属性，且属性值不为null时，仅创建值节点，值节点的有效时间为[operation_time, NOW]
        s_cypher = """
        MATCH (n {name: "Pauline Boutler"})
        SET n = {name: "Pauline Boutler Brown"}
        AT TIME timePoint("2023")
        RETURN n@T as object_interval, n.name@T as property_interval, n.name as property_value, n.name#Value@T as value_interval
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{
            "object_interval": {"from": DateTime(1978, 1, 1, tzinfo=timezone.utc),
                                "to": DateTime(9999, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)},
            "property_interval": {"from": DateTime(1978, 1, 1, tzinfo=timezone.utc),
                                  "to": DateTime(9999, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)},
            "property_value": ["Pauline Boutler", "Pauline Boutler Brown"],
            "value_interval": [{"from": DateTime(1978, 1, 1, tzinfo=timezone.utc),
                                "to": DateTime(2022, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)},
                               {"from": DateTime(2023, 1, 1, tzinfo=timezone.utc),
                                "to": DateTime(9999, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)}]}]

        # 实体存在该属性时，逻辑删除原有值节点（若有），若属性值为null，不创建值节点
        s_cypher = """
        MATCH (n {name: "Pauline Boutler"})
        SET n = {name: null}
        AT TIME timePoint("2023")
        RETURN n@T as object_interval, n.name@T as property_interval, n.name as property_value, n.name#Value@T as value_interval
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{
            "object_interval": {"from": DateTime(1978, 1, 1, tzinfo=timezone.utc),
                                "to": DateTime(9999, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)},
            "property_interval": {"from": DateTime(1978, 1, 1, tzinfo=timezone.utc),
                                  "to": DateTime(9999, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)},
            "property_value": "Pauline Boutler",
            "value_interval": {"from": DateTime(1978, 1, 1, tzinfo=timezone.utc),
                               "to": DateTime(2022, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)}}]

        # 只能为结束时间为NOW的实体设置属性，若实体存在该属性，该属性节点的结束时间也需为NOW
        s_cypher = """
        CREATE (n:Person@T("1999","2015") {name@T("1999","2015"): "Nick"@T("1999","2015")})
        SET n = {name: "Nick Brown"}
        AT TIME timePoint("2000")
        """
        cypher_query = STransformer.transform(s_cypher)
        with self.assertRaises(ClientError):
            self.graphdb_connector.driver.execute_query(cypher_query)
            self.dataset1.rebuild()

        s_cypher = """
        CREATE (n:Person@T("1999",NOW) {name@T("1999","2015"): "Nick"@T("1999","2015")})
        SET n = {name: "Nick Brown"}
        AT TIME timePoint("2000")
        """
        cypher_query = STransformer.transform(s_cypher)
        with self.assertRaises(ClientError):
            self.graphdb_connector.driver.execute_query(cypher_query)
            self.dataset1.rebuild()

        # 若已存在该属性下的值节点，需逻辑删除原有值节点，操作时间需要晚于结束时间为NOW的值节点的开始时间，且操作时间不能与历史值节点的有效时间重合
        s_cypher = """
        CREATE (n:Person@T("2000", NOW) {name@T("2000", NOW): "Nick"@T("2000", NOW)})
        SET n = {name: "Nick Brown"}
        AT TIME timePoint("2000")
        """
        cypher_query = STransformer.transform(s_cypher)
        with self.assertRaises(ClientError):
            self.graphdb_connector.driver.execute_query(cypher_query)
            self.dataset1.rebuild()

        s_cypher = """
        CREATE (n:Person@T("2000", NOW) {name@T("2000", NOW): "Nick"@T("2000", "2015")})
        SET n = {name: "Nick Brown"}
        AT TIME timePoint("2003")
        """
        cypher_query = STransformer.transform(s_cypher)
        with self.assertRaises(ClientError):
            self.graphdb_connector.driver.execute_query(cypher_query)
            self.dataset1.rebuild()

    # 为关系设置单个属性
    def test_set_relationship_property(self):
        # 添加单个属性
        s_cypher = """
        MATCH (:Person {name: "Pauline Boutler"})-[e:LIVE]->(:City {name: "London"})
        SET e.code = "255389"
        RETURN properties(e) as properties
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"properties": {"code": "255389", "intervalFrom": DateTime(2004, 1, 1, tzinfo=timezone.utc),
                                           "intervalTo": DateTime(9999, 12, 31, 23, 59, 59, 999999999,
                                                                  tzinfo=timezone.utc)}}]
        # 删除单个属性
        s_cypher = """
        MATCH (:Person {name: "Pauline Boutler"})-[e:LIVE]->(:City {name: "London"})
        SET e.code = null
        RETURN properties(e) as properties
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"properties": {"intervalFrom": DateTime(2004, 1, 1, tzinfo=timezone.utc),
                                           "intervalTo": DateTime(9999, 12, 31, 23, 59, 59, 999999999,
                                                                  tzinfo=timezone.utc)}}]

    # 为关系设置一组属性，使用=赋值时需先逻辑删除关系原有的所有属性
    # set n = {...}或set n += {...}
    def test_set_relationship_properties(self):
        # 使用=赋值时需先删除关系原有的所有属性
        s_cypher = """
        MATCH (:Person {name: "Pauline Boutler"})-[e:LIVE]->(:City {name: "London"})
        SET e.type = 0
        SET e = {code: "255389"}
        RETURN properties(e) as properties
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{
            "properties": {"code": "255389", "intervalFrom": DateTime(2004, 1, 1, tzinfo=timezone.utc),
                           "intervalTo": DateTime(9999, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)}}]

        # 使用+=赋值时不需删除实体原有的其他属性
        s_cypher = """
        MATCH (:Person {name: "Pauline Boutler"})-[e:LIVE]->(:City {name: "London"})
        SET e += {type: 0}
        RETURN properties(e) as properties
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{
            "properties": {"code": "255389", "type": 0, "intervalFrom": DateTime(2004, 1, 1, tzinfo=timezone.utc),
                           "intervalTo": DateTime(9999, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)}}]
        # 使用null删除关系的属性
        s_cypher = """
        MATCH (:Person {name: "Pauline Boutler"})-[e:LIVE]->(:City {name: "London"})
        SET e += {type: null}
        RETURN properties(e) as properties
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{
            "properties": {"code": "255389", "intervalFrom": DateTime(2004, 1, 1, tzinfo=timezone.utc),
                           "intervalTo": DateTime(9999, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)}}]

        s_cypher = """
        MATCH (:Person {name: "Pauline Boutler"})-[e:LIVE]->(:City {name: "London"})
        SET e = {code: null}
        RETURN properties(e) as properties
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{
            "properties": {"intervalFrom": DateTime(2004, 1, 1, tzinfo=timezone.utc),
                           "intervalTo": DateTime(9999, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)}}]

    # 设置对象节点的有效时间
    def test_set_object_effective_time(self):
        s_cypher = """
        MATCH (n {name: "Pauline Boutler"})
        SET n@T("1960", NOW)
        RETURN n@T as effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{
            "effective_time": {"from": DateTime(1960, 1, 1, tzinfo=timezone.utc),
                               "to": DateTime(9999, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)}}]

        # 对象节点的有效时间必须覆盖其属性节点的有效时间
        s_cypher = """
        MATCH (n {name: "Pauline Boutler"})
        SET n@T("1980", NOW)
        RETURN n@T as effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        with self.assertRaises(ClientError):
            self.graphdb_connector.driver.execute_query(cypher_query)
            self.dataset1.rebuild()

        # 对象节点的有效时间必须覆盖其关系的有效时间
        s_cypher = """
        MATCH (n {name: "Pauline Boutler"})
        SET n@T("1980","1990").name@T("1980", "1990")#Value@T("1980", "1990")
        RETURN n@T as effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        with self.assertRaises(ClientError):
            self.graphdb_connector.driver.execute_query(cypher_query)
            self.dataset1.rebuild()

    # 设置属性节点的有效时间
    def test_set_property_effective_time(self):
        s_cypher = """
        MATCH (n {name: "Pauline Boutler"})
        SET n@T("1960", NOW).name@T("1960", NOW)
        RETURN n.name@T as effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{
            "effective_time": {"from": DateTime(1960, 1, 1, tzinfo=timezone.utc),
                               "to": DateTime(9999, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)}}]

        # 属性节点的有效时间必须落在其对象节点的有效时间内
        s_cypher = """
        MATCH (n {name: "Pauline Boutler"})
        SET n.name@T("1960", NOW)
        RETURN n.name@T as effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        with self.assertRaises(ClientError):
            self.graphdb_connector.driver.execute_query(cypher_query)
            self.dataset1.rebuild()

        # 属性节点的有效时间必须覆盖其值节点的有效时间
        s_cypher = """
        MATCH (n {name: "Pauline Boutler"})
        SET n.name@T("1980", NOW)
        RETURN n.name@T as effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        with self.assertRaises(ClientError):
            self.graphdb_connector.driver.execute_query(cypher_query)
            self.dataset1.rebuild()

    # 设置值节点的有效时间
    def test_set_value_effective_time(self):
        # 修改在操作时间有效的值节点的有效时间
        s_cypher = """
        MATCH (n {name: "Mary Smith Taylor"})
        SET n.name#Value@T("1937", "1947-12-31T23:59:59.999999999")
        AT TIME timePoint("1937")
        RETURN n.name#Value@T as effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{
            "effective_time": [{"from": DateTime(1937, 1, 1, tzinfo=timezone.utc),
                                "to": DateTime(1947, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)},
                               {"from": DateTime(1960, 1, 1, tzinfo=timezone.utc),
                                "to": DateTime(9999, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)}]}]

        # 值节点的有效时间必须落在其属性节点的有效时间内
        s_cypher = """
        MATCH (n {name: "Mary Smith Taylor"})
        SET n.name#Value@T("1930", "1959")
        RETURN n.name#Value@T as effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        with self.assertRaises(ClientError):
            self.graphdb_connector.driver.execute_query(cypher_query)
            self.dataset1.rebuild()

        # 值节点的有效时间不能与同属性节点下的其他属性节点的有效时间重合
        s_cypher = """
        MATCH (n {name: "Mary Smith Taylor"})
        SET n.name#Value@T("1937", "1947-12-31T23:59:59.999999999")
        AT TIME timePoint(NOW)
        RETURN n.name#Value@T as effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        with self.assertRaises(ClientError):
            self.graphdb_connector.driver.execute_query(cypher_query)
            self.dataset1.rebuild()

    # 设置关系的有效时间
    def test_set_relationship_effective_time(self):
        s_cypher = """
        MATCH (:Person {name: "Pauline Boutler"})-[e:LIVE]->(:City {name: "London"})
        SET e@T("2010", "2020")
        RETURN e@T as effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"effective_time": {"from": DateTime(2010, 1, 1, tzinfo=timezone.utc),
                                               "to": DateTime(2020, 1, 1, tzinfo=timezone.utc)}}]

        # 关系的有效时间必须同时落在其出点和入点的有效时间内
        s_cypher = """
        MATCH (:Person {name: "Pauline Boutler"})-[e:LIVE]->(:City {name: "London"})
        SET e@T("1960", NOW)
        RETURN e@T as effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        with self.assertRaises(ClientError):
            self.graphdb_connector.driver.execute_query(cypher_query)
            self.dataset1.rebuild()

    # 设置实体的标签
    def test_set_labels(self):
        s_cypher = """
        MATCH (n {name: "Pauline Boutler"})
        SET n:Student
        RETURN labels(n) as labels
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"labels": ["Object", "Person", "Student"]}]

        # 不能设置关系的标签
        s_cypher = """
        MATCH (:Person {name: "Pauline Boutler"})-[e:LIVE]->(:City {name: "London"})
        SET e:FRIEND
        RETURN labels(e) as labels
        """
        cypher_query = STransformer.transform(s_cypher)
        with self.assertRaises(ClientError):
            self.graphdb_connector.driver.execute_query(cypher_query)
            self.dataset1.rebuild()
