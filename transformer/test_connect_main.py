import os
import sys
root_path = os.path.dirname(os.path.dirname(__file__))
sys.path.append(root_path)

from antlr4 import *

from transformer.generator.cypher_generator import CypherGenerator
from transformer.grammar_parser.s_cypherLexer import s_cypherLexer
from transformer.grammar_parser.s_cypherParser import s_cypherParser
from transformer.translator.cypher_translator import CypherTranslator

from neo4j import GraphDatabase

from textwrap import dedent

def transform_to_cypher(s_cypher_query: InputStream | str):
    if s_cypher_query.__class__ == str:
        s_cypher_query = InputStream(s_cypher_query)
    # 词法分析
    lexer = s_cypherLexer(s_cypher_query)
    # 语法分析
    parser = s_cypherParser(CommonTokenStream(lexer))
    # 转换为中间形式
    translator = CypherTranslator(parser)
    s_cypher_entity = translator.translate_s_cypher_query()
    # 转换为Cypher查询字符串
    cypher_query = CypherGenerator().generate_cypher_query(s_cypher_entity)
    return cypher_query


if __name__ == '__main__':
    s_cypher_query = dedent("""
        MATCH (n:City@T("1690", NOW) {name@T("1900", NOW): "London"@T("2000", NOW)})
        RETURN n
        """)
    # s_cypher_query = StdinStream()
    cypher_query = transform_to_cypher(s_cypher_query)
    print(cypher_query)

    # test connect
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "s-cypher"))
    session = driver.session()
    tx = session.begin_transaction()
    result = tx.run(cypher_query)

    # tx.commit()  # 查询不需要提交
    tx.closed()
    driver.close()


