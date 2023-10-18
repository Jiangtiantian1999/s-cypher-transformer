from textwrap import dedent
from unittest import TestCase

from transformer.main import transform_to_cypher


class TestStale(TestCase):
    def test_stale_1(self):
        s_cypher = dedent("""
        MATCH (n {name: "Pauline Boutler"})
        STALE n
        AT_TIME date("2023")
        """)
        cypher_query = transform_to_cypher(s_cypher)
        print("test_stale_1:", s_cypher, '\n', cypher_query, '\n')

    def test_stale_2(self):
        s_cypher = dedent("""
        MATCH (:Person {name: "Pauline Boutler"})-[e:LIVE_IN]->(:City {name: "London"})
        STALE e
        """)
        cypher_query = transform_to_cypher(s_cypher)
        print("test_stale_2:", s_cypher, '\n', cypher_query, '\n')

    def test_stale_3(self):
        s_cypher = dedent("""
        MATCH (n {name: "Pauline Boutler"})
        STALE n.name
        AT_TIME date("2023")
        """)
        cypher_query = transform_to_cypher(s_cypher)
        print("test_stale_3:", s_cypher, '\n', cypher_query, '\n')

    def test_stale_4(self):
        s_cypher = dedent("""
        MATCH (n {name: "Pauline Boutler"})
        STALE n.name#Value
        AT_TIME date("2023")
        """)
        cypher_query = transform_to_cypher(s_cypher)
        print("test_stale_4:", s_cypher, '\n', cypher_query, '\n')
