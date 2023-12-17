from datetime import timezone
from unittest import TestCase

from neo4j.time import DateTime

from test.dataset_initialization import DataSet1
from test.graphdb_connector import GraphDBConnector
from transformer.s_transformer import STransformer


class TestTimeWindow(TestCase):
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
        cls.clear(cls)
        cls.dataset1.rebuild()
        super().tearDownClass()
        cls.graphdb_connector.close()

    def clear(self):
        s_cypher = """
        SNAPSHOT NULL
        """
        cypher_query = STransformer.transform(s_cypher)
        self.graphdb_connector.driver.execute_query(cypher_query)

        s_cypher = """
        SCOPE NULL
        """
        cypher_query = STransformer.transform(s_cypher)
        self.graphdb_connector.driver.execute_query(cypher_query)

    # 测试AT TIME
    def test_at_time(self):
        s_cypher = """
        MATCH (n:Person)
        AT TIME datetime("1938202T21+18:00")
        RETURN n.name as person
        ORDER BY person
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"person": ["Mary Smith", "Mary Smith Taylor"]}]

        s_cypher = """
        MATCH (n:Person)
        AT TIME timePoint("1960")
        RETURN n.name as person
        ORDER BY person
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"person": ["Mary Smith", "Mary Smith Taylor"]}, {"person": "Cathy Van"},
                           {"person": "Peter Burton"}]

    # 测试BETWEEN
    def test_between(self):
        s_cypher = """
        MATCH (n:Person)-[e:FRIEND]->(m:Person)
        BETWEEN interval(timePoint("2000"), "2010")
        RETURN n.name as person1, m.name as person2
        ORDER BY person1, person2
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"person1": ["Mary Smith", "Mary Smith Taylor"], "person2": "Pauline Boutler"},
                           {"person1": ["Mary Smith", "Mary Smith Taylor"], "person2": "Peter Burton"},
                           {"person1": "Pauline Boutler", "person2": "Cathy Van"},
                           {"person1": "Peter Burton", "person2": "Cathy Van"}]

        s_cypher = """
        MATCH (n:Person)-[e:FRIEND]->(m:Person)
        BETWEEN interval("2015", NOW)
        RETURN n.name as person1, m.name as person2
        ORDER BY person1, person2
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"person1": ["Mary Smith", "Mary Smith Taylor"], "person2": "Pauline Boutler"},
                           {"person1": ["Mary Smith", "Mary Smith Taylor"], "person2": "Peter Burton"},
                           {"person1": "Pauline Boutler", "person2": "Cathy Van"},
                           {"person1": "Peter Burton", "person2": "Cathy Van"},
                           {"person1": "Peter Burton", "person2": "Daniel Yang"}]

        s_cypher = """
        MATCH (n:Person {name: "Cathy Van"})
        BETWEEN interval(n.name@T.from, n@T.to)
        RETURN n.name as person_name
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"person_name": "Cathy Van"}]

    # 测试SNAPSHOT
    def test_snapshot(self):
        # 设置SNAPSHOT时间点
        s_cypher = """
        SNAPSHOT datetime('1938')
        """
        cypher_query = STransformer.transform(s_cypher)
        self.graphdb_connector.driver.execute_query(cypher_query)
        # SNAPSHOT在图匹配和获取属性值时均生效
        s_cypher = """
        MATCH (n:Person)
        RETURN n.name as person
        ORDER BY person
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.clear()
        assert records == [{"person": "Mary Smith"}]

        s_cypher = """
        MATCH (n:Person)
        RETURN n.name as person
        ORDER BY person
        LIMIT 3
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"person": ["Mary Smith", "Mary Smith Taylor"]}, {"person": "Cathy Van"},
                           {"person": "Daniel Yang"}]

    # 测试SCOPE
    def test_scope(self):
        # 设置SCOPE时间区间
        s_cypher = """
        SCOPE interval('1940', "1960")
        """
        cypher_query = STransformer.transform(s_cypher)
        self.graphdb_connector.driver.execute_query(cypher_query)
        # SCOPE在图匹配和获取属性值时均生效
        s_cypher = """
        MATCH (n:Person)
        RETURN n.name as person
        ORDER BY person
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.clear()
        assert records == [{"person": ["Mary Smith", "Mary Smith Taylor"]}, {"person": "Cathy Van"},
                           {"person": "Peter Burton"}]

        s_cypher = """
        MATCH (n:Person)
        RETURN n.name as person
        ORDER BY person
        LIMIT 3
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"person": ["Mary Smith", "Mary Smith Taylor"]}, {"person": "Cathy Van"},
                           {"person": "Daniel Yang"}]

    # 测试同时声明的优先级 AT TIME = BETWEEN > SCOPE > SNAPSHOT
    def test_priority(self):
        # 匹配时AT_TIME t > SNAPSHOT t，取值时#T(t) > SNAPSHOT t
        s_cypher = """
        SNAPSHOT datetime('2023')
        """
        cypher_query = STransformer.transform(s_cypher)
        self.graphdb_connector.driver.execute_query(cypher_query)
        s_cypher = """
        MATCH (n:Person)
        AT TIME datetime("1960")
        RETURN n.name#T("1950") as person
        ORDER BY person
        LIMIT 3
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.clear()
        assert records == [{"person": "Mary Smith"}, {"person": None}, {"person": None}]

        # 优先级：BETWEEN > SCOPE，取值时#T(t1, t2) > SCOPE
        s_cypher = """
        SCOPE interval('1937','1959')
        """
        cypher_query = STransformer.transform(s_cypher)
        self.graphdb_connector.driver.execute_query(cypher_query)
        s_cypher = """
        MATCH (n:Person)
        BETWEEN interval('1960','1980')
        RETURN n.name#T('1950','1980') as person
        ORDER BY person
        LIMIT 3
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.clear()
        assert records == [{"person": ["Mary Smith", "Mary Smith Taylor"]}, {"person": "Cathy Van"},
                           {"person": "Pauline Boutler"}]

        # 在查询语句和delete语句中和取值时，SCOPE>SNAPSHOT
        s_cypher = """
        SNAPSHOT datetime('1959')
        """
        cypher_query = STransformer.transform(s_cypher)
        self.graphdb_connector.driver.execute_query(cypher_query)
        s_cypher = """
        SCOPE interval('1937','1960')
        """
        cypher_query = STransformer.transform(s_cypher)
        self.graphdb_connector.driver.execute_query(cypher_query)
        s_cypher = """
        MATCH (n:Person)
        RETURN n.name as person
        ORDER BY person
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.clear()
        assert records == [{"person": ['Mary Smith', 'Mary Smith Taylor']}, {"person": "Cathy Van"},
                           {"person": "Peter Burton"}]

        s_cypher = """
        MATCH (n {name: "Mary Smith Taylor"})
        DELETE n.name#Value
        RETURN n.name as name
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.dataset1.rebuild()
        assert records == [{"name": None}]

        # 在更新语句（除delete语句）中SCOPE不生效
        s_cypher = """
        SNAPSHOT datetime('1959')
        """
        cypher_query = STransformer.transform(s_cypher)
        self.graphdb_connector.driver.execute_query(cypher_query)
        s_cypher = """
        SCOPE interval('1937','1959')
        """
        cypher_query = STransformer.transform(s_cypher)
        self.graphdb_connector.driver.execute_query(cypher_query)
        s_cypher = """
        CREATE (n:Person{name:"Nick"})
        RETURN n@T as effective_time
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        self.clear()
        self.dataset1.rebuild()
        assert records == [{
            "effective_time": {"from": DateTime(1959, 1, 1, tzinfo=timezone.utc),
                               "to": DateTime(9999, 12, 31, 23, 59, 59, 999999999, tzinfo=timezone.utc)}}]
