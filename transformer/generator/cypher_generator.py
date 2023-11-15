from transformer.generator.clause_converter import ClauseConverter
from transformer.generator.expression_converter import ExpressionConverter
from transformer.generator.graph_converter import GraphConverter
from transformer.generator.variables_manager import VariablesManager
from transformer.ir.s_cypher_clause import *


class CypherGenerator:

    @staticmethod
    def generate_cypher_query(s_cypher_clause: SCypherClause) -> str:
        variables_manager = VariablesManager()
        expression_converter = ExpressionConverter(variables_manager)
        graph_converter = GraphConverter(variables_manager, expression_converter)
        clause_converter = ClauseConverter(variables_manager, expression_converter, graph_converter)

        query_clause_string = clause_converter.convert_s_cypher_clause(s_cypher_clause)
        return query_clause_string
