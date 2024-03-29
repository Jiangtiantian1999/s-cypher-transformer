from neo4j import BoltDriver

from test.graphdb_connector import GraphDBConnector
from transformer.s_transformer import STransformer


class PersonDataSet:
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


# graphdb_connector = GraphDBConnector()
# graphdb_connector.default_connect()
# person_dataset = PersonDataSet(graphdb_connector.driver)
# person_dataset.rebuild()
# graphdb_connector.close()
