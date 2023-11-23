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
        # TODO: remove multiple properties
        pass

    def test_remove_3(self):
        # TODO: remove not exist property
        pass
