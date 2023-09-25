from unittest import TestCase, TestSuite, TextTestRunner

from transformer.main import transform_to_cypher


class TestMatch(TestCase):
    def test_match_1(self):
        s_cypher = 'MATCH (n:City@T("1690", NOW) {name@T("1900", NOW): "London"@T("2000", NOW)})' \
                   '\nRETURN n'
        print("test_match_1:")
        print(s_cypher)
        cypher_query = transform_to_cypher(s_cypher)
        print(cypher_query, "\n")

    def test_match_2(self):
        s_cypher = 'MATCH (n:City@T("1690", NOW) )' \
                   '\nRETURN n'
        print("test_match_2:")
        print(s_cypher)
        cypher_query = transform_to_cypher(s_cypher)
        print(cypher_query, "\n")

    def test_match_3(self):
        s_cypher = 'MATCH (n:City)' \
                   '\nRETURN n'
        print("test_match_3:")
        print(s_cypher)
        cypher_query = transform_to_cypher(s_cypher)
        print(cypher_query, "\n")

    def test_match_4(self):
        s_cypher = 'MATCH (n:City)-->(m:City)' \
                   '\nRETURN n, m'
        print("test_match_4:")
        print(s_cypher)
        cypher_query = transform_to_cypher(s_cypher)
        print(cypher_query, "\n")

