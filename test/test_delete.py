from unittest import TestCase

from transformer.main import transform_to_cypher


class TestDelete(TestCase):
    def test_delete_1(self):
        s_cypher = 'MATCH (n {name: "Pauline Boutler"})' \
                   '\nDELETE n'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_delete_1:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')

    def test_delete_2(self):
        s_cypher = 'MATCH (n {name: "Pauline Boutler"})' \
                   '\nDELETE n.name'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_delete_2:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')

    def test_delete_3(self):
        s_cypher = 'MATCH (n {name: "Pauline Boutler"})' \
                   'DELETE n.name#Value'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_delete_3:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')

    def test_delete_4(self):
        s_cypher = 'MATCH (a:Person {name: "Pauline Boutler"})-[e:LIVE_IN]->(b:City {name: "London"})' \
                   'DELETE e'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_delete_4:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')
