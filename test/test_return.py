from datetime import timezone
from unittest import TestCase

from neo4j.exceptions import ClientError
from neo4j.time import DateTime, Time, Duration

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
    def test_return_property(self):
        # 返回节点属性（单个）
        s_cypher = """
        MATCH (n1:Person)-[e:LIVE@T("2000")]->(n2:City {name: "Brussels"})
        RETURN n1.name as person_name
        ORDER BY person_name
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"person_name": "Cathy Van"}, {"person_name": "Pauline Boutler"}]

        # 返回节点属性（多个）
        s_cypher = """
        MATCH (n1:Person)-[e:LIVE@T("1990")]->(n2:City {name: "Antwerp"})
        RETURN n1.name as person_name
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"person_name": ["Mary Smith", "Mary Smith Taylor"]}]

        # 返回指定有效时间下的节点属性
        s_cypher = """
        MATCH (n1:Person)-[e:LIVE@T("1990")]->(n2:City {name: "Antwerp"})
        RETURN n1.name@T(NOW) as person_name
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"person_name": "Mary Smith Taylor"}]

    # 返回有效时间
    def test_return_effective_time(self):
        # 返回对象节点有效时间
        s_cypher = """
        MATCH (n:Person {name: "Mary Smith Taylor"})
        RETURN n@T as effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"effective_time": {"from": DateTime(1937, 1, 1, tzinfo=timezone.utc),
                                               "to": DateTime(9999, 12, 31, 23, 59, 59, 999999999,
                                                              tzinfo=timezone.utc)}}]

        # 返回属性节点有效时间
        s_cypher = """
        MATCH (n:Person {name: "Mary Smith Taylor"})
        RETURN n.name@T as effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"effective_time": {"from": DateTime(1937, 1, 1, tzinfo=timezone.utc),
                                               "to": DateTime(9999, 12, 31, 23, 59, 59, 999999999,
                                                              tzinfo=timezone.utc)}}]

        # 返回值节点有效时间
        s_cypher = """
        MATCH (n:Person {name: "Mary Smith Taylor"})
        RETURN n.name#Value@T as effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"effective_time": [{"from": DateTime(1937, 1, 1, tzinfo=timezone.utc),
                                                "to": DateTime(1959, 12, 31, 23, 59, 59, 999999999,
                                                               tzinfo=timezone.utc)},
                                               {"from": DateTime(1960, 1, 1, tzinfo=timezone.utc),
                                                "to": DateTime(9999, 12, 31, 23, 59, 59, 999999999,
                                                               tzinfo=timezone.utc)}]}]

        # 返回指定有效时间下的值节点有效时间
        s_cypher = """
        MATCH (n:Person {name: "Mary Smith Taylor"})
        RETURN n.name@T("NOW")@T as effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"effective_time": {"from": DateTime(1960, 1, 1, tzinfo=timezone.utc),
                                               "to": DateTime(9999, 12, 31, 23, 59, 59, 999999999,
                                                              tzinfo=timezone.utc)}}]

        # 错误用法检测
        s_cypher = """
        MATCH (n:Person{name: 'Pauline Boutler'})
        WITH n.name AS name
        RETURN name@T
        """
        cypher_query = STransformer.transform(s_cypher)
        with self.assertRaises(ClientError):
            self.graphdb_connector.driver.execute_query(cypher_query)

            # 测试ORDER BY和LIMIT

    def test_order_by(self):
        # 根据有效时间返回结果，未作设置，默认使用map的比较方法（先比较to，再比较from）
        s_cypher = """
        MATCH (p:Person)
        RETURN p@T as effective_time
        ORDER BY effective_time DESC
        LIMIT 3
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"effective_time": {"from": DateTime(1995, 1, 1, tzinfo=timezone.utc),
                                               "to": DateTime(9999, 12, 31, 23, 59, 59, 999999999,
                                                              tzinfo=timezone.utc)}},
                           {"effective_time": {"from": DateTime(1978, 1, 1, tzinfo=timezone.utc),
                                               "to": DateTime(9999, 12, 31, 23, 59, 59, 999999999,
                                                              tzinfo=timezone.utc)}},
                           {"effective_time": {"from": DateTime(1967, 1, 1, tzinfo=timezone.utc),
                                               "to": DateTime(9999, 12, 31, 23, 59, 59, 999999999,
                                                              tzinfo=timezone.utc)}}]

        s_cypher = """
        MATCH (p:Person)
        RETURN p.name@T(NOW) as name, p@T.from.year as birth_year
        ORDER BY birth_year, name
        LIMIT 3
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"name": "Cathy Van", "birth_year": 1960}, {"name": "Peter Burton", "birth_year": 1960},
                           {"name": "Mary Smith Taylor", "birth_year": 1960}]

    # 测试聚合函数
    def test_aggregate_function(self):
        # 测试collect
        s_cypher = """
        MATCH (a:Person)-[:FRIEND]->(b:Person)
        WITH *
        ORDER BY b.name
        RETURN a.name as person, collect(b.name@T(NOW)) as friends
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [
            {"person": ["Mary Smith", "Mary Smith Taylor"], "friends": ["Pauline Boutler", "Peter Burton"]},
            {"person": "Pauline Boutler", "friends": ["Cathy Van"]},
            {"person": "Peter Burton", "friends": ["Cathy Van", "Daniel Yang"]}]

        # 测试avg, max, min
        s_cypher = """
        MATCH (p:Person)
        WITH 2023 - p@T.from.year as age
        RETURN round(avg(age), 2) AS AverageAge, max(age) AS Oldest, min(age) AS Youngest;
        """

        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"AverageAge": 56.83, "Oldest": 86, "Youngest": 28}]

        # 不能对时间点或时间区间做avg聚合运算
        s_cypher = """
        MATCH (p:Person)
        RETURN avg(p@T.from) AS AverageBirth, min(p@T.from) AS Oldest;
        """
        cypher_query = STransformer.transform(s_cypher)
        with self.assertRaises(ClientError):
            self.graphdb_connector.driver.execute_query(cypher_query)

    # 测试时间点和时间区间的运算操作
    def test_time_operate(self):
        # 时间点DURING时间区间
        s_cypher = """
        WITH timePoint("2015-W30") as time_point, interval("2015Q20",NOW) as interval
        RETURN time_point, interval, time_point DURING interval as result
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"time_point": DateTime(2015, 6, 20, tzinfo=timezone.utc),
                            "interval": {"from": DateTime(2015, 4, 1, tzinfo=timezone.utc),
                                         "to": DateTime(9999, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)},
                            "result": True}]

        # 时间区间DURING时间点
        s_cypher = """
        WITH interval("2015202",timePoint({year:2016, month:10, day:1})) as interval1, interval("2015Q20",now()) as interval2
        RETURN interval1, interval2, interval1 DURING interval2 as result
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"interval1": {"from": DateTime(2015, 7, 21, tzinfo=timezone.utc),
                                          "to": DateTime(2016, 10, 1, tzinfo=timezone.utc)},
                            "interval2": {"from": DateTime(2015, 4, 1, tzinfo=timezone.utc),
                                          "to": DateTime(9999, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)},
                            "result": True}]

        # OVERLAPS
        s_cypher = """
        WITH interval("2015-Q2","2015-06-30") as interval1, interval("2015Q260","2015-W30-2") as interval2
        RETURN interval1, interval2, interval1 OVERLAP interval2 as result
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"interval1": {"from": DateTime(2015, 4, 1, tzinfo=timezone.utc),
                                          "to": DateTime(2015, 6, 30, tzinfo=timezone.utc)},
                            "interval2": {"from": DateTime(2015, 5, 30, tzinfo=timezone.utc),
                                          "to": DateTime(2015, 7, 21, tzinfo=timezone.utc)}, "result": True}]

        # 时间点之间不能相减
        s_cypher = """
        MATCH (p:Person{name: "Mary Smith Taylor"})-[:FRIEND]->(b:Person)
        RETURN p.name@T(NOW) as person1, b.name@T(NOW) as person2, p@T.from - b@T.from AS AgeDiff
        ORDER BY person2
        """
        cypher_query = STransformer.transform(s_cypher)
        with self.assertRaises(ClientError):
            self.graphdb_connector.driver.execute_query(cypher_query)

        # 开始时间不能晚于结束时间
        s_cypher = """
        RETURN interval("2010","2009")
        """
        cypher_query = STransformer.transform(s_cypher)
        with self.assertRaises(ClientError):
            self.graphdb_connector.driver.execute_query(cypher_query)

    # 测试时间区间的运算函数
    def test_time_function(self):
        # interval.range
        s_cypher = """
        WITH interval(datetime("2015-Q2"), datetime("2015-06-30")) as interval1, interval(datetime("2015Q260"), datetime("2015-W30-2")) as interval2
        RETURN interval1, interval2, interval.range([interval1, interval2]) as range_interval
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"interval1": {"from": DateTime(2015, 4, 1, tzinfo=timezone.utc),
                                          "to": DateTime(2015, 6, 30, tzinfo=timezone.utc)},
                            "interval2": {"from": DateTime(2015, 5, 30, tzinfo=timezone.utc),
                                          "to": DateTime(2015, 7, 21, tzinfo=timezone.utc)},
                            "range_interval": {"from": DateTime(2015, 4, 1, tzinfo=timezone.utc),
                                               "to": DateTime(2015, 7, 21, tzinfo=timezone.utc)}}]
        # interval.intersection
        s_cypher = """
        WITH interval(datetime("2015-Q2"), datetime("2015-06-30")) as interval1, interval(datetime("2015Q260"), datetime("2015-W30-2")) as interval2
        RETURN interval1, interval2, interval.intersection([interval1, interval2]) as intersection_interval
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"interval1": {"from": DateTime(2015, 4, 1, tzinfo=timezone.utc),
                                          "to": DateTime(2015, 6, 30, tzinfo=timezone.utc)},
                            "interval2": {"from": DateTime(2015, 5, 30, tzinfo=timezone.utc),
                                          "to": DateTime(2015, 7, 21, tzinfo=timezone.utc)},
                            "intersection_interval": {"from": DateTime(2015, 5, 30, tzinfo=timezone.utc),
                                                      "to": DateTime(2015, 6, 30, tzinfo=timezone.utc)}}]

        # interval.difference
        s_cypher = """
        WITH interval(time("8:20"), time("13:00")) as interval1, interval(time("15:08"), time("23:00")) as interval2
        RETURN interval1, interval2, interval.difference(interval1, interval2) as difference_interval
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [
            {"interval1": {"from": Time(8, 20, tzinfo=timezone.utc), "to": Time(13, tzinfo=timezone.utc)},
             "interval2": {"from": Time(15, 8, tzinfo=timezone.utc), "to": Time(23, tzinfo=timezone.utc)},
             "difference_interval": Duration(hours=2, minutes=8)}]

        # 不能对相交的时间区间做difference
        s_cypher = """
        WITH interval(date("2015"), date("2019")) as interval1, interval(date("2017"), date("2023")) as interval2
        RETURN interval1, interval2, interval.difference(interval1, interval2) as difference_interval
        """
        cypher_query = STransformer.transform(s_cypher)
        with self.assertRaises(ClientError):
            self.graphdb_connector.driver.execute_query(cypher_query)
