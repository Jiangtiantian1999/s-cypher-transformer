from transformer.ir.s_cypher_clause import AtTimeClause, BetweenClause
from transformer.ir.s_graph import *


class GraphConverter:
    def __init__(self):
        self.variables_manager = None
        self.expression_converter = None

    def convert_path(self, path: SPath, time_window: AtTimeClause | BetweenClause = None) -> (
            str, List[str], List[str]):
        # 路径模式，属性节点和值节点的模式，路径有效时间限制
        path_pattern, property_patterns, interval_conditions = self.convert_object_node(path.nodes[0], time_window)
        index = 1
        while index < len(path.nodes):
            # 生成边模式
            edge_pattern, edge_interval_condition = self.convert_edge(path.edges[index - 1], time_window)
            path_pattern = path_pattern + edge_pattern
            interval_conditions.append(edge_interval_condition)
            # 生成节点模式
            node_pattern, node_property_patterns, node_interval_conditions = self.convert_object_node(
                path.nodes[index], time_window)
            path_pattern = path_pattern + node_pattern
            property_patterns.extend(node_property_patterns)
            interval_conditions.extend(node_interval_conditions)

            index = index + 1
        if path.variable:
            path_pattern = path.variable + " = " + path_pattern
        return path_pattern, property_patterns, interval_conditions

    def convert_object_node(self, object_node: ObjectNode, time_window: Expression = None) -> (
            str, List[str], List[str]):
        # 对象节点模式, 对象节点的有效时间限制
        object_pattern, object_interval_condition = self.convert_node(object_node, time_window)
        interval_conditions = [object_interval_condition]

        # 对象节点属性模式
        property_patterns = []
        for key, value in object_node.properties.items():
            property_pattern, property_interval_condition = self.convert_node(key, time_window)
            value_pattern, value_interval_condition = self.convert_node(value, time_window)
            property_patterns.append(
                object_pattern + "-[:OBJECT_PROPERTY]->" + property_pattern + "-[:PROPERTY_VALUE]->" + value_pattern)
            # 属性节点的有效时间限制
            interval_conditions.append(property_interval_condition)
            # 值节点的有效时间限制
            interval_conditions.append(value_interval_condition)

        return object_pattern, property_patterns, interval_conditions

    def convert_node(self, node: SNode, time_window: AtTimeClause | BetweenClause = None) -> (str, List[str]):
        if node.variable is None:
            node.variable = self.variables_manager.get_random_variable()
            self.variables_manager.variables_dict[node.variable] = node
        node_pattern = ""
        if node.variable:
            node_pattern = node.variable
        for label in node.labels:
            node_pattern = node_pattern + ':' + label
        if node.__class__ == PropertyNode:
            node_pattern = node_pattern + "{content: \"" + node.content + "\"}"
        elif node.__class__ == ValueNode:
            node_pattern = node_pattern + "{content: " + self.expression_converter.convert_expression(
                node.content) + "}"
        node_pattern = '(' + node_pattern + ')'

        # 节点的有效时间限制
        if node.interval is not None:
            interval_from_string = self.convert_time_point_literal(node.interval.interval_from)
            interval_to_string = self.convert_time_point_literal(node.interval.interval_to)
            interval_condition = "scypher.limitInterval(" + node.variable + ", scypher.interval(" + interval_from_string + ", " + interval_to_string + "))"
        elif time_window is not None:
            if time_window.__class__ == AtTimeClause:
                time_window = time_window.time_point
            elif time_window.__class__ == BetweenClause:
                time_window = time_window.interval
            node.time_window = time_window
            interval_condition = "scypher.limitInterval(" + node.variable + ", " + self.expression_converter.convert_expression(
                time_window) + ')'
        else:
            interval_condition = "scypher.limitInterval(" + node.variable + ", null)"

        return node_pattern, interval_condition

    def convert_edge(self, edge: SEdge, time_window: AtTimeClause | BetweenClause = None) -> (str, List[str]):
        if edge.variable is None:
            if self.variables_manager is not None:
                edge.variable = self.variables_manager.get_random_variable()
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
            interval_from_string = self.convert_time_point_literal(edge.interval.interval_from)
            interval_to_string = self.convert_time_point_literal(edge.interval.interval_to)
            interval_condition = "scypher.limitInterval(" + edge.variable + ", scypher.interval(" + interval_from_string + ", " + interval_to_string + "))"
        elif time_window is not None:
            if time_window.__class__ == AtTimeClause:
                time_window = time_window.time_point
            elif time_window.__class__ == BetweenClause:
                time_window = time_window.interval
            time_window_string, time_window_type = self.expression_converter.convert_expression(time_window)
            interval_condition = "scypher.limitInterval(" + edge.variable + ", " + time_window_string + ')'
        else:
            interval_condition = "scypher.limitInterval(" + edge.variable + ", null)"

        return edge_pattern, interval_condition

    def convert_time_point_literal(self, time_point_literal: TimePointLiteral) -> str:
        time_point = time_point_literal.time_point
        if time_point.__class__ == str:
            return '\"' + time_point + '\"'
        else:
            time_point_string, time_point_type = self.expression_converter.convert_map_literal(time_point, None)
            return time_point_string
