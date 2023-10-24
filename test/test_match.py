from textwrap import dedent
from unittest import TestCase

from transformer.main import transform_to_cypher


class TestMatch(TestCase):
    def test_match_1(self):
        s_cypher = dedent("""
        MATCH (n:City@T("1690", NOW) {name@T("1900", NOW): "London"@T("2000", NOW)})
        RETURN n
        """)
        cypher_query = transform_to_cypher(s_cypher)
        print("test_match_1:", s_cypher, '\n', cypher_query, '\n')

    def test_match_2(self):
        s_cypher = dedent("""
        MATCH (n1:Person)-[:LIVED@T("2000","2005")]->(n2:City {name: "Brussels"})
        RETURN n1
        """)
        cypher_query = transform_to_cypher(s_cypher)
        print("test_match_2:", s_cypher, '\n', cypher_query, '\n')

    def test_match_3(self):
        s_cypher = dedent("""
        MATCH path = cPath((n1:Person)-[:FRIEND*2]->(n2:Person))
        RETURN path
        """)
        cypher_query = transform_to_cypher(s_cypher)
        print("test_match_3:", s_cypher, '\n', cypher_query, '\n')

    def test_match_4(self):
        s_cypher = dedent("""
        MATCH path = pairCPath((n1:Person)-[:FRIEND*2..3]->(n2:Person))
        RETURN path
        """)
        cypher_query = transform_to_cypher(s_cypher)
        print("test_match_4:", s_cypher, '\n', cypher_query, '\n')

    def test_match_5(self):
        s_cypher = dedent("""
        MATCH path = earliestPath((n1:Station {name: "HangZhou East"})-[:route*]->(n2:Station {name: "XvZhou North"}))
        RETURN path
        """)
        cypher_query = transform_to_cypher(s_cypher)
        print("test_match_5:", s_cypher, '\n', cypher_query, '\n')

    def test_match_6(self):
        s_cypher = dedent("""
        MATCH path = latestPath((n1:Station {name: "HangZhou East"})-[:route*]->(n2:Station {name: "XvZhou North"}))
        RETURN path
        """)
        cypher_query = transform_to_cypher(s_cypher)
        print("test_match_6:", s_cypher, '\n', cypher_query, '\n')

    def test_match_7(self):
        s_cypher = dedent("""
        MATCH path = fastestPath((n1:Station {name: "HangZhou East"})-[:route*]->(n2:Station {name: "XiAn North"}))
        RETURN path
        """)
        cypher_query = transform_to_cypher(s_cypher)
        print("test_match_7:", s_cypher, '\n', cypher_query, '\n')

    def test_match_8(self):
        s_cypher = dedent("""
        MATCH path = shortestSPath((n1:Station {name: "HangZhou East"})-[:route*]->(n2:Station {name: "XiAn North"}))
        RETURN path
        """)
        cypher_query = transform_to_cypher(s_cypher)
        print("test_match_8:", s_cypher, '\n', cypher_query, '\n')

    def test_match_9(self):
        s_cypher = dedent("""
        MATCH (n:Person) BETWEEN interval("1940", NOW)
        WHERE n.name STARTS WITH "Mary"
        RETURN n.name
        """)
        cypher_query = transform_to_cypher(s_cypher)
        print("test_match_9:", s_cypher, '\n', cypher_query, '\n')

    def test_match_10(self):
        s_cypher = dedent("""
        MATCH (n:Person) AT_TIME date("1950")
        WHERE n.name STARTS WITH "Mary"
        RETURN n.name
        """)
        cypher_query = transform_to_cypher(s_cypher)
        print("test_match_10:", s_cypher, '\n', cypher_query, '\n')

    def test_match_11(self):
        s_cypher = dedent("""
        MATCH (n:Person) AT_TIME date("2015202T21+18:00")
        WHERE n.name STARTS WITH "Mary"
        RETURN n.name
        """)
        cypher_query = transform_to_cypher(s_cypher)
        print("test_match_11:", s_cypher, '\n', cypher_query, '\n')

    def test_match_12(self):
        s_cypher = dedent("""
        MATCH (n:Person) 
        BETWEEN interval("1940", NOW) 
        RETURN n.name limit 10
        """)
        cypher_query = transform_to_cypher(s_cypher)
        print("test_match_12:", s_cypher, '\n', cypher_query, '\n')

    def test_match_13(self):
        s_cypher = dedent("""
        MATCH (n:Person @T("1690", NOW)) 
        BETWEEN interval("1940", NOW) 
        RETURN n.name
        """)
        cypher_query = transform_to_cypher(s_cypher)
        print("test_match_13:", s_cypher, '\n', cypher_query, '\n')

    def test_match_14(self):
        s_cypher = dedent("""
        MATCH (n:Person @T("1960", NOW)) 
        BETWEEN interval("1940", NOW)
        RETURN n.name
        """)
        cypher_query = transform_to_cypher(s_cypher)
        print("test_match_14:", s_cypher, '\n', cypher_query, '\n')

    def test_match_15(self):
        s_cypher = dedent("""
        MATCH (n:Person{name: 'Pauline Boutler'})
        WITH n AS person
        RETURN person.name@T;
        """)
        cypher_query = transform_to_cypher(s_cypher)
        print("test_match_15:", s_cypher, '\n', cypher_query, '\n')

    def test_match_16(self):
        s_cypher = dedent("""
        MATCH (n:Person{name: 'Pauline Boutler'})
        WITH n.name + '000' as name
        RETURN name;
        """)
        cypher_query = transform_to_cypher(s_cypher)
        print("test_match_16:", s_cypher, '\n', cypher_query, '\n')

    def test_match_17(self):
        s_cypher = dedent("""
        MATCH (n:Person{name: 'Pauline Boutler'})
        WITH n.name AS name
        RETURN name@T;
        """)
        cypher_query = transform_to_cypher(s_cypher)
        print("test_match_17:", s_cypher, '\n', cypher_query, '\n')

    def test_match_18(self):
        s_cypher = dedent("""
        SNAPSHOT date('1999')
        MATCH path = (a:Person)-[*1..5]->(b:Person)
        RETURN path;
        """)
        cypher_query = transform_to_cypher(s_cypher)
        print("test_match_18:", s_cypher, '\n', cypher_query, '\n')

    def test_match_19(self):
        s_cypher = dedent("""
        MATCH (a:Person)-[r:FRIENDS_WITH]->(b:Person)
        WHERE r@T.from < '2022-01-01'
        RETURN a, b;
        """)
        cypher_query = transform_to_cypher(s_cypher)
        print("test_match_19:", s_cypher, '\n', cypher_query, '\n')

    def test_match_20(self):
        s_cypher = dedent("""
        MATCH (n:City@T("1690", NOW) {name@T("1900", NOW): "London"@T("2000", NOW)}) -[r:route]->(m:City@T("1000", NOW) {name@T("1900", NOW): "Birmingham"@T("2200", NOW)})
        WHERE r@T.from < '2022-01-01'
        RETURN n;
        """)
        cypher_query = transform_to_cypher(s_cypher)
        print("test_match_20:", s_cypher, '\n', cypher_query, '\n')

    def test_match_21(self):
        s_cypher = dedent("""
        MATCH (n:City {name: "London"}) -[r:route]->(m:City@T("1000", NOW) {name@T("1900", NOW): "Birmingham"@T("2200", NOW)})
        WHERE r@T.from < '2022-01-01'
        RETURN n;
        """)
        cypher_query = transform_to_cypher(s_cypher)
        print("test_match_21:", s_cypher, '\n', cypher_query, '\n')