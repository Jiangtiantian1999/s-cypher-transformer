from unittest import TestCase

from transformer.main import transform_to_cypher


class TestRemove(TestCase):
    def test_remove_1(self):
        s_cypher = """MATCH (:Person {name: "Pauline Boutler"})-[e:LIVE_IN]->(:City {name: "London"})
        REMOVE e.code"""
        cypher_query = transform_to_cypher(s_cypher)
        print("test_remove_1:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')

    def test_remove_2(self):
        # TODO: remove multiple properties
        pass

    def test_remove_3(self):
        # TODO: remove not exist property
        pass