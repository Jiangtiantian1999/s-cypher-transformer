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

    def test_match_5(self):
        s_cypher = 'MATCH (n1:Person)-[e:FRIEND]->(n2:Person)' \
                   'WHERE n1.name STARTS WITH "Mary"' \
                   'RETURN e'
        print("test_match_5:")
        print(s_cypher)
        cypher_query = transform_to_cypher(s_cypher)
        print(cypher_query, "\n")

    # def test_match_6(self):
    #     s_cypher = 'MATCH (n1:Person)-[e:FRIEND]->(n2:Person)' \
    #                'WHERE n1.name STARTS WITH "Mary" AND (e@T.to - e@T.from) >= duration({years: 20})' \
    #                'RETURN e'
    #     print("test_match_6:")
    #     print(s_cypher)
    #     cypher_query = transform_to_cypher(s_cypher)
    #     print(cypher_query, "\n")
