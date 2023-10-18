from textwrap import dedent
from unittest import TestCase

from transformer.main import transform_to_cypher


class TestUnwind(TestCase):
    def test_unwind_1(self):
        s_cypher = dedent("""
        UNWIND [1, 2, 3] AS x
        RETURN x
        """)
        cypher_query = transform_to_cypher(s_cypher)
        print("test_unwind_1:", s_cypher, '\n', cypher_query, '\n')

    def test_unwind_2(self):
        s_cypher = dedent("""
        WITH [1, 1, 2, 2] AS coll
        UNWIND coll AS x
        WITH DISTINCT x
        RETURN collect(x) AS SET
        """)
        cypher_query = transform_to_cypher(s_cypher)
        print("test_unwind_2:", s_cypher, '\n', cypher_query, '\n')
