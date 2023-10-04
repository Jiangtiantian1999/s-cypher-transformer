from unittest import TestCase

from transformer.main import transform_to_cypher


class TestCall(TestCase):
    def test_call_1(self):
        s_cypher = 'CALL db.labels'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_call_1:", '\n', s_cypher, '\n', cypher_query, '\n')

    def test_call_2(self):
        s_cypher = 'CALL dbms.procedures()' \
                   '\nYIELD name, signature' \
                   '\nWHERE name="dbms.listConfig"' \
                   '\nRETURN signature'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_call_2:", '\n', s_cypher, '\n', cypher_query, '\n')

    def test_call_3(self):
        s_cypher = 'CALL org.opencypher.procedure.example.addNodeToIndex("users", 0, "name")'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_call_3:", '\n', s_cypher, '\n', cypher_query, '\n')

    def test_call_4(self):
        s_cypher = 'MATCH path = (n1:Person)-[:FRIEND*2]->(n2:Person)' \
                   '\nCALL cPath(path)' \
                   '\nYIELD cpath' \
                   '\nRETURN cpath'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_call_4:", '\n', s_cypher, '\n', cypher_query, '\n')
