from datetime import timezone
from unittest import TestCase

from neo4j.time import DateTime, Date, Time, Duration
import pytz

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

    # 为表达式提供变量
    def test_with_introduce_variable(self):
        s_cypher = """
        MATCH (n:Person{name: "Pauline Boutler"})
        WITH n AS person
        RETURN person.name@T as effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"effective_time": {"from": DateTime(1978, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc),
                                               "to": DateTime(9999, 12, 31, 23, 59, 59, 999999999,
                                                              tzinfo=timezone.utc)}}]

        s_cypher = """
        MATCH (n:Person)
        WHERE n.name CONTAINS 'Pauline'
        WITH n AS person
        RETURN person.name@T as effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"effective_time": {"from": DateTime(1978, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc),
                                               "to": DateTime(9999, 12, 31, 23, 59, 59, 999999999,
                                                              tzinfo=timezone.utc)}}]

        s_cypher = """
        MATCH (person:Person)-[:LIVE@T("2000")]->(city:City)
        WITH person, city
        WHERE person.name@T.from >= timePoint("1960") AND city.name = "Antwerp"
        RETURN person.name as person_name, city.name@T.from as city_effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"person_name": "Daniel Yang",
                            "city_effective_time": DateTime(1581, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc)}]

        # 日期变量
        s_cypher = """
        WITH date({year: 1989, month: 12, day: 15}) AS dd
        RETURN dd
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"dd": Date(1989, 12, 15)}]

        s_cypher = """
        WITH interval(timePoint("1960"),timePoint({year: 1984, month: 10, day: 11})) AS interval1, interval("2023W26",now()) AS interval2
        RETURN interval1, interval1 DURING interval2 as result
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"interval1": {'from': DateTime(1960, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc),
                                          'to': DateTime(1984, 10, 11, 0, 0, 0, 0, tzinfo=timezone.utc)},
                            "result": False}]

        # 通配符的使用
        s_cypher = """
        MATCH (a:Person)-[e@T("2000")]->(b:Person)
        WITH *, type(e) AS connectionType
        RETURN a.name as a_name, b.name as b_name, connectionType
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"a_name": "Peter Burton", "b_name": "Cathy Van", "connectionType": "FRIEND"},
                           {"a_name": ["Mary Smith", "Mary Smith Taylor"],
                            "b_name": "Peter Burton", "connectionType": "FRIEND"}]

    # 计算操作
    def test_with_compute(self):
        s_cypher = """
        MATCH (n:Person{name: "Pauline Boutler"})
        WITH n.name + "000" as name
        RETURN name
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"name": "Pauline Boutler000"}]

        s_cypher = """
        MATCH (n:Person{name: 'Daniel Yang'})
        WITH n.name + ' Justin' as name
        RETURN name;
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"name": "Daniel Yang Justin"}]

        s_cypher = """
        MATCH (n:Person{name: "Pauline Boutler"})-[e:FRIEND@T("2002")]->(n2:Person)
        WITH (size(n.name) - size(n2.name)) as name
        RETURN name;
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"name": 6}]

        s_cypher = """
        MATCH (n1:Person{name: "Pauline Boutler"})-[e:FRIEND@T("2002")]->(n2:Person)
        WITH n2, size(n2.name) * 2 AS double_name_size
        RETURN n2.name as name, double_name_size
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"name": "Cathy Van", "double_name_size": 18}]

    # 使用函数
    def test_with_function(self):
        s_cypher = """
        MATCH (n:Person{name: 'Daniel Yang'})
        WITH duration.between(n.name@T.from, datetime("2000")) as effective_time
        RETURN effective_time;
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"effective_time": Duration(months=60, days=0, seconds=0, nanoseconds=0)}]

    # 进行排序和限制
    def test_with_order_limit(self):
        s_cypher = """
        MATCH (n1:Person)-[:LIVE@T("1985")]->(n2:City {name: "Brussels"})
        WITH n1
        ORDER BY n1.name DESC
        LIMIT 3
        RETURN collect(n1.name) as names
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"names": ['Pauline Boutler', 'Cathy Van', ['Mary Smith', 'Mary Smith Taylor']]}]

    # 过滤
    def test_with_filter(self):
        s_cypher = """
        UNWIND [
        datetime('2005-07-21T21:50:32.142+0100'),
        datetime('2015-W30-2T214032.142Z'),
        datetime('2010T224032-0100'),
        datetime('20170721T21:40-01:30'),
        datetime('2015-W33T2140-02'),
        datetime('2008202T21+18:00'),
        datetime('1997-09-21T21:40:32.142[Europe/London]'),
        datetime('1989-07-21T21:40:32.142-04[America/New_York]')
        ] AS theDate
        WITH theDate
        LIMIT 3
        WHERE theDate >= datetime('2008202T21+18:00')
        RETURN theDate
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"theDate": DateTime(2015, 7, 21, 21, 40, 32, 142000000, tzinfo=timezone.utc)},
                           {"theDate": DateTime(2010, 1, 1, 22, 40, 32, 0, tzinfo=pytz.FixedOffset(-60))}]

    # 多步骤查询中的连接
    def test_with_multi_steps(self):
        s_cypher = """
        MATCH (p:Person)-[:FRIEND]->(n2:Person)
        WITH p, collect(n2) AS friends
        WHERE size(friends) >= 2
        WITH p, friends
        ORDER BY size(friends) DESC
        RETURN p.name as person_name, size(friends) as friend_num
        ORDER BY person_name
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"person_name": ['Mary Smith', 'Mary Smith Taylor'], "friend_num": 2},
                           {"person_name": 'Peter Burton', "friend_num": 2}]
