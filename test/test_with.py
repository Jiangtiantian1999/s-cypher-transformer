from textwrap import dedent
from unittest import TestCase

from transformer.s_transformer import STransformer


class TestWith(TestCase):
    def test_with_1(self):
        s_cypher = dedent("""
        MATCH (n:Person{name: "Pauline Boutler"})
        WITH n AS person
        RETURN person.name@T
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_with_1:", s_cypher, '\n', cypher_query, '\n')

    def test_with_2(self):
        s_cypher = dedent("""
        MATCH (n:Person{name: "Pauline Boutler"})
        WITH n.name + "000" as name
        RETURN name
        """)
        cypher_query = STransformer.transform(s_cypher)
        print("test_with_2:", s_cypher, '\n', cypher_query, '\n')

## WITH date({year: 1984, month: 10, day: 11}) AS dd

# 修改或转换结果：
# 进行计算或使用函数：
# 进行排序和限制：
# 进行过滤
# 多步骤查询中的连接
