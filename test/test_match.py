from unittest import TestCase

from transformer.main import transform_to_cypher


class TestMatch(TestCase):
    def test_match_1(self):
        s_cypher = 'MATCH (n:City@T("1690", NOW) {name@T("1900", NOW): "London"@T("2000", NOW)})' \
                   '\nRETURN n'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_match_1:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')

    def test_match_2(self):
        s_cypher = 'MATCH (n1:Person)-[:LIVED@T("2000","2005")]->(n2:City {name: "Brussels"})' \
                   '\nRETURN n1'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_match_2:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')

    def test_match_3(self):
        s_cypher = 'MATCH path = cPath((n1:Person)-[:FRIEND*2]->(n2:Person))' \
                   '\nRETURN path'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_match_3:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')

    def test_match_4(self):
        s_cypher = 'MATCH path = pairCPath((n1:Person)-[:FRIEND*2..3]->(n2:Person))' \
                   '\nRETURN path'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_match_4:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')

    def test_match_5(self):
        s_cypher = 'MATCH path = earliestPath((n1:Station {name: "HangZhou East"})-[:route*]->(n2:Station {name: "XvZhou North"}))' \
                   '\nRETURN path'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_match_5:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')

    def test_match_6(self):
        s_cypher = 'MATCH path = latestPath((n1:Station {name: "HangZhou East"})-[:route*]->(n2:Station {name: "XvZhou North"}))' \
                   'RETURN path'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_match_6:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')

    def test_match_7(self):
        s_cypher = 'MATCH path = fastestPath((n1:Station {name: "HangZhou East"})-[:route*]->(n2:Station {name: "XiAn North"}))' \
                   '\nRETURN path'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_match_7:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')

    def test_match_8(self):
        s_cypher = 'MATCH path = shortestSPath((n1:Station {name: "HangZhou East"})-[:route*]->(n2:Station {name: "XiAn North"}))' \
                   '\nRETURN path'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_match_8:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')
