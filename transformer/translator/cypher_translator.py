from transformer.translator.s_cypher_walker import *
from transformer.ir.s_cypher_clause import *
from transformer.grammar_parser.s_cypherParser import s_cypherParser
from antlr4 import *


# translate the S-Cypher input to its internal representation
class CypherTranslator:
    def __init__(self, parser: s_cypherParser):
        self.parser = parser

    def translate_s_cypher_query(self) -> SCypherClause:
        walker = ParseTreeWalker()
        extractor = SCypherWalker(self.parser)
        tree = self.parser.oC_Query()
        print(tree.toStringTree(tree, self.parser))
        walker.walk(extractor, tree)
        clause = extractor.query_clause
        return SCypherClause(clause)

