from unittest import TestCase

from transformer.main import transform_to_cypher


class TestTimeWindow(TestCase):
    def test_at_time_1(self):
        s_cypher = 'MATCH (n:Person)' \
                   '\nAT_TIME date("1950")' \
                   '\nWHERE n.name STARTS WITH "Mary"' \
                   '\nRETURN n.name'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_at_time_1:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')

    def test_between_1(self):
        s_cypher = 'MATCH (n:Person)' \
                   '\nBETWEEN interval("1940", NOW)' \
                   '\nWHERE n.name STARTS WITH "Mary"' \
                   '\nRETURN n.name'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_between_1:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')
