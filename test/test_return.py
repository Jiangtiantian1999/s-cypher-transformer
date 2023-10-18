from textwrap import dedent
from unittest import TestCase

from transformer.main import transform_to_cypher


class TestReturn(TestCase):
    def test_return_1(self):
        s_cypher = """MATCH (n1:Person)-[e:FRIEND]->(n2:Person)
        RETURN n1.name, e.name
        """
        cypher_query = transform_to_cypher(s_cypher)
        print("test_return_1:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')

    def test_return_2(self):
        s_cypher = "RETURN datetime({epochSeconds: timestamp() / 1000, nanosecond: 23}) AS theDate;"
        cypher_query = transform_to_cypher(s_cypher)
        print("test_return_2:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')

    def test_return_3(self):
        # TODO: make sure that the object a have several properties
        s_cypher = """MATCH (a:Person)
        RETURN DISTINCT a.country;
        """
        cypher_query = transform_to_cypher(dedent(s_cypher))
        print("test_return_3:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')

    def test_return_4(self):
        # TODO: is the interval sortable?
        s_cypher = """MATCH (p:Person)
        RETURN p@T as n
        ORDER BY n DESC
        """
        cypher_query = transform_to_cypher(dedent(s_cypher))
        print("test_return_4:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')

    def test_return_5(self):
        # TODO: test collect
        s_cypher = """MATCH (a:Person)-[:FRIENDS_WITH]->(b)
        RETURN a.name, collect(b.name) AS Friends;
        """
        cypher_query = transform_to_cypher(dedent(s_cypher))
        print("test_return_5:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')

    def test_return_6(self):
        # TODO: test aggregate functions
        s_cypher = """MATCH (p:Person)
        RETURN avg(p.age) AS AverageAge, max(p.age) AS Oldest, min(p.age) AS Youngest;
        """
        cypher_query = transform_to_cypher(dedent(s_cypher))
        print("test_return_6:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')

    def test_return_7(self):
        # TODO: test aggregate functions for interval
        s_cypher = """MATCH (p:Person)
        RETURN avg(p@T.from) AS AverageBirth, min(p@T.from) AS Oldest;
        """
        cypher_query = transform_to_cypher(dedent(s_cypher))
        print("test_return_7:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')

    def test_return_7(self):
        # TODO: test aggregate functions for 'Now' with other timestamp
        s_cypher = """MATCH (p:Person)
        RETURN max(p@T.to) AS Oldest;
        """
        cypher_query = transform_to_cypher(dedent(s_cypher))
        print("test_return_7:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')

    def test_return_8(self):
        # TODO: test calculation for interval
        s_cypher = """MATCH (p:Person)-[:FRIENDS_WITH]->(b:Person)
        WHERE p.name STARTS WITH "Mary"
        RETURN p,b, p@T.from-b@T.from AS AgeDiff;
        """
        cypher_query = transform_to_cypher(dedent(s_cypher))
        print("test_return_8:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')