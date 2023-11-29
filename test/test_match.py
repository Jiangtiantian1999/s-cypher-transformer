from textwrap import dedent
from unittest import TestCase

from neo4j import GraphDatabase
from sshtunnel import SSHTunnelForwarder

from transformer.s_transformer import STransformer


class TestMatch(TestCase):
    server = None
    driver = None
    session = None
    tx = None

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        TestMatch.server = SSHTunnelForwarder(("118.25.15.14", 1111), ssh_password="123456", ssh_username="jtt",
                                              remote_bind_address=("0.0.0.0", 7687))
        TestMatch.server.start()
        TestMatch.driver = GraphDatabase.driver("bolt://127.0.0.1:" + str(TestMatch.server.local_bind_port),
                                                auth=("neo4j", "s-cypher"))
        TestMatch.session = TestMatch.driver.session()
        TestMatch.tx = TestMatch.session.begin_transaction()

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        TestMatch.tx.closed()
        TestMatch.driver.close()
        TestMatch.server.close()

    def test_match_1(self):
        s_cypher = dedent("""
        MATCH (n:City@T("1690", NOW) {name@T("1900", NOW): "London"@T("2000", NOW)})
        RETURN n
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_match_1:", s_cypher, '\n', cypher_query, '\n')
        results = TestMatch.tx.run(cypher_query)
        for result in results:
            print(result)

    def test_match_2(self):
        s_cypher = dedent("""
        MATCH (n1:Person)-[:LIVED@T("2000","2005")]->(n2:City {name: "Brussels"})
        RETURN n1
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_match_2:", s_cypher, '\n', cypher_query, '\n')
        results = TestMatch.tx.run(cypher_query)
        for result in results:
            print(result)

    def test_match_3(self):
        s_cypher = dedent("""
        MATCH path = cPath((n1:Person)-[:FRIEND*2]->(n2:Person))
        RETURN path
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_match_3:", s_cypher, '\n', cypher_query, '\n')
        results = TestMatch.tx.run(cypher_query)
        for result in results:
            print(result)

    def test_match_4(self):
        s_cypher = dedent("""
        MATCH path = pairCPath((n1:Person)-[:FRIEND*2..3]->(n2:Person))
        RETURN path
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_match_4:", s_cypher, '\n', cypher_query, '\n')
        results = TestMatch.tx.run(cypher_query)
        for result in results:
            print(result)

    def test_match_5(self):
        s_cypher = dedent("""
        MATCH path = earliestPath((n1:Station {name: "HangZhou East"})-[:route*]->(n2:Station {name: "XvZhou North"}))
        RETURN path
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_match_5:", s_cypher, '\n', cypher_query, '\n')
        results = TestMatch.tx.run(cypher_query)
        for result in results:
            print(result)

    def test_match_6(self):
        s_cypher = dedent("""
        MATCH path = latestPath((n1:Station {name: "HangZhou East"})-[:route*]->(n2:Station {name: "XvZhou North"}))
        RETURN path
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_match_6:", s_cypher, '\n', cypher_query, '\n')
        results = TestMatch.tx.run(cypher_query)
        for result in results:
            print(result)

    def test_match_7(self):
        s_cypher = dedent("""
        MATCH path = fastestPath((n1:Station {name: "HangZhou East"})-[:route*]->(n2:Station {name: "XiAn North"}))
        RETURN path
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_match_7:", s_cypher, '\n', cypher_query, '\n')
        results = TestMatch.tx.run(cypher_query)
        for result in results:
            print(result)

    def test_match_8(self):
        s_cypher = dedent("""
        MATCH path = shortestSPath((n1:Station {name: "HangZhou East"})-[:route*]->(n2:Station {name: "XiAn North"}))
        RETURN path
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_match_8:", s_cypher, '\n', cypher_query, '\n')
        results = TestMatch.tx.run(cypher_query)
        for result in results:
            print(result)

    def test_match_9(self):
        s_cypher = dedent("""
        MATCH (n:Person) BETWEEN interval("1940", NOW)
        WHERE n.name STARTS WITH "Mary"
        RETURN n.name
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_match_9:", s_cypher, '\n', cypher_query, '\n')
        results = TestMatch.tx.run(cypher_query)
        for result in results:
            print(result)

    def test_match_10(self):
        s_cypher = dedent("""
        MATCH (n:Person) AT TIME date("1950")
        WHERE n.name STARTS WITH "Mary"
        RETURN n.name
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_match_10:", s_cypher, '\n', cypher_query, '\n')
        results = TestMatch.tx.run(cypher_query)
        for result in results:
            print(result)

    def test_match_11(self):
        s_cypher = dedent("""
        MATCH (n:Person) AT TIME date("2015202T21+18:00")
        WHERE n.name STARTS WITH "Mary"
        RETURN n.name
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_match_11:", s_cypher, '\n', cypher_query, '\n')
        results = TestMatch.tx.run(cypher_query)
        for result in results:
            print(result)

    def test_match_12(self):
        s_cypher = dedent("""
        MATCH (n:Person) 
        BETWEEN interval("1940", NOW) 
        RETURN n.name limit 10
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_match_2:", s_cypher, '\n', cypher_query, '\n')
        results = TestMatch.tx.run(cypher_query)
        for result in results:
            print(result)

    def test_match_13(self):
        s_cypher = dedent("""
        MATCH (n:Person @T("1690", NOW)) 
        BETWEEN interval("1940", NOW) 
        RETURN n.name
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_match_13:", s_cypher, '\n', cypher_query, '\n')
        results = TestMatch.tx.run(cypher_query)
        for result in results:
            print(result)

    def test_match_14(self):
        s_cypher = dedent("""
        MATCH (n:Person @T("1960", NOW)) 
        BETWEEN interval("1940", NOW)
        RETURN n.name
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_match_14:", s_cypher, '\n', cypher_query, '\n')
        results = TestMatch.tx.run(cypher_query)
        for result in results:
            print(result)

    def test_match_15(self):
        s_cypher = dedent("""
        MATCH (n:Person{name: 'Pauline Boutler'})
        WITH n AS person
        RETURN person.name@T;
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_match_15:", s_cypher, '\n', cypher_query, '\n')
        results = TestMatch.tx.run(cypher_query)
        for result in results:
            print(result)

    def test_match_16(self):
        s_cypher = dedent("""
        MATCH (n:Person{name: 'Pauline Boutler'})
        WITH n.name + '000' as name
        RETURN name;
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_match_16:", s_cypher, '\n', cypher_query, '\n')
        results = TestMatch.tx.run(cypher_query)
        for result in results:
            print(result)

    def test_match_17(self):
        s_cypher = dedent("""
        MATCH (n:Person{name: 'Pauline Boutler'})
        WITH n.name AS name
        RETURN name@T;
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_match_17:", s_cypher, '\n', cypher_query, '\n')
        results = TestMatch.tx.run(cypher_query)
        for result in results:
            print(result)

    def test_match_18(self):
        s_cypher = dedent("""
        SNAPSHOT date('1999')
        MATCH path = (a:Person)-[*1..5]->(b:Person)
        RETURN path;
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_match_18:", s_cypher, '\n', cypher_query, '\n')
        results = TestMatch.tx.run(cypher_query)
        for result in results:
            print(result)

    def test_match_19(self):
        s_cypher = dedent("""
        MATCH (a:Person)-[r:FRIENDS_WITH]->(b:Person)
        WHERE r@T.from < '2022-01-01'
        RETURN a, b;
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_match_19:", s_cypher, '\n', cypher_query, '\n')
        results = TestMatch.tx.run(cypher_query)
        for result in results:
            print(result)

    def test_match_20(self):
        s_cypher = dedent("""
        MATCH (n:City@T("1690", NOW) {name@T("1900", NOW): "London"@T("2000", NOW)}) -[r:route]->(m:City@T("1000", NOW) {name@T("1900", NOW): "Birmingham"@T("2200", NOW)})
        WHERE r@T.from < '2022-01-01'
        RETURN n;
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_match_20:", s_cypher, '\n', cypher_query, '\n')
        results = TestMatch.tx.run(cypher_query)
        for result in results:
            print(result)

    def test_match_21(self):
        s_cypher = dedent("""
        MATCH (n:City {name: "London"}) -[r:route]->(m:City@T("1000", NOW) {name@T("1900", NOW): "Birmingham"@T("2200", NOW)})
        WHERE r@T.from < '2022-01-01'
        RETURN n;
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_match_21:", s_cypher, '\n', cypher_query, '\n')
        results = TestMatch.tx.run(cypher_query)
        for result in results:
            print(result)

    def test_match_22(self):
        s_cypher = dedent("""
        MATCH (n:Person@T("1937", NOW) {name@T("1937", NOW): "Mary Smith"@T("1937", "1959")}) -[r:LIVE_IN]->(m:City@T("1581", NOW) {name@T("1581", NOW): "Antwerp"@T("1581", NOW)})
        WHERE r@T.from > '1989-08-09'
        RETURN n;
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_match_22:", s_cypher, '\n', cypher_query, '\n')
        results = TestMatch.tx.run(cypher_query)
        for result in results:
            print(result)

    def test_match_23(self):
        s_cypher = dedent("""
        MATCH (n:Person{name@T("1937", NOW): "Mary Smith"@T("1937", "1959")}) -[r:LIVE_IN]->(m:City@T("1581", NOW) {name@T("1581", NOW): "Antwerp"@T("1581", NOW)})
        WHERE r@T.from > '1989-08-09'
        RETURN n;
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_match_23:", s_cypher, '\n', cypher_query, '\n')
        results = TestMatch.tx.run(cypher_query)
        for result in results:
            print(result)

    def test_match_24(self):
        s_cypher = dedent("""
        MATCH (n:Person{name@T("1937", NOW): "Mary Smith"@T("1937", "1959")}) -[r:LIKE]->(m:Brand@T("1938", NOW) {name@T("1938", NOW): "Samsung"@T("1938", NOW)})
        WHERE r@T.from > '1890-08-09'
        RETURN m;
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_match_24:", s_cypher, '\n', cypher_query, '\n')
        results = TestMatch.tx.run(cypher_query)
        for result in results:
            print(result)

    def test_match_25(self):
        s_cypher = dedent("""
        MATCH (n1:Person {name: 'Pauline Boutler'})-[e:FRIEND]->(n2:Person)
        WHERE e@T.to >= date ('2000')
        RETURN n2;
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_match_25:", s_cypher, '\n', cypher_query, '\n')
        results = TestMatch.tx.run(cypher_query)
        for result in results:
            print(result)

    def test_match_26(self):
        s_cypher = dedent("""
        MATCH (n1:Person)-[e:FRIEND]->(n2:Person {name: 'Cathy Van'})
        WHERE e@T.from >= date ('1990')
        RETURN n1;
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_match_26:", s_cypher, '\n', cypher_query, '\n')
        results = TestMatch.tx.run(cypher_query)
        for result in results:
            print(result)

    def test_match_27(self):
        s_cypher = dedent("""
        MATCH (n1:Person)-[e:FRIEND]->(n2:Person {name: 'Cathy Van'})
        WHERE n1.name ENDS WITH 'Burton'
        RETURN n1;
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_match_27:", s_cypher, '\n', cypher_query, '\n')
        results = TestMatch.tx.run(cypher_query)
        for result in results:
            print(result)

    def test_match_28(self):
        s_cypher = dedent("""
        MATCH (n1:Person)
        WHERE n1.name CONTAINS 'Mary Smith'
        RETURN n1;
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_match_28:", s_cypher, '\n', cypher_query, '\n')
        results = TestMatch.tx.run(cypher_query)
        for result in results:
            print(result)

    def test_match_29(self):
        s_cypher = dedent("""
        MATCH (n1:Person)-[:LIVED@T("2000","2002")]->(n2:City {name: "Brussels"})
        RETURN n1;
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_match_29:", s_cypher, '\n', cypher_query, '\n')
        results = TestMatch.tx.run(cypher_query)
        for result in results:
            print(result)

    def test_match_30(self):
        s_cypher = dedent("""
        MATCH (n1:Person)-[:LIVED@T("2001","2022")]->(n2:City)
        WHERE n2.name CONTAINS 'Paris' AND n1@T.from <= date('1960')
        RETURN n1;
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_match_30:", s_cypher, '\n', cypher_query, '\n')
        results = TestMatch.tx.run(cypher_query)
        for result in results:
            print(result)

    def test_match_31(self):
        s_cypher = dedent("""
        MATCH (n1:Person)-[e:FRIEND]->(n2:Person)
        WHERE n1.name STARTS WITH "Mary" AND (e@T.to - e@T.from) >= duration({years: 20})
        RETURN e;
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_match_31:", s_cypher, '\n', cypher_query, '\n')
        results = TestMatch.tx.run(cypher_query)
        for result in results:
            print(result)

    def test_match_32(self):
        s_cypher = dedent("""
        MATCH (n:Brand)
        WHERE n.name CONTAINS 'Samsung'
        WITH n AS brand
        RETURN brand.name@T;
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_match_32:", s_cypher, '\n', cypher_query, '\n')
        results = TestMatch.tx.run(cypher_query)
        for result in results:
            print(result)

    def test_match_33(self):
        s_cypher = dedent("""
        MATCH (n:Person{name: 'Daniel Yang'})
        WITH n.name + 'Justin' as name
        RETURN name;
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_match_33:", s_cypher, '\n', cypher_query, '\n')
        results = TestMatch.tx.run(cypher_query)
        for result in results:
            print(result)

    def test_match_34(self):
        s_cypher = dedent("""
        MATCH path = cPath((n1:Person)-[:LIVE_IN*2]->(n2:City))
        RETURN path;
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_match_34:", s_cypher, '\n', cypher_query, '\n')
        results = TestMatch.tx.run(cypher_query)
        for result in results:
            print(result)

    def test_match_35(self):
        s_cypher = dedent("""
        MATCH path = cPath((n1:Person)-[:LIKE*2]->(n2:Brand))
        RETURN path;
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_match_35:", s_cypher, '\n', cypher_query, '\n')
        results = TestMatch.tx.run(cypher_query)
        for result in results:
            print(result)

    def test_match_36(self):
        s_cypher = dedent("""
        MATCH path = cPath((n1:Person)-[:FRIEND*2]->(n2:Person))
        RETURN path;
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_match_36:", s_cypher, '\n', cypher_query, '\n')
        results = TestMatch.tx.run(cypher_query)
        for result in results:
            print(result)

    def test_match_37(self):
        s_cypher = dedent("""
        MATCH path = pairCPath((n1:Person)-[:FRIEND*1..2]->(n2:Person))
        RETURN path;
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_match_37:", s_cypher, '\n', cypher_query, '\n')
        results = TestMatch.tx.run(cypher_query)
        for result in results:
            print(result)

    def test_match_38(self):
        s_cypher = dedent("""
        MATCH path = pairCPath((n1:Person)-[:LIKE*1..2]->(n2:Brand))
        RETURN path;
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_match_38:", s_cypher, '\n', cypher_query, '\n')
        results = TestMatch.tx.run(cypher_query)
        for result in results:
            print(result)

    def test_match_39(self):
        s_cypher = dedent("""
        MATCH path = pairCPath((n1:Person)-[:LIKE*2..3]->(n2:Brand))
        RETURN path;
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_match_39:", s_cypher, '\n', cypher_query, '\n')
        results = TestMatch.tx.run(cypher_query)
        for result in results:
            print(result)

    def test_match_40(self):
        s_cypher = dedent("""
        MATCH path = pairCPath((n1:Person)-[:LIVE_IN*1..2]->(n2:City))
        RETURN path;
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_match_40:", s_cypher, '\n', cypher_query, '\n')
        results = TestMatch.tx.run(cypher_query)
        for result in results:
            print(result)

    def test_match_41(self):
        s_cypher = dedent("""
        MATCH path = pairCPath((n1:Person)-[:LIVE_IN*2..3]->(n2:City))
        RETURN path;
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_match_41:", s_cypher, '\n', cypher_query, '\n')
        results = TestMatch.tx.run(cypher_query)
        for result in results:
            print(result)

    def test_match_42(self):
        s_cypher = dedent("""
        MATCH path = earliestPath((n1:Station {name: "HangZhou East"})-[:route*]->(n2:Station {name: "Ning Bo"}))
        RETURN path;
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_match_42:", s_cypher, '\n', cypher_query, '\n')
        results = TestMatch.tx.run(cypher_query)
        for result in results:
            print(result)

    def test_match_43(self):
        s_cypher = dedent("""
        MATCH path = latestPath((n1:Station {name: "HangZhou East"})-[:route*]->(n2:Station {name: "Ning Bo"}))
        RETURN path;
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_match_43:", s_cypher, '\n', cypher_query, '\n')
        results = TestMatch.tx.run(cypher_query)
        for result in results:
            print(result)

    def test_match_44(self):
        s_cypher = dedent("""
        MATCH path = fastestPath((n1:Station {name: "HangZhou East"})-[:route*]->(n2:Station {name: "Ning Bo"}))
        RETURN path;
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_match_44:", s_cypher, '\n', cypher_query, '\n')
        results = TestMatch.tx.run(cypher_query)
        for result in results:
            print(result)

    def test_match_45(self):
        s_cypher = dedent("""
        MATCH path = shortestSPath((n1:Station {name: "HangZhou East"})-[:route*]->(n2:Station {name: "Ning Bo"}))
        RETURN path;
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_match_45:", s_cypher, '\n', cypher_query, '\n')
        results = TestMatch.tx.run(cypher_query)
        for result in results:
            print(result)

    def test_match_46(self):
        s_cypher = dedent("""
        MATCH path = shortestSPath((n1:Station {name: "HangZhou East"})-[:route*2]->(n2:Station {name: "Ning Bo"}))
        RETURN path;
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_match_46:", s_cypher, '\n', cypher_query, '\n')
        results = TestMatch.tx.run(cypher_query)
        for result in results:
            print(result)

    def test_match_47(self):
        s_cypher = dedent("""
        MATCH path = fastestPath((n1:Station {name: "HangZhou East"})-[:route*2..3]->(n2:Station {name: "Ning Bo"}))
        RETURN path;
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_match_47:", s_cypher, '\n', cypher_query, '\n')
        results = TestMatch.tx.run(cypher_query)
        for result in results:
            print(result)

    def test_match_48(self):
        s_cypher = dedent("""
        MATCH (n:City)
        AT_TIME date("2000")
        WHERE n.spot STARTS WITH "West"
        RETURN n.name;
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_match_48:", s_cypher, '\n', cypher_query, '\n')
        results = TestMatch.tx.run(cypher_query)
        for result in results:
            print(result)

