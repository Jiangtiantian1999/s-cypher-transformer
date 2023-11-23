from textwrap import dedent
from unittest import TestCase

from transformer.s_transformer import STransformer


class TestStale(TestCase):
    def test_stale_1(self):
        s_cypher = dedent("""
        MATCH (n {name: "Pauline Boutler"})
        STALE n
        AT TIME date("2023")
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_stale_1:", s_cypher, '\n', cypher_query, '\n')

    def test_stale_2(self):
        s_cypher = dedent("""
        MATCH (:Person {name: "Pauline Boutler"})-[e:LIVE_IN]->(:City {name: "London"})
        STALE e
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_stale_2:", s_cypher, '\n', cypher_query, '\n')

    def test_stale_3(self):
        s_cypher = dedent("""
        MATCH (n {name: "Pauline Boutler"})
        STALE n.name
        AT TIME date("2023")
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_stale_3:", s_cypher, '\n', cypher_query, '\n')

    def test_stale_4(self):
        s_cypher = dedent("""
        MATCH (n {name: "Pauline Boutler"})
        STALE n.name#Value
        AT TIME date("2023")
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_stale_4:", s_cypher, '\n', cypher_query, '\n')

    def test_stale_5(self):
        # test if @T.to is not NOW
        s_cypher = dedent("""
        MATCH (n:City@T("1690", "1999") {name@T("1900", "1999"): "London"@T("1900", "1999")})
        STALE n
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_stale_5:", s_cypher, '\n', cypher_query, '\n')
