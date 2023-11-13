from textwrap import dedent
from unittest import TestCase

from transformer.main import transform_to_cypher


class TestTimeWindow(TestCase):
    def test_at_time_1(self):
        s_cypher = dedent("""
        MATCH (n:Person)
        AT TIME date("1950")
        WHERE n.name STARTS WITH "Mary"
        RETURN n.name
        """)
        cypher_query = transform_to_cypher(s_cypher)
        print("test_at_time_1:", s_cypher, '\n', cypher_query, '\n')

    def test_between_1(self):
        s_cypher = dedent("""
        MATCH (n:Person)
        BETWEEN interval("1940", NOW)
        WHERE n.name STARTS WITH "Mary"
        RETURN n.name
        """)
        cypher_query = transform_to_cypher(s_cypher)
        print("test_between_1:", s_cypher, '\n', cypher_query, '\n')

# TODO: SNAPSHOT SCOPE
