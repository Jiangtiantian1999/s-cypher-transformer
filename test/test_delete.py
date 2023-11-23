from textwrap import dedent
from unittest import TestCase

from transformer.s_transformer import STransformer


class TestDelete(TestCase):
    def test_delete_1(self):
        s_cypher = dedent("""
        MATCH (n {name: "Pauline Boutler"})
        DELETE n
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_delete_1:", s_cypher, '\n', cypher_query, '\n')

    def test_delete_2(self):
        s_cypher = dedent("""
        MATCH (n {name: "Pauline Boutler"})
        DELETE n.name
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_delete_2:", s_cypher, '\n', cypher_query, '\n')

    def test_delete_3(self):
        s_cypher = dedent("""
        MATCH (n {name: "Pauline Boutler"})
        DELETE n.name#Value
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_delete_3:", s_cypher, '\n', cypher_query, '\n')

    def test_delete_4(self):
        s_cypher = dedent("""
        MATCH (a:Person {name: "Pauline Boutler"})-[e:LIVE_IN]->(b:City {name: "London"})
        DELETE e
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_delete_4:", s_cypher, '\n', cypher_query, '\n')
