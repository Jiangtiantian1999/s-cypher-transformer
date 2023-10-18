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

    def test_create_5(self):
        s_cypher = 'CREATE (n:City {name: "London"})' \
                   '\nAT_TIME date("1688")'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_create_5:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')

    def test_create_6(self):
        s_cypher = 'CREATE (n:City {name: "London"})'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_create_6:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')

    def test_create_7(self):
        s_cypher = 'CREATE (n:City@T("1688", NOW) {name@T("1643", NOW): "London"@T("1690", NOW)})'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_create_7:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')

    def test_create_8(self):
        s_cypher = 'CREATE (n:City {name@T("16ss", NOW): "London"@T("1690", NOW)})' \
                   '\nAT_TIME date("1688")'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_create_8:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')

    def test_create_9(self):
        s_cypher = 'CREATE (n:City {name@T("1690", NOW): "London"@T("1611", "1632")})' \
                   '\nAT_TIME date("1688")'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_create_9:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')

    def test_create_10(self):
        s_cypher = 'CREATE (n:City {name@T("1690", NOW): "London"@T("1699", "1690")})' \
                   '\nAT_TIME date("1688")'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_create_10:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')

    def test_create_11(self):
        s_cypher = 'CREATE (n:City {name@T(datetime("2015-07-21T21:40:32.142+0100"), NOW): "London"@T(datetime("1690-07-21T21:40:32.142+0100", NOW)})' \
                   '\nAT_TIME datetime("1600-07-21T21:40:32.142+0100")'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_create_11:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')

    def test_create_12(self):
        s_cypher = 'MATCH (n1:Person), (n2:City)' \
                'WHERE n1.name = "Pauline Boutler" AND n2.name = "London"' \
                'CREATE (n1)-[e:LIVE_IN@T(datetime("20150721T21:40-01:30"), NOW)]->(n2)' \
                'AT_TIME date("2023")'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_create_12:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')

    def test_create_13(self):
        s_cypher = 'MATCH (n1:Person), (n2:City)' \
                'WHERE n1.name = "Pauline Boutler" AND n2.name = "London"' \
                'CREATE (n1)-[e:LIVE_IN@T(datetime("20150721T21:40-01:30"), NOW)]->(n2)' \
                'AT_TIME datetime("20110721T21:40-01:30")'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_create_13:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')

    def test_create_14(self):
        s_cypher = 'MATCH (n1:Person), (n2:City)' \
                'WHERE n1.name = "Pauline Boutler" AND n2.name = "London"' \
                'CREATE (n1)-[e:LIVE_IN@T(datetime("20150721T21:40-01:30"), datetime("20130721T21:40-01:30"))]->(n2)' \
                'AT_TIME datetime("20110721T21:40-01:30")'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_create_13:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')


    def test_create_15(self):
        s_cypher = 'CREATE (n:City {name@T("1690", NOW): "London"@T("1690", NOW), spot: "BigBen"})' \
                   '\nAT_TIME date("1688")'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_create_15:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')