from transformer.generator.clause_converter import ClauseConverter
from transformer.generator.expression_converter import ExpressionConverter
from transformer.generator.graph_converter import GraphConverter
from transformer.generator.variables_manager import VariablesManager
from transformer.ir.s_cypher_clause import *


class CypherGenerator:

    def generate_cypher_query(self, s_cypher_clause: SCypherClause) -> str:
        variables_manager = VariablesManager()
        graph_converter = GraphConverter()
        expression_converter = ExpressionConverter()
        clause_converter = ClauseConverter()

        variables_manager.expression_converter = expression_converter

        graph_converter.variables_manager = variables_manager
        graph_converter.expression_converter = expression_converter

        expression_converter.variables_manager = variables_manager
        expression_converter.graph_converter = graph_converter
        expression_converter.clause_converter = clause_converter

        clause_converter.variables_manager = variables_manager
        clause_converter.graph_converter = graph_converter
        clause_converter.expression_converter = expression_converter

        query_clause_string = clause_converter.convert_s_cypher_clause(s_cypher_clause)
        return query_clause_string
