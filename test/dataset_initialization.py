from neo4j import BoltDriver

from test.graphdb_connector import GraphDBConnector
from transformer.s_transformer import STransformer


class DataSet1:
    def __init__(self, driver: BoltDriver):
        self.driver = driver

    def rebuild(self):
        self.clear()
        self.initialize()

    def clear(self):
        s_cypher_query = """
        MATCH (p:Person),(c:City),(b:Brand)
        DETACH DELETE p,c,b
        """
        cypher_query = STransformer.transform(s_cypher_query)
        self.driver.execute_query(cypher_query)

    def initialize(self):
        s_cypher_query = """
        CREATE (p1:Person{name:"Pauline Boutler"}) AT TIME timePoint("1978")
        CREATE (p2:Person{name:"Cathy Van"}) AT TIME timePoint("1960")
        CREATE (p3:Person{name:"Sandra Carter"}) AT TIME timePoint("1967")
        CREATE (p4:Person{name:"Peter Burton"}) AT TIME timePoint("1960")
        CREATE (p5:Person{name:"Daniel Yang"}) AT TIME timePoint("1995")
        CREATE (p6:Person{name:"Mary Smith"}) AT TIME timePoint("1937")
        CREATE (c1:City{name:"London"}) AT TIME timePoint("1688")
        CREATE (c2:City{name:"Brussels"}) AT TIME timePoint("1581")
        CREATE (c3:City{name:"Paris"}) AT TIME timePoint("1792")
        CREATE (c4:City{name:"Antwerp"}) AT TIME timePoint("1581")
        CREATE (c5:City{name:"New York"}) AT TIME timePoint("1776")
        CREATE (b1:Brand{name:"Samsung"}) AT TIME timePoint("1938")
        CREATE (b2:Brand{name:"Lucky Goldstar"}) AT TIME timePoint("1958")
        CREATE (p1)-[:FRIEND@T("2002", "2017")]->(p2)
        CREATE (p4)-[:FRIEND@T("1995", NOW)]->(p2), (p4)-[:FRIEND@T("2015", "2018")]->(p5)
        CREATE (p6)-[:FRIEND@T("1993", NOW)]->(p4), (p6)-[:FRIEND@T("2010", "2018")]->(p1)
        CREATE (p1)-[:LIVE@T("1978", "2003")]->(c2), (p1)-[:LIVE@T("2004", NOW)]->(c1)
        CREATE (p2)-[:LIVE@T("1980", '2000')]->(c2), (p2)-[:LIVE@T("2001", NOW)]->(c3)
        CREATE (p3)-[:LIVE@T("1967", NOW)]->(c5)
        CREATE (p4)-[:LIVE@T("1961", NOW)]->(c5)
        CREATE (p5)-[:LIVE@T("1995", NOW)]->(c4)
        CREATE (p6)-[:LIVE@T("1979", "1989")]->(c2), (p6)-[:LIVE@T("1990", NOW)]->(c4)
        CREATE (p1)-[:LIKE@T("2005", "2008")]->(b1)
        CREATE (p2)-[:LIKE@T("1998", NOW)]->(b2)
        CREATE (p3)-[:LIKE@T("2001", NOW)]->(b1), (p3)-[:LIKE@T("1995", "2000")]->(b2)
        CREATE (p6)-[:LIKE@T("1982", NOW)]->(b1)
        SET p6.name = "Mary Smith Taylor"
        AT TIME timePoint("1960")
        """
        cypher_query = STransformer.transform(s_cypher_query)
        self.driver.execute_query(cypher_query)


class DataSet2:
    def __init__(self, driver: BoltDriver):
        self.driver = driver

    def rebuild(self):
        self.clear()
        self.initialize()

    def clear(self):
        s_cypher_query = """
        MATCH (s:Station)
        DETACH DELETE s
        """
        cypher_query = STransformer.transform(s_cypher_query)
        self.driver.execute_query(cypher_query)

    def initialize(self):
        s_cypher_query = """
        CREATE (s0:Station{name:"Zhenzhoudong Railway Station"}) AT TIME timePoint("1999")
        CREATE (s1:Station{name:"Lianyungang Railway Station"}) AT TIME timePoint("1999")
        CREATE (s2:Station{name:"Xi'anbei Railway Station"}) AT TIME timePoint("1999")
        CREATE (s3:Station{name:"Xuzhoudong Railway Station"}) AT TIME timePoint("1999")
        CREATE (s4:Station{name:"Nanjingnan Railway Station"}) AT TIME timePoint("1999")
        CREATE (s5:Station{name:"Hefeinan Railway Station"}) AT TIME timePoint("1999")
        CREATE (s6:Station{name:"Shanghai Hongqiao Railway Station"}) AT TIME timePoint("1999")
        CREATE (s7:Station{name:"Wuhan Railway Station"}) AT TIME timePoint("1999")
        CREATE (s8:Station{name:"Hangzhoudong Railway Station"}) AT TIME timePoint("1999")
        CREATE (s3)-[r0:G1323@T("2023-02-06T12:44", "2023-02-06T14:32")]->(s0)
        CREATE (s3)-[r1:G289@T("2023-02-06T13:46", "2023-02-06T14:54")]->(s1)
        CREATE (s6)-[r2:G7540@T("2023-02-06T13:03", "2023-02-06T16:40")]->(s1)
        CREATE (s6)-[r3:G116@T("2023-02-06T09:26", "2023-02-06T12:28")]->(s3)
        CREATE (s4)-[r4:G178@T("2023-02-06T11:12", "2023-02-06T12:32")]->(s3)
        CREATE (s5)-[r5:G3190@T("2023-02-06T12:09", "2023-02-06T17:39")]->(s2)
        CREATE (s6)-[r6:G1204@T("2023-02-06T09:33", "2023-02-06T11:04")]->(s4)
        CREATE (s8)-[r7:G7602@T("2023-02-06T09:54", "2023-02-06T11:58")]->(s5)
        CREATE (s8)-[r8:G7349@T("2023-02-06T08:15", "2023-02-06T09:29")]->(s6)
        CREATE (s8)-[r9:G3190@T("2023-02-06T09:42", "2023-02-06T17:39")]->(s2)
        CREATE (s7)-[r10:G822@T("2023-02-06T14:25", "2023-02-06T19:22")]->(s2)
        CREATE (s8)-[r11:G590@T("2023-02-06T09:13", "2023-02-06T14:04")]->(s7)
        CREATE (s8)-[r12:G7372@T("2023-02-06T08:07", "2023-02-06T09:23")]->(s6)
        """
        cypher_query = STransformer.transform(s_cypher_query)
        self.driver.execute_query(cypher_query)


def test():
    graphdb_connector = GraphDBConnector()
    graphdb_connector.out_net_connect()
    # dataset1 = DataSet1(graphdb_connector.driver)
    # dataset1.rebuild()
    dataset2 = DataSet2(graphdb_connector.driver)
    dataset2.rebuild()
    graphdb_connector.close()

# test()
