from s_cypher_walker import SCypherWalker
from transformer.ir.s_cypher_clause import *
from transformer.grammar_parser.s_cypherParser import s_cypherParser
from transformer.grammar_parser.s_cypherLexer import s_cypherLexer
from antlr4 import *


# translate the S-Cypher input to its internal representation
class CypherTranslator:
    @staticmethod
    def set_parser(self, s_cypher_input) -> s_cypherParser:
        lexer = s_cypherLexer(s_cypher_input)
        tokens = CommonTokenStream(lexer)
        parser = s_cypherParser(tokens)
        return parser

    def translate_match_clause(self, match_input) -> MatchClause:
        parser = self.set_parser(match_input)
        tree = parser.oC_Match()
        walker = ParseTreeWalker()
        extractor = SCypherWalker(parser)
        walker.walk(extractor, tree)
        patterns = extractor.match_patterns
        is_optional = extractor.match_is_optional
        where_clause = extractor.match_where_clause
        time_window = extractor.match_time_window
        return MatchClause(patterns, is_optional, where_clause, time_window)

    def translate_single_query_clause(self, single_query_clause: list[str]) -> SingleQueryClause:
        pass

    def translate_union_query_clause(self, union_query_clause: list[str]) -> UnionQueryClause:
        pass

    def translate_multi_query_clause(self, multi_query_clause: list[str]) -> MultiQueryClause:
        pass

    def translate_with_query_clause(self, with_query_clause: list[str]) -> WithQueryClause:
        pass

    def translate_reading_clause(self, reading_clause: list[str]) -> ReadingClause:
        pass

    def translate_where_clause(self, where_clause: list[str]) -> WhereClause:
        # interval_conditions = []
        pass

    def translate_updating_clause(self, updating_clause: list[str]) -> UpdatingClause:
        pass

    def translate_with_clause(self, with_clause: list[str]) -> WithClause:
        pass
