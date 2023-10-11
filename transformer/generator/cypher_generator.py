from transformer.generator.clause_converter import ClauseConverter
from transformer.ir.s_cypher_clause import *


class CypherGenerator:
    clause_converter = None

    def generate_cypher_query(self, s_cypher_clause: SCypherClause) -> str:
        self.clause_converter = ClauseConverter()
        if s_cypher_clause.query_clause.__class__ == UnionQueryClause:
            return self.clause_converter.convert_union_query_clause(s_cypher_clause.query_clause)
        elif s_cypher_clause.query_clause.__class__ == CallClause:
            return self.clause_converter.convert_call_clause(s_cypher_clause.query_clause)
        elif s_cypher_clause.query_clause.__class__ == TimeWindowLimitClause:
            return self.clause_converter.convert_time_window_limit_clause(s_cypher_clause.query_clause)
