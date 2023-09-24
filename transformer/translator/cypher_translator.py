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
        # self.walker = ParseTreeWalker()
        # self.extractor = SCypherWalker(parser)

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

    # def translate_single_query(self):
    #     self.walker.walk(self.extractor, self.parser.oC_SingleQuery())
    #
    # def translate_multi_query_clause(self) -> List[MultiQueryClause]:
    #     # single_query_clause: SingleQueryClause = None,
    #     # with_query_clauses: List[WithQueryClause] = None
    #     pass
    #
    # def translate_union_query(self):
    #     self.walker.walk(self.extractor, self.parser.oC_Union())
    #     self.walker.walk(self.extractor, self.parser.oC_SinglePartQuery())
    #
    # def translate_single_query_clause(self) -> SingleQueryClause:
    #     # reading_clauses: List[ReadingClause] = None,
    #     # updating_clauses: List[UpdatingClause] = None,
    #     # return_clause: ReadingClause
    #     # -----------------是不是要换成ReturnClause-------------
    #     single_tree = self.parser.oC_SinglePartQuery()
    #     single_extractor = SCypherWalker(self.parser)
    #     self.walker.walk(single_extractor, single_tree)
    #     reading_clauses = self.translate_reading_clause()
    #     updating_clauses = self.translate_updating_clause()
    #     return_clause = self.translate_return_clause()
    #     return SingleQueryClause(reading_clauses, updating_clauses, return_clause)
    #
    # def translate_with_query_clauses(self) -> List[WithQueryClause]:
    #     #  with_clause: WithClause,
    #     #  reading_clauses: List[ReadingClause] = None,
    #     #  updating_clauses: List[UpdatingClause] = None
    #     with_tree = self.parser.oC_With()
    #     with_extractor = SCypherWalker(self.parser)
    #     self.walker.walk(with_extractor, with_tree)
    #     reading_clauses = self.translate_reading_clause()
    #     updating_clauses = self.translate_updating_clause()
    #     with_clause = self.extractor.with_clause
    #     return [WithQueryClause(with_clause, reading_clauses, updating_clauses)]
    #
    # def translate_reading_clause(self) -> List[ReadingClause]:
    #     # reading_clause: MatchClause | UnwindClause | CallClause
    #     reading_tree = self.parser.oC_ReadingClause()
    #     reading_extractor = SCypherWalker(self.parser)
    #     self.walker.walk(reading_extractor, reading_tree)
    #     clause = None
    #     if self.parser.oC_Match() is not None:
    #         clause = self.translate_match_clause()
    #     elif self.parser.oC_Unwind() is not None:
    #         clause = self.translate_unwind_query_clause()
    #     elif self.parser.oC_InQueryCall() is not None:
    #         clause = self.translate_in_query_clause()
    #     reading_clauses = [ReadingClause(clause)]
    #     return reading_clauses
    #
    # def translate_updating_clause(self) -> List[UpdatingClause]:
    #     pass
    #
    # def translate_return_clause(self) -> ReturnClause:
    #     # projection_items: List[ProjectionItem],
    #     # is_distinct: bool = False,
    #     # order_by_clause: OrderByClause = None, skip_clause: SkipClause = None,
    #     # limit_clause: LimitClause = None
    #     return_tree = self.parser.oC_Return()
    #     return_extractor = SCypherWalker(self.parser)
    #     self.walker.walk(return_extractor, return_tree)
    #     return return_extractor.return_clause
    #
    # def translate_match_clause(self) -> MatchClause:
    #     # patterns: List[Pattern],
    #     # is_optional: bool = False,
    #     # where_clause: WhereClause = None,
    #     # time_window: TimePoint | Interval = None
    #     match_tree = self.parser.oC_Match()
    #     match_extractor = SCypherWalker(self.parser)
    #     self.walker.walk(match_extractor, match_tree)
    #     match_clause = match_extractor.match_clause
    #     return match_clause
    #
    # def translate_unwind_query_clause(self) -> UnwindClause:
    #     pass
    #
    # def translate_call_query_clause(self) -> CallClause:
    #     call_tree = self.parser.oC_InQueryCall()
    #     self.walker.walk((self.extractor, call_tree))
    #     return self.extractor.inner_call_clause
    #
    # # def translate_where_clause(self) -> WhereClause:
    # #     where_tree = self.parser.oC_Where()
    # #     self.walker.walk(self.extractor, where_tree)
    # #     return self.extractor.where_clause
    #
    # # reading clause
    # def translate_in_query_clause(self):
    #     pass
