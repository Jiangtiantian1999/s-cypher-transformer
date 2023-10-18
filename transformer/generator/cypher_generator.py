from transformer.generator.clause_converter import ClauseConverter
from transformer.generator.variables_manager import VariablesManager
from transformer.ir.s_cypher_clause import *


class CypherGenerator:

    def generate_cypher_query(self, s_cypher_clause: SCypherClause) -> str:
        variables_manager = VariablesManager()
        query_clause = s_cypher_clause.query_clause
        if query_clause.__class__ == UnionQueryClause:
            return ClauseConverter.convert_union_query_clause(query_clause, variables_manager)
        elif query_clause.__class__ == CallClause:
            return ClauseConverter.convert_call_clause(query_clause, variables_manager)
        elif query_clause.__class__ == TimeWindowLimitClause:
            return ClauseConverter.convert_time_window_limit_clause(query_clause)
