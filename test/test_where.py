from unittest import TestCase

from transformer.main import transform_to_cypher


class TestWhere(TestCase):
    def test_where_1(self):
        s_cypher = 'MATCH (n1:Person)-[e:FRIEND]->(n2:Person)' \
                   '\nWHERE n1.name STARTS WITH "Mary" AND (e@T.to - e@T.from) >= duration({years: 20})' \
                   '\nRETURN e'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_where_1:", '\n', s_cypher, '\n', cypher_query, '\n')
