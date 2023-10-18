from unittest import TestCase
from textwrap import dedent
from transformer.main import transform_to_cypher


class TestSet(TestCase):
    def test_set_1(self):
        s_cypher = """MATCH (n {name: "Pauline Boutler"})
        SET n.gender@T("2000", NOW) = "Male"
        AT_TIME now()
        """
        cypher_query = transform_to_cypher(s_cypher)
        print("test_set_1:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')

    def test_set_2(self):
        s_cypher = """MATCH (n {name: "Pauline Boutler"})
        SET n.gender@T("2000", NOW) = "Male"@T("2000", NOW)
        """
        cypher_query = transform_to_cypher(s_cypher)
        print("test_set_2:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')

    def test_set_3(self):
        s_cypher = """MATCH (n {name: "Pauline Boutler"})
        SET n@T("1978", NOW).gender@T("2000", NOW) = "Male"@T("2000", NOW)
        """
        cypher_query = transform_to_cypher(s_cypher)
        print("test_set_3:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')

    def test_set_4(self):
        s_cypher = """MATCH (:Person {name: "Pauline Boutler"})-[e:LIVE_IN]->(:City {name: "London"})
        SET e.code = "255389"
        """
        cypher_query = transform_to_cypher(s_cypher)
        print("test_set_4:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')

    def test_set_5(self):
        s_cypher = """MATCH (:Person {name: "Pauline Boutler"})-[e:LIVE_IN]->(:City {name: "London"})
        SET e.code = "255389"
        AT_TIME date("2023")
        """
        cypher_query = transform_to_cypher(s_cypher)
        print("test_set_5:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')

    def test_set_6(self):
        s_cypher = """MATCH (n {name: "Pauline Boutler"})
        SET n@T("1960", NOW)
        """
        cypher_query = transform_to_cypher(s_cypher)
        print("test_set_6:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')

    def test_set_7(self):
        s_cypher = """MATCH (n{name: "Pauline Boutler"})
        SET n.name@T("1970", NOW)
        """
        cypher_query = transform_to_cypher(s_cypher)
        print("test_set_7:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')

    def test_set_8(self):
        s_cypher = """MATCH (n {name: "Pauline Boutler"})
        SET n.name#Value@T("1978", "2023")
        """
        cypher_query = transform_to_cypher(s_cypher)
        print("test_set_8:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')

    def test_set_9(self):
        s_cypher = """MATCH (n {name: "Pauline Boutler"})
        SET n@T("1960", NOW).name@T("1960", "2010")#Value@T("1960", "2000")
        """
        cypher_query = transform_to_cypher(s_cypher)
        print("test_set_9:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')

    def test_set_10(self):
        s_cypher = """MATCH (:Person {name: "Pauline Boutler"})-[e:LIVE_IN]->(:City {name: "London"})
        SET e@T("2010", "2020")
        """
        cypher_query = transform_to_cypher(s_cypher)
        print("test_set_10:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')

    def tset_set_11(self):
        # TODO: Test whether an error will be reported when the interval of the child node is not within the interval of the parent node
        s_cypher = """MATCH (n:City@T("1690", NOW))
        SET  n.name@T(1550,1660)
        """
        cypher_query = transform_to_cypher(s_cypher)
        print("test_match_11:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')

    def tset_set_12(self):
        # TODO: Test whether an error will be reported when the interval of the child node is not within the interval of the parent node
        s_cypher = """MATCH (n:City@T("1690", NOW) {name@T("1900", NOW): "London"@T("2000", NOW)})
        SET  n.name#Value@T(1550,1660)
        """
        cypher_query = transform_to_cypher(s_cypher)
        print("test_match_11:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')

    def test_set_12(self):
        # TODO: Test when the new interval for e is not within the interval of the p1
        s_cypher = """MATCH (n1:Person@T("2003", NOW) {name: "John"})-[e:LIVED@T("2010","2023")]->(n2:City@T("1690", NOW) {name@T("1900", NOW): "London"@T("2000", NOW)})
        SET e@T("1700", NOW)
        """
        cypher_query = transform_to_cypher(s_cypher)
        print("test_match_2:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')