from transformer.generator.expression_converter import ExpressionConverter
from transformer.generator.variables_manager import VariablesManager
from transformer.ir.s_cypher_clause import AtTimeClause, BetweenClause
from transformer.ir.s_graph import *


class GraphConverter:

    @staticmethod
    def convert_path(path: SPath, time_window: AtTimeClause | BetweenClause = None,
                     variables_manager: VariablesManager = None) -> (
            str, List[str], List[str]):
        # 路径模式，属性节点和值节点的模式，路径有效时间限制
        path_pattern, property_patterns, interval_conditions = GraphConverter.convert_object_node(path.nodes[0],
                                                                                                  time_window,
                                                                                                  variables_manager)
        index = 1
        while index < len(path.nodes):
            # 生成边模式
            edge_pattern, edge_interval_condition = GraphConverter.convert_edge(path.edges[index - 1], time_window,
                                                                                variables_manager)
            path_pattern = path_pattern + edge_pattern
            interval_conditions.append(edge_interval_condition)
            # 生成节点模式
            node_pattern, node_property_patterns, node_interval_conditions = GraphConverter.convert_object_node(
                path.nodes[index], time_window, variables_manager)
            path_pattern = path_pattern + node_pattern
            property_patterns.extend(node_property_patterns)
            interval_conditions.extend(node_interval_conditions)

            index = index + 1
        if path.variable:
            path_pattern = path.variable + " = " + path_pattern
        return path_pattern, property_patterns, interval_conditions

    @staticmethod
    def convert_object_node(object_node: ObjectNode, time_window: Expression = None,
                            variables_manager: VariablesManager = None) -> (
            str, List[str], List[str]):
        # 对象节点模式, 对象节点的有效时间限制
        object_pattern, object_interval_condition = GraphConverter.convert_node(object_node, time_window,
                                                                                variables_manager)
        interval_conditions = [object_interval_condition]

        # 对象节点属性模式
        property_patterns = []
        for key, value in object_node.properties.items():
            property_pattern, property_interval_condition = GraphConverter.convert_node(key, time_window,
                                                                                        variables_manager)
            value_pattern, value_interval_condition = GraphConverter.convert_node(value, time_window, variables_manager)
            property_patterns.append(
                object_pattern + "-[:OBJECT_PROPERTY]->" + property_pattern + "-[:PROPERTY_VALUE]->" + value_pattern)
            # 属性节点的有效时间限制
            interval_conditions.append(property_interval_condition)
            # 值节点的有效时间限制
            interval_conditions.append(value_interval_condition)

        return object_pattern, property_patterns, interval_conditions

    @staticmethod
    def convert_node(node: SNode, time_window: AtTimeClause | BetweenClause = None,
                     variables_manager: VariablesManager = None) -> (str, List[str]):
        if node.variable is None:
            if variables_manager is not None:
                node.variable = variables_manager.get_random_variable()
                variables_manager.variables_dict[node.variable] = node
            else:
                raise RuntimeError("Missing variables manager.")
        node_pattern = ""
        if node.variable:
            node_pattern = node.variable
        for label in node.labels:
            node_pattern = node_pattern + ':' + label
        if node.__class__ == PropertyNode:
            node_pattern = node_pattern + "{content: \"" + node.content + "\"}"
        elif node.__class__ == ValueNode:
            value_expression_string, value_expression_type = ExpressionConverter.convert_expression(node.content,
                                                                                                    variables_manager)
            node_pattern = node_pattern + "{content: " + value_expression_string + "}"
        node_pattern = '(' + node_pattern + ')'

        # 节点的有效时间限制
        if node.interval is not None:
            interval_from_string = GraphConverter.convert_time_point_literal(node.interval.interval_from)
            interval_to_string = GraphConverter.convert_time_point_literal(node.interval.interval_to)
            interval_condition = "scypher.limitInterval(" + node.variable + ", scypher.interval(" + interval_from_string + ", " + interval_to_string + "))"
        elif time_window is not None:
            if time_window.__class__ == AtTimeClause:
                time_window = time_window.time_point
            elif time_window.__class__ == BetweenClause:
                time_window = time_window.interval
            time_window_string, time_window_type = ExpressionConverter.convert_expression(time_window,
                                                                                          variables_manager)
            interval_condition = "scypher.limitInterval(" + node.variable + ", " + time_window_string + ")"
        else:
            interval_condition = "scypher.limitInterval(" + node.variable + ", null)"

        return node_pattern, interval_condition

    @staticmethod
    def convert_edge(edge: SEdge, time_window: AtTimeClause | BetweenClause = None,
                     variables_manager: VariablesManager = None) -> (
            str, List[str]):
        if edge.variable is None:
            if variables_manager is not None:
                edge.variable = variables_manager.get_random_variable()
            else:
                raise RuntimeError("Missing variables manager.")
        # 边模式
        edge_pattern = edge.variable
        for label in edge.labels:
            edge_pattern = edge_pattern + ':' + label
        if edge.length[0] != 1 or edge.length[1] != 1:
            edge_pattern = edge_pattern + '*'
            if edge.length[0] is not None or edge.length[1] is not None:
                if edge.length[0] == edge.length[1]:
                    edge_pattern = edge_pattern + str(edge.length[0])
                else:
                    if edge.length[0]:
                        edge_pattern = edge_pattern + str(edge.length[0])
                    edge_pattern = edge_pattern + ".."
                    if edge.length[1]:
                        edge_pattern = edge_pattern + str(edge.length[1])
        if len(edge.properties) != 0:
            edge_pattern = edge_pattern + '{'
            for index, (key, value) in enumerate(edge.properties.items()):
                if index != 0:
                    edge_pattern = edge_pattern + ", "
                edge_pattern = edge_pattern + key + " : " + str(value)
            edge_pattern = edge_pattern + '}'
        if edge.variable or edge.labels or edge.length[0] != 1 or edge.length[1] != 1 or edge.properties:
            edge_pattern = "-[" + edge_pattern + "]-"
        else:
            edge_pattern = '-' + edge_pattern + '-'
        if edge.direction == edge.LEFT:
            edge_pattern = '<' + edge_pattern
        elif edge.direction == edge.RIGHT:
            edge_pattern = edge_pattern + '>'

        # 边的有效时间限制
        if edge.interval is not None:
            interval_from_string = GraphConverter.convert_time_point_literal(edge.interval.interval_from)
            interval_to_string = GraphConverter.convert_time_point_literal(edge.interval.interval_to)
            interval_condition = "scypher.limitInterval(" + edge.variable + ", scypher.interval(" + interval_from_string + ", " + interval_to_string + "))"
        elif time_window is not None:
            if time_window.__class__ == AtTimeClause:
                time_window = time_window.time_point
            elif time_window.__class__ == BetweenClause:
                time_window = time_window.interval
            time_window_string, time_window_type = ExpressionConverter.convert_expression(time_window,
                                                                                          variables_manager)
            interval_condition = "scypher.limitInterval(" + edge.variable + ", " + time_window_string + ')'
        else:
            interval_condition = "scypher.limitInterval(" + edge.variable + ", null)"

        return edge_pattern, interval_condition

    @staticmethod
    def convert_time_point_literal(time_point_literal: TimePointLiteral) -> str:
        time_point = time_point_literal.time_point
        if time_point.__class__ == str:
            return '\"' + time_point + '\"'
        else:
            time_point_string, time_point_type = ExpressionConverter.convert_map_literal(time_point, None)
            return time_point_string
