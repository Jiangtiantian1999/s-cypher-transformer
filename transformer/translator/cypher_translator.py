from s_cypher_walker import SCypherWalker
from transformer.ir.s_cypher_clause import *
from transformer.grammar_parser.s_cypherParser import s_cypherParser
from transformer.grammar_parser.s_cypherLexer import s_cypherLexer
from antlr4 import *
from transformer.ir.s_graph import *


# translate the S-Cypher input to its internal representation
class CypherTranslator:
    @staticmethod
    def set_parser(s_cypher_input) -> s_cypherParser:
        lexer = s_cypherLexer(s_cypher_input)
        tokens = CommonTokenStream(lexer)
        parser = s_cypherParser(tokens)
        return parser

    def translate_match_clause(self, match_input) -> MatchClause:
        match_parser = self.set_parser(match_input)
        match_tree = match_parser.oC_Match()
        match_walker = ParseTreeWalker()
        match_extractor = SCypherWalker(match_parser)
        match_walker.walk(match_extractor, match_tree)
        match_clause = match_extractor.match_clause
        return match_clause

    def translate_where_clause(self, where_input) -> WhereClause:
        where_parser = self.set_parser(where_input)
        where_tree = where_parser.oC_Where()
        where_walker = ParseTreeWalker()
        where_extractor = SCypherWalker(where_parser)
        where_walker.walk(where_extractor, where_tree)
        return where_extractor.where_clause

    def translate_single_query_clause(self, single_query_input) -> SingleQueryClause:
        pass

    def translate_union_query_clause(self, union_query_input) -> UnionQueryClause:
        union_parser = self.set_parser(union_query_input)
        union_tree = union_parser.oC_Union()
        union_walker = ParseTreeWalker()
        union_extractor = SCypherWalker(union_parser)
        union_walker.walk(union_extractor, union_tree)
        multi_query_clauses = union_extractor.multi_query_clause
        is_all_list = []
        for multi_query_clause in multi_query_clauses:
            is_all_list.append(multi_query_clause.is_all)
        return UnionQueryClause(multi_query_clauses, is_all_list)

    def translate_multi_query_clause(self, multi_query_clause: list[str]) -> MultiQueryClause:
        pass

    def translate_with_query_clause(self, with_query_clause: list[str]) -> WithQueryClause:
        pass

    def translate_reading_clause(self, reading_input):
        reading_parser = self.set_parser(reading_input)
        reading_tree = reading_parser.oC_ReadingClause()
        reading_walker = ParseTreeWalker()
        reading_extractor = SCypherWalker(reading_parser)
        reading_walker.walk(reading_extractor, reading_tree)
        match_clause = reading_extractor.match_clause
        unwind_clause = reading_extractor.unwind_clause
        inner_call_clause = reading_extractor.inner_call_clause
        return match_clause, unwind_clause, inner_call_clause

    def translate_updating_clause(self, updating_clause: list[str]) -> UpdatingClause:
        pass

    def translate_with_clause(self, with_clause: list[str]) -> WithClause:
        pass

    def translate_edge(self, edge_input) -> SEdge:
        pass

    def translate_node(self, node_input) -> SNode:
        node_parser = self.set_parser(node_input)
        node_tree = node_parser.oC_Where()
        node_walker = ParseTreeWalker()
        node_extractor = SCypherWalker(node_parser)
        node_walker.walk(node_extractor, node_tree)
        # labels: List[str], content: str = None, variable: str = None, interval: Interval = None

    def translate_object_node(self, obj_node_input) -> ObjectNode:
        pass

    def translate_path(self, path_input) -> SPath:
        pass
