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

    # 测试字符串运算
    def test_where_1(self):
        s_cypher = """
        MATCH (n1:Person)-[e:FRIEND]->(n2:Person)
        WHERE n1.name STARTS WITH "Mary" AND (e@T.to - e@T.from) >= duration({years: 20})
        RETURN e
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

        s_cypher = """
        MATCH (n:City)
        AT_TIME date("2000")
        WHERE n.spot STARTS WITH "West"
        RETURN n.name;
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

        s_cypher = """
        MATCH (n1:Person)-[e:FRIEND]->(n2:Person {name: 'Cathy Van'})
        WHERE n1.name ENDS WITH 'Burton'
        RETURN n1;
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

        s_cypher = """
        MATCH (n1:Person)
        WHERE n1.name CONTAINS 'Mary Smith'
        RETURN n1;
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

        s_cypher = """
        MATCH (n1:Person)-[:LIVED@T("2001","2022")]->(n2:City)
        WHERE n2.name CONTAINS 'Paris' AND n1@T.from <= date('1960')
        RETURN n1;
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    # 测试用有效时间过滤数据
    def test_where_2(self):
        s_cypher = """
        MATCH (a:Person)-[r:FRIENDS_WITH]->(b:Person)
        WHERE r@T.from < '2022-01-01'
        RETURN a, b;
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

        s_cypher = """
        MATCH (n:City {name: "London"}) -[r:route]->(m:City@T("1000", NOW) {name@T("1900", NOW): "Birmingham"@T("2200", NOW)})
        WHERE r@T.from < '2022-01-01'
        RETURN n;
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

        s_cypher = """
        MATCH (n:City@T("1690", NOW) {name@T("1900", NOW): "London"@T("2000", NOW)})-[r:route]->(m:City@T("1000", NOW) {name@T("1900", NOW): "Birmingham"@T("2200", NOW)})
        WHERE r@T.from < '2022-01-01'
        RETURN n;
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

        s_cypher = """
        MATCH (n:Person{name@T("1937", NOW): "Mary Smith"@T("1937", "1959")}) -[r:LIVE_IN]->(m:City@T("1581", NOW) {name@T("1581", NOW): "Antwerp"@T("1581", NOW)})
        WHERE r@T.from > '1989-08-09'
        RETURN n;
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

        s_cypher = """
        MATCH (n:Person{name@T("1937", NOW): "Mary Smith"@T("1937", "1959")}) -[r:LIKE]->(m:Brand@T("1938", NOW) {name@T("1938", NOW): "Samsung"@T("1938", NOW)})
        WHERE r@T.from > '1890-08-09'
        RETURN m;
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

        s_cypher = """
        MATCH (n:Person@T("1937", NOW) {name@T("1937", NOW): "Mary Smith"@T("1937", "1959")}) -[r:LIVE_IN]->(m:City@T("1581", NOW) {name@T("1581", NOW): "Antwerp"@T("1581", NOW)})
        WHERE r@T.from > '1989-08-09'
        RETURN n;
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

        s_cypher = """
        MATCH (n1:Person)-[e:FRIEND]->(n2:Person {name: 'Cathy Van'})
        WHERE e@T.from >= date ('1990')
        RETURN n1;
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

        s_cypher = """
        MATCH (n1:Person {name: 'Pauline Boutler'})-[e:FRIEND]->(n2:Person)
        WHERE e@T.to >= date ('2000')
        RETURN n2;
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

        s_cypher = """
        MATCH (n:City {name: "London"}) -[r:route]->(m:City@T("1000", NOW) {name@T("1900", NOW): "Birmingham"@T("2200", NOW)})
        WHERE r@T.from < '2022-01-01'
        RETURN n;
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    # 测试时间区间的运算符
    def test_where_3(self):
        s_cypher = """
        MATCH (n1:Person)-[e:FRIEND]->(n2:Person)
        WHERE n1@T DURING interval.intersection([[date("2000"), date("2005")], [date("2003"), date("2015")]])
        RETURN e
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

        s_cypher = """
        MATCH (n1:Person)-[e:FRIEND]->(n2:Person)
        WHERE n1@T DURING interval.range([[date("2000"), date("2005")], [date("2003"), date("2015")]])
        RETURN e
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

        s_cypher = """
        MATCH (n1:Person)-[e:FRIEND]->(n2:Person)
        WHERE n1@T DURING interval.elapsed_time([[date("2000"), date("2005")], [date("2010"), date("2015")]])
        RETURN e
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

    def test_where_4(self):
        s_cypher = """
        MATCH (n1:Person)-[e:FRIEND]->(n2:Person)
        WHERE n1@T OVERLAPS interval.range([[date("2000"), date("2005")], [date("2010"), date("2015")]])
        RETURN e
        """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

        s_cypher = """
                MATCH (n1:Person)-[e:FRIEND]->(n2:Person)
                WHERE n1@T OVERLAPS interval.range([[date("2000"), date("2005")], [date("2010"), date("2015")]])
                RETURN e
                """
        cypher_query = STransformer.transform(s_cypher)
        tx = self.graphdb_connector.driver.session().begin_transaction()
        results = tx.run(cypher_query).data()

# duration.between(date("2000"), date("2005")) >= duration({years: 20})
# duration.inMonths(duration.between(date("2000"), date("2005"))) >= 20
# duration.inDays(duration.between(date("2000"), date("2005"))) >= 20
# duration.inSeconds(duration.between(date("2000"), date("2005"))) >= 20

# def test_where_2(self):
#     s_cypher = 'MATCH (n1:Person)-[e:FRIEND]->(n2:Person)' \
#                '\nWHERE n1.name STARTS WITH "Mary"' \
#                '\nRETURN e'
#     cypher_query = transform_to_cypher(s_cypher)
#     print("test_where_2:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')
#
# def test_where_3(self):
#     s_cypher = 'MATCH (n1:Person)' \
#                '\nWHERE (e@T.to - e@T.from) >= duration({years: 20})' \
#                '\nRETURN e'
#     cypher_query = transform_to_cypher(s_cypher)
#     print("test_where_3:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')


## where 中可以套很多各种时间类型的函数判断
## and or not等逻辑判断
