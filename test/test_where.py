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


## where 中可以套很多各种时间类型的函数判断
## and or not等逻辑判断