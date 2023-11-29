from textwrap import dedent
from unittest import TestCase

from transformer.s_transformer import STransformer


class TestTimeWindow(TestCase):
    def test_at_time_1(self):
        s_cypher = dedent("""
        MATCH (n:Person)
        AT TIME date("1950")
        WHERE n.name STARTS WITH "Mary"
        RETURN n.name
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_at_time_1:", s_cypher, '\n', cypher_query, '\n')

    def test_between_1(self):
        s_cypher = dedent("""
        MATCH (n:Person)
        BETWEEN interval("1940", NOW)
        WHERE n.name STARTS WITH "Mary"
        RETURN n.name
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_between_1:", s_cypher, '\n', cypher_query, '\n')

    def test_between_2(self):
        s_cypher = dedent("""
        MATCH (n:Brand)
        BETWEEN interval("1958", NOW)
        WHERE n.name CONTAINS "Lucky"
        RETURN n;
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_between_2:", s_cypher, '\n', cypher_query, '\n')

    def test_snapshot_1(self):
        s_cypher = dedent("""
        SNAPSHOT date('1999')
        MATCH (n:City)
        AT_TIME date("2000")
        WHERE n.spot STARTS WITH "West"
        RETURN n.name;
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_snapshot_1:", s_cypher, '\n', cypher_query, '\n')

    def test_snapshot_2(self):
        s_cypher = dedent("""
        SNAPSHOT date('2023')
        MATCH path = (a:Person)-[*1..5]->(b:Brand)
        WHERE a.name ENDS WITH 'Van'
        RETURN path;
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_snapshot_2:", s_cypher, '\n', cypher_query, '\n')

    # TODO: SCOPE
