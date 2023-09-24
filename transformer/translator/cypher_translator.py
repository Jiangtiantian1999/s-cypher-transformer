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
        if self.parser.oC_RegularQuery() is not None:
            # print(Trees.toStringTree(tree, None, self.parser))
            clause = extractor.union_query_clause
        elif self.parser.oC_StandaloneCall() is not None:
            clause = extractor.stand_alone_call_clause
        elif self.parser.oC_Unwind() is not None:
            clause = extractor.unwind_clause
        return SCypherClause(clause)
        # --------test match--------
        # match_clause = self.translate_match_clause()
        # reading_clause = ReadingClause(match_clause)
        # return_clause = self.translate_return_clause()
        # single_query_clause = SingleQueryClause(reading_clauses=[reading_clause], return_clause=return_clause)
        # multi_query_clause = MultiQueryClause(single_query_clause)
        # union_query_clause = UnionQueryClause([multi_query_clause])
        # s_query_clause = SCypherClause(union_query_clause)
        # return s_query_clause
