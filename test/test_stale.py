from unittest import TestCase

from transformer.main import transform_to_cypher


class TestStale(TestCase):
    def test_stale_1(self):
        s_cypher = 'MATCH (n {name: "Pauline Boutler"})' \
                   '\nSTALE n' \
                   '\nAT_TIME date("2023")'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_stale_1:", '\n', s_cypher, '\n', cypher_query, '\n')

    def test_stale_2(self):
        s_cypher = 'MATCH (:Person {name: "Pauline Boutler"})-[e:LIVE_IN]->(:City {name: "London"})' \
                   '\nSTALE e'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_stale_2:", '\n', s_cypher, '\n', cypher_query, '\n')

    def test_stale_3(self):
        s_cypher = 'MATCH (n {name: "Pauline Boutler"})' \
                   '\nSTALE n.name' \
                   '\nAT_TIME date("2023")'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_stale_3:", '\n', s_cypher, '\n', cypher_query, '\n')

    def test_stale_4(self):
        s_cypher = 'MATCH (n {name: "Pauline Boutler"})' \
                   '\nSTALE n.name#Value' \
                   '\nAT_TIME date("2023")'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_stale_4:", '\n', s_cypher, '\n', cypher_query, '\n')
