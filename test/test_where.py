from textwrap import dedent
from unittest import TestCase

from transformer.main import transform_to_cypher


class TestWhere(TestCase):
    def test_where_1(self):
        s_cypher = dedent("""
        MATCH (n1:Person)-[e:FRIEND]->(n2:Person)
        WHERE n1.name STARTS WITH "Mary" AND (e@T.to - e@T.from) >= duration({years: 20})
        RETURN e
        """)
        cypher_query = transform_to_cypher(s_cypher)
        print("test_where_1:", s_cypher, '\n', cypher_query, '\n')


    def test_where_2(self):
        s_cypher = dedent("""
        MATCH (n1:Person)-[e:FRIEND]->(n2:Person)
        WHERE n1@T DURING interval.intersection([[date("2000"), date("2005")], [date("2003"), date("2015")]])
        RETURN e
        """)
        cypher_query = transform_to_cypher(s_cypher)
        print("test_where_2:", s_cypher, '\n', cypher_query, '\n')

    def test_where_3(self):
        s_cypher = dedent("""
        MATCH (n1:Person)-[e:FRIEND]->(n2:Person)
        WHERE n1@T DURING interval.range([[date("2000"), date("2005")], [date("2003"), date("2015")]])
        RETURN e
        """)
        cypher_query = transform_to_cypher(s_cypher)
        print("test_where_3:", s_cypher, '\n', cypher_query, '\n')

    def test_where_4(self):
        s_cypher = dedent("""
        MATCH (n1:Person)-[e:FRIEND]->(n2:Person)
        WHERE n1@T DURING interval.elapsed_time([[date("2000"), date("2005")], [date("2010"), date("2015")]])
        RETURN e
        """)
        cypher_query = transform_to_cypher(s_cypher)
        print("test_where_4:", s_cypher, '\n', cypher_query, '\n')

    def test_where_5(self):
        s_cypher = dedent("""
        MATCH (n1:Person)-[e:FRIEND]->(n2:Person)
        WHERE n1@T OVERLAPS interval.range([[date("2000"), date("2005")], [date("2010"), date("2015")]])
        RETURN e
        """)
        cypher_query = transform_to_cypher(s_cypher)
        print("test_where_5:", s_cypher, '\n', cypher_query, '\n')

    def test_where_6(self):
        s_cypher = dedent("""
        MATCH (n1:Person)-[e:FRIEND]->(n2:Person)
        WHERE n1@T OVERLAPS interval.range([[date("2000"), date("2005")], [date("2010"), date("2015")]])
        RETURN e
        """)
        cypher_query = transform_to_cypher(s_cypher)
        print("test_where_6:", s_cypher, '\n', cypher_query, '\n')

# duration.between(date("2000"), date("2005")) >= duration({years: 20})
# duration.inMonths(duration.between(date("2000"), date("2005"))) >= 20
# duration.inDays(duration.between(date("2000"), date("2005"))) >= 20
# duration.inSeconds(duration.between(date("2000"), date("2005"))) >= 20


## where 中可以套很多各种时间类型的函数判断
## and or not等逻辑判断