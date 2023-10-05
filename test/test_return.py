from unittest import TestCase

from transformer.main import transform_to_cypher


class TestReturn(TestCase):
    def test_return_1(self):
        s_cypher = 'MATCH (n1:Person)-[e:FRIEND]->(n2:Person)' \
                   '\nRETURN e.name'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_return_1:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')
