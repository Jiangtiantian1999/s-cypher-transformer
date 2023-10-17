from unittest import TestCase

from transformer.main import transform_to_cypher


class TestWith(TestCase):
    def test_with_1(self):
        s_cypher = 'MATCH (n:Person{name: "Pauline Boutler"})' \
                   '\nWITH n AS person' \
                   '\nRETURN person.name@T'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_with_1:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')

    def test_with_2(self):
        s_cypher = 'MATCH (n:Person{name: "Pauline Boutler"})' \
                   '\nWITH n.name + "000" as name' \
                   '\nRETURN name'
        cypher_query = transform_to_cypher(s_cypher)
        print("test_with_2:", '\n', s_cypher, '\n\n', cypher_query, '\n\n')

## WITH date({year: 1984, month: 10, day: 11}) AS dd

# 修改或转换结果：
# 进行计算或使用函数：
# 进行排序和限制：
# 进行过滤
# 多步骤查询中的连接