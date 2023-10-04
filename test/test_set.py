from unittest import TestCase

from transformer.main import transform_to_cypher


class TestSet(TestCase):
    def test_set_1(self):
        s_cypher = 'MATCH (n {name: "Pauline Boutler"})' \
                   '\nSET n.gender@T("2000", NOW) = "Male"' \
                   '\nAT_TIME now()'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_set_1:", '\n', s_cypher, '\n', cypher_query, '\n')

    def test_set_2(self):
        s_cypher = 'MATCH (n {name: "Pauline Boutler"})' \
                   '\nSET n.gender@T("2000", NOW) = "Male"@T("2000", NOW)'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_set_2:", '\n', s_cypher, '\n', cypher_query, '\n')

    def test_set_3(self):
        s_cypher = 'MATCH (n {name: "Pauline Boutler"})' \
                   '\nSET n@T("1978", NOW).gender@T("2000", NOW) = "Male"@T("2000", NOW)'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_set_3:", '\n', s_cypher, '\n', cypher_query, '\n')

    def test_set_4(self):
        s_cypher = 'MATCH (:Person {name: "Pauline Boutler"})-[e:LIVE_IN]->(:City {name: "London"})' \
                   '\nSET e.code = "255389"'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_set_4:", '\n', s_cypher, '\n', cypher_query, '\n')

    def test_set_5(self):
        s_cypher = 'MATCH (:Person {name: "Pauline Boutler"})-[e:LIVE_IN]->(:City {name: "London"})' \
                   '\nSET e.code = "255389"' \
                   '\nAT_TIME date("2023")'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_set_5:", '\n', s_cypher, '\n', cypher_query, '\n')

    def test_set_6(self):
        s_cypher = 'MATCH (n {name: "Pauline Boutler"})' \
                   '\nSET n@T("1960", NOW)'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_set_6:", '\n', s_cypher, '\n', cypher_query, '\n')

    def test_set_7(self):
        s_cypher = 'MATCH (n{name: "Pauline Boutler"})' \
                   '\nSET n.name@T("1970", NOW)'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_set_7:", '\n', s_cypher, '\n', cypher_query, '\n')

    def test_set_8(self):
        s_cypher = 'MATCH (n {name: "Pauline Boutler"})' \
                   '\nSET n.name#Value@T("1978", "2023")'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_set_8:", '\n', s_cypher, '\n', cypher_query, '\n')

    def test_set_9(self):
        s_cypher = 'MATCH (n {name: "Pauline Boutler"})' \
                   '\nSET n@T("1960", NOW).name@T("1960", "2010")#Value@T("1960", "2000")'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_set_9:", '\n', s_cypher, '\n', cypher_query, '\n')

    def test_set_10(self):
        s_cypher = 'MATCH (:Person {name: "Pauline Boutler"})-[e:LIVE_IN]->(:City {name: "London"})' \
                   '\nSET e@T("2010", "2020")'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_set_10:", '\n', s_cypher, '\n', cypher_query, '\n')
