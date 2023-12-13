from unittest import TestCase

from test.graphdb_connector import GraphDBConnector
from transformer.s_transformer import STransformer


class TestWhere(TestCase):
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

    # 测试逻辑操作
    def test_where_logic_operation(self):
        s_cypher = """
        MATCH (n:Person)-[r:LIVE@T("2000", "2010")]->(m:City)
        WHERE n.name#T(NOW) = "Mary Smith Taylor" XOR (m.name = "Paris" and n.name = "Cathy Van") OR NOT(n.name#T(NOW) = "Mary Smith Taylor" or n.name = "Cathy Van")
        RETURN n.name as person, m.name as city
        ORDER BY person, city
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"person": ["Mary Smith", "Mary Smith Taylor"], "city": "Antwerp"},
                           {"person": "Daniel Yang", "city": "Antwerp"},
                           {"person": "Peter Burton", "city": "New York"},
                           {"person": "Sandra Carter", "city": "New York"}]

    # 测试比较操作
    def test_compare_operation(self):
        s_cypher = """
        MATCH (n:Person)-[r:LIVE]->(m:City {name: "Antwerp"})
        WHERE r@T.from < timePoint('1990')
        RETURN n
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert len(records) == 0

        s_cypher = """
        MATCH (n:Person)-[r:LIVE]->(m:City {name: "Antwerp"})
        WHERE r@T.from <= timePoint('1990')
        RETURN n.name#T(NOW) as person
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"person": "Mary Smith Taylor"}]

        s_cypher = """
        MATCH (a:Person)-[r:FRIEND]->(b:Person)
        WHERE r@T.from > timePoint('2002')
        RETURN a.name#T(NOW) as person1, b.name#T(NOW) as person2
        ORDER BY person1, person2
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"person1": "Mary Smith Taylor", "person2": "Pauline Boutler"},
                           {"person1": "Peter Burton", "person2": "Daniel Yang"}]

        s_cypher = """
        MATCH (a:Person)-[r:FRIEND]->(b:Person)
        WHERE r@T.from >= timePoint('2002')
        RETURN a.name#T(NOW) as person1, b.name#T(NOW) as person2
        ORDER BY person1, person2
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summary, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"person1": "Mary Smith Taylor", "person2": "Pauline Boutler"},
                           {"person1": "Pauline Boutler", "person2": "Cathy Van"},
                           {"person1": "Peter Burton", "person2": "Daniel Yang"}]

    # 测试算术运算
    def test_arithmetic_operation(self):
        # 加减
        s_cypher = """
        MATCH (n:Person)-[e:LIVE]->(m:City)
        WHERE ( e@T.from + Duration({years: 20}) >= e@T.to and e@T.to <> timePoint(NOW) ) or ( e@T.from >= timePoint("2023") - Duration({years: 20}) and e@T.to = timePoint(NOW) )
        RETURN n.name as person, m.name as city
        ORDER BY person, city
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"person": ["Mary Smith", "Mary Smith Taylor"], "city": "Brussels"},
                           {"person": "Cathy Van", "city": "Brussels"},
                           {"person": "Pauline Boutler", "city": "London"}]

        # 乘除余
        s_cypher = """
        MATCH (n:Person)-[e:LIVE]->(m:City)
        WHERE (duration.between(n@T.from, timePoint('2023')) * 5).months < (duration.between(m@T.from, timePoint('2023')) / 2).months and 10 % 3 = 1
        RETURN n.name as person, m.name as city
        ORDER BY person, city
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"person": "Daniel Yang", "city": "Antwerp"}]

        # 幂
        s_cypher = """
        MATCH (n:Person)
        WHERE duration.between(timePoint('2023'), n@T.from).months^2 > 1000000
        RETURN n.name as person
        ORDER BY person
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"person": ["Mary Smith", "Mary Smith Taylor"]}]

    # 测试字符串操作
    def test_string_operation(self):
        # STARTS WITH
        s_cypher = """
        MATCH (n:Person)
        UNWIND n.name as name
        WITH name
        WHERE name STARTS WITH "Mary"
        RETURN name
        ORDER BY name
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"name": "Mary Smith"}, {"name": "Mary Smith Taylor"}]

        # ENDS WITH
        s_cypher = """
        MATCH (n:Person)
        WHERE n.name#T(NOW) ENDS WITH 'er'
        RETURN n.name as name
        ORDER BY name
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"name": "Pauline Boutler"}, {"name": "Sandra Carter"}]

        # CONTAINS
        s_cypher = """
        MATCH (n:Person)
        WHERE n.name CONTAINS 'an'
        RETURN n.name as name
        ORDER BY name
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"name": "Cathy Van"}, {"name": "Daniel Yang"}, {"name": "Sandra Carter"}]

    # 测试列表操作
    def test_list_operation(self):
        s_cypher = """
        MATCH (n:Person)-[:LIVE]->(m:City)
        WHERE m.name IN ["London", "Brussels"]
        RETURN DISTINCT n.name as person
        ORDER BY person
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"person": ["Mary Smith", "Mary Smith Taylor"]}, {"person": "Cathy Van"},
                           {"person": "Pauline Boutler"}]

    # 测试NULL操作
    def test_null_operation(self):
        s_cypher = """
        UNWIND [{k:1,v:NULL},{k:2,v:"v"}] as t
        WITH t
        WHERE t.v is null
        RETURN t.k as result
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"result": 1}]

        s_cypher = """
        UNWIND [{k:1,v:NULL},{k:2,v:"v"}] as t
        WITH t
        WHERE t.v is not null
        RETURN t.k as result
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"result": 2}]

    # 测试标签
    def test_label_operation(self):
        s_cypher = """
        MATCH (n)
        WHERE n:Brand
        RETURN n.name as brand
        ORDER BY brand
        """
        cypher_query = STransformer.transform(s_cypher)
        records, summery, keys = self.graphdb_connector.driver.execute_query(cypher_query)
        assert records == [{"brand": "Lucky Goldstar"}, {"brand": "Samsung"}]
