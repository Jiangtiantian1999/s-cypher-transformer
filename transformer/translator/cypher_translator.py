from s_cypher_walker import SCypherWalker
from transformer.ir.s_cypher_clause import *
from transformer.ir.s_graph import *
from transformer.exceptions.s_exception import ClauseError
import json


# translate the S-Cypher input to its internal representation
class CypherTranslator:
    @staticmethod
    def translate_s_cypher_query(tokenList: list, s_cypher_walker: SCypherWalker):
        pass

    def translate_single_query_tokens(self, single_query_tokens: list[str]) -> SingleQueryClause:
        pass

    def translate_union_query_clause(self, union_query_tokens: list[str]) -> UnionQueryClause:
        union_query_clause = UnionQueryClause()
        index = 0
        multi_query_clause = MultiQueryClause()
        single_query_tokens = []
        while index < len(union_query_tokens):
            if union_query_tokens[index] == "UNION":
                multi_query_clause.single_query_clause = self.translate_single_query_tokens(single_query_tokens)
                union_query_clause.multi_query_clauses.append(multi_query_clause)
                single_query_tokens.clear()
                if union_query_tokens[index + 1] == "ALL" and union_query_tokens[index + 2] == "SP":
                    union_query_clause.is_all.append(True)
                    index = index + 2
                else:
                    union_query_clause.is_all.append(False)
            elif union_query_tokens[index] == "SP":
                continue
            else:
                single_query_tokens.append(union_query_tokens[index])
            index = index + 1
        return union_query_clause

    def translate_multi_query_clause(self, multi_query_tokens: list[str]) -> MultiQueryClause:
        multi_query_tokens = MultiQueryClause()

    def translate_with_query_clause(self, with_query_tokens: list[str]) -> WithQueryClause:
        with_query_clause = WithQueryClause()

    def translate_reading_clause(self, reading_tokens: list[str]) -> ReadingClause:
        pass

    def translate_match_clause(self, match_tokens: list[str]) -> MatchClause:
        pass

    def translate_where_tokens(self, where_tokens: list[str]) -> WhereClause:
        # interval_conditions = []
        pass

    def translate_updating_tokens(self, updating_tokens: list[str]) -> UpdatingClause:
        pass

    def translate_with_tokens(self, with_tokens: list[str]) -> WithClause:
        pass


