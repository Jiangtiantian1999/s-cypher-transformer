from textwrap import dedent
from unittest import TestCase

from transformer.main import transform_to_cypher


class TestCreate(TestCase):
    def test_create_1(self):
        s_cypher = dedent("""
        CREATE (n:City {name@T("1690", NOW): "London"@T("1690", NOW)})
        AT_TIME date("1688")
        """)
        cypher_query = transform_to_cypher(s_cypher)
        print("test_create_1:", s_cypher, '\n', cypher_query, '\n')

    def test_create_2(self):
        s_cypher = dedent("""
        CREATE (n:City@T("1688", NOW) {name@T("1690", NOW): "London"@T("1690", NOW)})
        """)
        cypher_query = transform_to_cypher(s_cypher)
        print("test_create_2:", s_cypher, '\n', cypher_query, '\n')

    def test_create_3(self):
        s_cypher = dedent("""
        CREATE (n:City@T("1688", NOW) {name@T("1690", NOW): "London"})
        """)
        cypher_query = transform_to_cypher(s_cypher)
        print("test_create_3:", s_cypher, '\n', cypher_query, '\n')

    def test_create_4(self):
        s_cypher = dedent("""
        MATCH (n1:Person), (n2:City)
        WHERE n1.name = "Pauline Boutler" AND n2.name = "London"
        CREATE (n1)-[e:LIVE_IN@T("2004", NOW)]->(n2)
        AT TIME date("2023")
        """)
        cypher_query = transform_to_cypher(s_cypher)
        print("test_create_4:", s_cypher, '\n', cypher_query, '\n')

    def test_create_5(self):
        s_cypher = dedent("""
        CREATE (n:City {name: "London"})
        AT TIME date("1688")
        """)
        cypher_query = transform_to_cypher(s_cypher)
        print("test_create_5:", s_cypher, '\n', cypher_query, '\n')

    def test_create_6(self):
        s_cypher = dedent("""
        CREATE (n:City {name: "London"})
        """)
        cypher_query = transform_to_cypher(s_cypher)
        print("test_create_6:", s_cypher, '\n', cypher_query, '\n')

    def test_create_7(self):
        s_cypher = dedent("""
        CREATE (n:City@T("1688", NOW) {name@T("1643", NOW): "London"@T("1690", NOW)})
        """)
        cypher_query = transform_to_cypher(s_cypher)
        print("test_create_7:", s_cypher, '\n', cypher_query, '\n')

    def test_create_8(self):
        s_cypher = dedent("""
        CREATE (n:City {name@T("16ss", NOW): "London"@T("1690", NOW)})
        AT TIME date("1688")
        """)
        cypher_query = transform_to_cypher(s_cypher)
        print("test_create_8:", s_cypher, '\n', cypher_query, '\n')

    def test_create_9(self):
        s_cypher = dedent("""
        CREATE (n:City {name@T("1690", NOW): "London"@T("1611", "1632")})
        AT TIME date("1688")
        """)
        cypher_query = transform_to_cypher(s_cypher)
        print("test_create_9:", s_cypher, '\n', cypher_query, '\n')

    def test_create_10(self):
        s_cypher = dedent("""
        CREATE (n:City {name@T("1690", NOW): "London"@T("1699", "1690")})
        AT TIME date("1688")
        """)
        cypher_query = transform_to_cypher(s_cypher)
        print("test_create_10:", s_cypher, '\n', cypher_query, '\n')

    def test_create_11(self):
        s_cypher = dedent("""
        CREATE (n:City {name@T(datetime("2015-07-21T21:40:32.142+0100"), NOW): "London"@T(datetime("1690-07-21T21:40:32.142+0100", NOW)})
        AT TIME datetime("1600-07-21T21:40:32.142+0100")
        """)
        cypher_query = transform_to_cypher(s_cypher)
        print("test_create_11:", s_cypher, '\n', cypher_query, '\n')

    def test_create_12(self):
        s_cypher = dedent("""
        MATCH (n1:Person), (n2:City)
        WHERE n1.name = "Pauline Boutler" AND n2.name = "London"
        CREATE (n1)-[e:LIVE_IN@T(datetime("20150721T21:40-01:30"), NOW)]->(n2)
        AT TIME date("2023")
        """)
        cypher_query = transform_to_cypher(s_cypher)
        print("test_create_12:", s_cypher, '\n', cypher_query, '\n')

    def test_create_13(self):
        s_cypher = dedent("""
        MATCH (n1:Person), (n2:City)
        WHERE n1.name = "Pauline Boutler" AND n2.name = "London"
        CREATE (n1)-[e:LIVE_IN@T(datetime("20150721T21:40-01:30"), NOW)]->(n2)
        AT TIME datetime("20110721T21:40-01:30")
        """)
        cypher_query = transform_to_cypher(s_cypher)
        print("test_create_13:", s_cypher, '\n', cypher_query, '\n')

    def test_create_14(self):
        s_cypher = dedent("""
        MATCH (n1:Person), (n2:City)
        WHERE n1.name = "Pauline Boutler" AND n2.name = "London"
        CREATE (n1)-[e:LIVE_IN@T(datetime("20150721T21:40-01:30"), datetime("20130721T21:40-01:30"))]->(n2)
        AT TIME datetime("20110721T21:40-01:30")
        """)
        cypher_query = transform_to_cypher(s_cypher)
        print("test_create_13:", s_cypher, '\n', cypher_query, '\n')

    def test_create_15(self):
        s_cypher = dedent("""
        CREATE (n:City {name@T("1690", NOW): "London"@T("1690", NOW), spot: "BigBen"})
        AT TIME date("1688")
        """)
        cypher_query = transform_to_cypher(s_cypher)
        print("test_create_15:", s_cypher, '\n', cypher_query, '\n')
