from unittest import TestCase

from transformer.main import transform_to_cypher


class TestRemove(TestCase):
    def test_remove_1(self):
        s_cypher = 'MATCH (:Person {name: "Pauline Boutler"})-[e:LIVE_IN]->(:City {name: "London"})' \
                   '\nREMOVE e.code'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_remove_1:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')
