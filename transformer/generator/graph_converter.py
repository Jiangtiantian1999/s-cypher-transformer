from transformer.generator.utils import convert_dict_to_str
from transformer.ir.s_cypher_clause import AtTimeClause, BetweenClause
from transformer.ir.s_graph import *


class GraphConverter:
    def __init__(self):
        self.variables_manager = None
        self.expression_converter = None

    def match_path(self, path: SPath, time_window: AtTimeClause | BetweenClause = None) -> (str, List[str], List[str]):
        # 路径模式，属性节点和值节点的模式，路径有效时间限制
        path_pattern, property_patterns, node_interval_info = self.match_object_node(path.nodes[0], time_window)
        path_interval_info = node_interval_info
        for index, edge in enumerate(path.edges):
            # 生成边模式
            edge_pattern, edge_interval_info = self.match_edge(edge, time_window)
            path_pattern = path_pattern + edge_pattern
            path_interval_info.update(edge_interval_info)
            # 生成节点模式
            node_pattern, node_property_patterns, node_interval_info = self.match_object_node(path.nodes[index + 1],
                                                                                              time_window)
            path_pattern = path_pattern + node_pattern
            property_patterns.extend(node_property_patterns)
            path_interval_info.update(node_interval_info)

        if path.variable:
            path_pattern = path.variable + " = " + path_pattern
        return path_pattern, property_patterns, path_interval_info

    def match_object_node(self, object_node: ObjectNode, time_window: AtTimeClause | BetweenClause = None) -> (
            str, List[str], dict[str, str]):
        # 对象节点模式, 对象节点的有效时间限制
        object_pattern, object_interval_info = self.match_node(object_node, time_window)
        node_interval_info = object_interval_info

        # 对象节点属性模式
        property_patterns = []
        for property_node, value_node in object_node.properties.items():
            property_pattern, property_interval_info = self.match_node(property_node, time_window)
            value_pattern, value_interval_info = self.match_node(value_node, time_window)
            property_patterns.append(
                '(' + object_node.variable + ")-[:OBJECT_PROPERTY]->" + property_pattern + "-[:PROPERTY_VALUE]->" + value_pattern)
            # 属性节点的有效时间限制
            node_interval_info.update(property_interval_info)
            # 值节点的有效时间限制
            node_interval_info.update(value_interval_info)

        return object_pattern, property_patterns, node_interval_info

    def match_node(self, node: SNode, time_window: AtTimeClause | BetweenClause = None) -> (str, dict[str, str]):
        if node.variable is None:
            node.variable = self.variables_manager.get_random_variable()
        node_pattern = node.variable
        for label in node.labels:
            node_pattern = node_pattern + ':' + label
        if node.__class__ == PropertyNode:
            node_pattern = node_pattern + "{content: \"" + node.content + "\"}"
        elif node.__class__ == ValueNode:
            node_pattern = node_pattern + "{content: " + self.expression_converter.convert_expression(
                node.content) + '}'
        node_pattern = '(' + node_pattern + ')'

        # 节点的有效时间限制
        node_interval_info = {}
        if node.interval is not None:
            interval_from_string = self.convert_time_point_literal(node.interval.interval_from)
            interval_to_string = self.convert_time_point_literal(node.interval.interval_to)
            node_interval_info = {
                node.variable: "scypher.interval(" + interval_from_string + ", " + interval_to_string + ')'}
        elif time_window is not None:
            node_interval_info = {node.variable: None}

        return node_pattern, node_interval_info

    def match_edge(self, edge: SEdge, time_window: AtTimeClause | BetweenClause = None) -> (str, dict[str, str]):
        if edge.variable is None:
            edge.variable = self.variables_manager.get_random_variable()
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
            for index, (property_name, property_value) in enumerate(edge.properties.items()):
                if index != 0:
                    edge_pattern = edge_pattern + ", "
                property_value_string = self.expression_converter.convert_expression(property_value)
                edge_pattern = edge_pattern + property_name + " : " + property_value_string
            edge_pattern = edge_pattern + '}'
        if edge_pattern != "":
            edge_pattern = "-[" + edge_pattern + "]-"
        else:
            edge_pattern = '-' + edge_pattern + '-'
        if edge.direction == edge.LEFT:
            edge_pattern = '<' + edge_pattern
        elif edge.direction == edge.RIGHT:
            edge_pattern = edge_pattern + '>'

        # 边的有效时间限制
        edge_interval_info = {}
        if edge.interval is not None:
            interval_from_string = self.convert_time_point_literal(edge.interval.interval_from)
            interval_to_string = self.convert_time_point_literal(edge.interval.interval_to)
            edge_interval_info = {
                edge.variable: "scypher.interval(" + interval_from_string + ", " + interval_to_string + ')'}
        elif time_window is not None:
            edge_interval_info = {edge.variable: None}

        return edge_pattern, edge_interval_info

    def create_path(self, path: SPath, time_window: AtTimeClause = None) -> (List[str], List[str], List[str], str):
        # 路径模式，属性节点和值节点的模式
        if path.nodes[0].variable is None and path.variable or len(path.nodes) > 1:
            path.nodes[0].variable = self.variables_manager.get_random_variable()
        if path.variable or len(path.nodes) > 1:
            path_pattern = '(' + path.nodes[0].variable + ')'
        else:
            path_pattern = None
        all_object_node_pattern, all_property_node_patterns, all_value_node_patterns = [], [], []
        object_node_pattern, property_node_patterns, value_node_patterns = self.create_object_node(path.nodes[0],
                                                                                                   time_window)
        all_object_node_pattern.append(object_node_pattern)
        all_property_node_patterns.extend(property_node_patterns)
        all_value_node_patterns.extend(value_node_patterns)
        for index, edge in enumerate(path.edges):
            if path.nodes[index + 1].variable is None:
                path.nodes[index + 1].variable = self.variables_manager.get_random_variable()
            if edge.variable is None:
                edge.variable = self.variables_manager.get_random_variable()
            object_node_pattern, property_node_patterns, value_node_patterns = self.create_object_node(
                path.nodes[index + 1], time_window)
            all_object_node_pattern.append(object_node_pattern)
            all_property_node_patterns.extend(property_node_patterns)
            all_value_node_patterns.extend(value_node_patterns)
            edge_pattern = self.create_edge(edge, path.nodes[index], path.nodes[index + 1], time_window)
            path_pattern = path_pattern + edge_pattern + '(' + path.nodes[index + 1].variable + ')'
        if path.variable:
            path_pattern = path.variable + " = " + path_pattern
        return all_object_node_pattern, all_property_node_patterns, all_value_node_patterns, path_pattern

    def create_object_node(self, object_node: ObjectNode, time_window: Expression = None) -> (
            str, List[str], List[str]):
        property_node_patterns, value_node_patterns = [], []
        if object_node.variable in self.variables_manager.updating_object_nodes_dict.keys():
            # 该对象节点是在更新语句中定义的，直接创建属性节点和值节点（和相连边）即可
            object_node_pattern = self.create_node(object_node, None, time_window)
            for property_node, value_node in object_node.properties.items():
                property_pattern = self.create_node(property_node, time_window, object_node)
                property_node_patterns.append('(' + object_node.variable + ")-[:OBJECT_PROPERTY]->" + property_pattern)
                value_pattern = self.create_node(value_node, time_window, object_node)
                value_node_patterns.append('(' + property_node.variable + ")-[:PROPERTY_VALUE]->" + value_pattern)
        else:
            # 该对象节点是在查询语句中定义的，在更新语句中调用时不能设置其标签或属性
            if len(object_node.labels) > 1 or len(object_node.properties) > 0:
                raise ValueError("Variable `" + object_node.variable + "` already declared.")
            object_node_pattern = '(' + object_node.variable + ')'
        return object_node_pattern, property_node_patterns, value_node_patterns

    def create_node(self, node: SNode, time_window: AtTimeClause = None, parent_node: SNode = None) -> str:
        if node.variable is None and (
                node.__class__ == PropertyNode or (node.__class__ == ObjectNode and len(node.properties) > 0)):
            node.variable = self.variables_manager.get_random_variable()
        if node.variable:
            node_pattern = node.variable
        else:
            node_pattern = ""
        # 添加节点标签
        for label in node.labels:
            node_pattern = node_pattern + ':' + label
        # 添加节点内容
        if node.__class__ == PropertyNode:
            node_pattern = node_pattern + "{content: \"" + node.content + "\""
        elif node.__class__ == ValueNode:
            node_pattern = node_pattern + "{content: " + self.expression_converter.convert_expression(node.content)
        # 添加节点有效时间
        if node.__class__ == ObjectNode:
            if node.interval:
                interval_from_string = "scypher.timePoint(" + self.convert_time_point_literal(
                    node.interval.interval_from) + ')'
                interval_to_string = "scypher.timePoint(" + self.convert_time_point_literal(
                    node.interval.interval_to) + ')'
            elif time_window:
                interval_from_string = self.expression_converter.convert_expression(time_window.time_point)
                interval_to_string = "scypher.timePoint(\"NOW\")"
            else:
                interval_from_string = "scypher.timePoint()"
                interval_to_string = "scypher.timePoint(\"NOW\")"
            node_pattern = node_pattern + "{intervalFrom: " + interval_from_string + ", intervalTo: " + interval_to_string + "}"
        elif node.__class__ in [PropertyNode, ValueNode]:
            if node.interval:
                interval_from_string = self.convert_time_point_literal(node.interval.interval_from)
                interval_to_string = self.convert_time_point_literal(node.interval.interval_to)
            elif time_window:
                interval_from_string = self.expression_converter.convert_expression(time_window.time_point)
                interval_to_string = "\"NOW\""
            else:
                interval_from_string = "NULL"
                interval_to_string = "\"NOW\""
            node_pattern = node_pattern + "{intervalFrom: scypher.getIntervalFromOfSubordinateNode(" + parent_node.variable + ", " + interval_from_string + "), "
            node_pattern = node_pattern + "intervalTo: scypher.getIntervalToOfSubordinateNode(" + parent_node.variable + ", " + interval_to_string + ")}"

        node_pattern = '(' + node_pattern + ')'
        return node_pattern

    def create_edge(self, edge: SEdge, from_node: ObjectNode = None, to_node: ObjectNode = None,
                    time_window: AtTimeClause = None) -> str:
        if len(edge.labels) == 0:
            raise SyntaxError(
                "Exactly one relationship type must be specified for CREATE. Did you forget to prefix your relationship type with a ':'?")
        if edge.variable:
            edge_pattern = edge.variable
        else:
            edge_pattern = ""
        # 添加边标签
        for label in edge.labels:
            edge_pattern = edge_pattern + ':' + label
        # 添加边属性
        edge_pattern = edge_pattern + '{'
        for key, value in edge.properties.items():
            edge_pattern = edge_pattern + key + ": " + self.expression_converter.convert_expression(value) + ", "
        # 需要检查边的有效时间，以及是否有重复边
        edge_info = {"labels": edge.labels, "properties": list(edge.properties.keys())}
        if edge.interval:
            interval_from_string = self.convert_time_point_literal(edge.interval.interval_from)
            interval_to_string = self.convert_time_point_literal(edge.interval.interval_to)
        elif time_window:
            interval_from_string = self.expression_converter.convert_expression(time_window.time_point)
            interval_to_string = "\"NOW\""
        else:
            interval_from_string = "NULL"
            interval_to_string = "\"NOW\""
        edge_pattern = edge_pattern + "intervalFrom: scypher.getIntervalFromOfEdge(" + from_node.variable + ", " + to_node.variable + ", " + convert_dict_to_str(
            edge_info) + ", " + interval_from_string + "), "
        edge_pattern = edge_pattern + "intervalTo: scypher.getIntervalToOfEdge(" + from_node.variable + ", " + to_node.variable + ", " + convert_dict_to_str(
            edge_info) + ", " + interval_to_string + ")}"

        edge_pattern = '-[' + edge_pattern + ']-'
        if edge.direction == edge.LEFT:
            edge_pattern = '<' + edge_pattern
        elif edge.direction == edge.RIGHT:
            edge_pattern = edge_pattern + '>'

        return edge_pattern

    def convert_time_point_literal(self, time_point_literal: TimePointLiteral) -> str:
        time_point = time_point_literal.time_point
        if time_point.__class__ == str:
            return '\"' + time_point + '\"'
        else:
            return self.expression_converter.convert_map_literal(time_point, None)
