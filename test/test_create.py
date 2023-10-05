from unittest import TestCase

from transformer.main import transform_to_cypher


class TestCreate(TestCase):
    def test_create_1(self):
        s_cypher = 'CREATE (n:City {name@T("1690", NOW): "London"@T("1690", NOW)})' \
                   '\nAT_TIME date("1688")'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_create_1:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')

    def test_create_2(self):
        s_cypher = 'CREATE (n:City@T("1688", NOW) {name@T("1690", NOW): "London"@T("1690", NOW)})'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_create_2:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')

    def test_create_3(self):
        s_cypher = 'CREATE (n:City@T("1688", NOW) {name@T("1690", NOW): "London"})'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_create_3:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')

    def test_create_4(self):
        s_cypher = 'MATCH (n1:Person), (n2:City)' \
                   'WHERE n1.name = "Pauline Boutler" AND n2.name = "London"' \
                   'CREATE (n1)-[e:LIVE_IN@T("2004", NOW)]->(n2)' \
                   'AT_TIME date("2023")'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_create_4:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')
