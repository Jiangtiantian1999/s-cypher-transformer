from transformer.translator.s_cypher_walker import *
from transformer.ir.s_cypher_clause import *
from transformer.grammar_parser.s_cypherParser import s_cypherParser
from transformer.grammar_parser.s_cypherLexer import s_cypherLexer
from antlr4 import *
from transformer.ir.s_graph import *
from antlr4.tree.Trees import Trees


# translate the S-Cypher input to its internal representation
class CypherTranslator:
    def __init__(self, parser: s_cypherParser):
        self.parser = parser

    def translate_s_cypher_query(self) -> SCypherClause:
        clause = None
        walker = ParseTreeWalker()
        extractor = SCypherWalker(self.parser)
        tree = self.parser.oC_Query()
        walker.walk(extractor, tree)
        clause = extractor.query_clause
        return SCypherClause(clause)

