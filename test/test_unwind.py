from unittest import TestCase

from transformer.main import transform_to_cypher


class TestUnwind(TestCase):
    def test_unwind_1(self):
        s_cypher = 'UNWIND [1, 2, 3] AS x' \
                   '\nRETURN x'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_unwind_1:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')

    # def test_unwind_2(self):
    #     s_cypher = 'WITH [1, 1, 2, 2] AS coll' \
    #                '\nUNWIND coll AS x' \
    #                '\nWITH DISTINCT x' \
    #                '\nRETURN collect(x) AS SET'
    #     cypher_query = transform_to_cypher(s_cypher)
    #     print("test_unwind_2:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')
