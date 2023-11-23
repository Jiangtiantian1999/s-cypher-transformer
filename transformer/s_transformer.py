from __future__ import annotations
from antlr4 import *
from transformer.exceptions.s_exception import SCypherErrorListener, SCypherErrorStrategy
from transformer.generator.cypher_generator import CypherGenerator
from transformer.grammar_parser.s_cypherLexer import s_cypherLexer
from transformer.grammar_parser.s_cypherParser import s_cypherParser
from transformer.translator.cypher_translator import CypherTranslator


class STransformer:
    @staticmethod
    def transform(s_cypher_query: InputStream | str):
        if s_cypher_query.__class__ == str:
            s_cypher_query = InputStream(s_cypher_query)
        # 词法分析
        lexer = s_cypherLexer(s_cypher_query)
        # 语法分析
        parser = s_cypherParser(CommonTokenStream(lexer))
        # 语法错误报告
        parser.removeErrorListeners()
        parser.addErrorListener(SCypherErrorListener())
        # 语法错误恢复
        parser._errHandler = SCypherErrorStrategy()
        # 转换为中间形式
        translator = CypherTranslator(parser)
        s_cypher_entity = translator.translate_s_cypher_query()
        # 转换为Cypher查询字符串
        cypher_query = CypherGenerator().generate_cypher_query(s_cypher_entity)
        return cypher_query
