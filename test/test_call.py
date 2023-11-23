from textwrap import dedent
from unittest import TestCase

from transformer.s_transformer import STransformer


class TestCall(TestCase):


    def test_call_1(self):
        s_cypher = dedent("""
        CALL db.labels
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_call_1:", s_cypher, '\n', cypher_query, '\n')

    def test_call_2(self):
        s_cypher = dedent("""
        CALL dbms.info()
        YIELD id, name, createDate
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_call_2:", s_cypher, '\n', cypher_query, '\n')

    def test_call_3(self):
        s_cypher = dedent("""
        CALL org.opencypher.procedure.example.addNodeToIndex("users", 0, "name")
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_call_3:", s_cypher, '\n', cypher_query, '\n')

    def test_call_4(self):
        s_cypher = dedent("""
        MATCH (n1:Person {name: "Nick"})-[:FRIEND*2]->(n2:Person)
        RETURN max(n1.ege, n2.ege) as max_edge
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_call_4:", s_cypher, '\n', cypher_query, '\n')
