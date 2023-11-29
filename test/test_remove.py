from textwrap import dedent
from unittest import TestCase

from transformer.s_transformer import STransformer


class TestRemove(TestCase):
    def test_remove_1(self):
        s_cypher = dedent("""
        MATCH (:Person {name: "Pauline Boutler"})-[e:LIVE_IN]->(:City {name: "London"})
        REMOVE e.code
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_remove_1:", s_cypher, '\n', cypher_query, '\n')

    def test_remove_2(self):
        s_cypher = dedent("""
               MATCH (n1:Person {name: "Pauline Boutler"})-[e:LIVE_IN]->(n2:City {name: "London"})
               REMOVE e.code, n2.spot
               """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_remove_2:", s_cypher, '\n', cypher_query, '\n')

    def test_remove_3(self):
        s_cypher = dedent("""
                MATCH (n1:City)
                WHERE n1.spot is NULL
                REMOVE n1
                """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_remove_3:", s_cypher, '\n', cypher_query, '\n')

    def test_remove_4(self):
        s_cypher = dedent("""
               MATCH (n1:Person {name: "Pauline Boutler"})-[e:LIVE_IN]->(n2:City {name: "London"})
               WHERE n1@T.from >= date("2004") and n1.name STARTS WITH "Pauline"
               REMOVE e.code, n2.spot
               """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_remove_4:", s_cypher, '\n', cypher_query, '\n')

    def test_remove_5(self):
        s_cypher = dedent("""
               MATCH (p:Person)
               WHERE n1@T.from < date("1988")
               WITH p
               REMOVE p.name;
               """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_remove_5:", s_cypher, '\n', cypher_query, '\n')