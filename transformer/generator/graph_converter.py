from transformer.generator.expression_converter import ExpressionConverter
from transformer.generator.utils import convert_dict_to_str
from transformer.generator.variables_manager import VariablesManager
from transformer.ir.s_cypher_clause import AtTimeClause, BetweenClause
from transformer.ir.s_graph import *


class GraphConverter:
    def __init__(self, variables_manager: VariablesManager, expression_converter: ExpressionConverter):
        self.variables_manager = variables_manager
        self.expression_converter = expression_converter

    def match_path(self, path: SPath, time_window: AtTimeClause | BetweenClause = None) -> (str, List[str], List[str]):
        # 路径模式，属性节点和值节点的模式，路径有效时间限制
        path_pattern, property_patterns, node_time_window_info = self.match_object_node(path.nodes[0], time_window)
        path_time_window_info = node_time_window_info
        for index, relationship in enumerate(path.relationships):
            # 生成关系模式
            relationship_pattern, relationship_time_window_info = self.match_relationship(relationship, time_window)
            path_pattern = path_pattern + relationship_pattern
            path_time_window_info.update(relationship_time_window_info)
            # 生成节点模式
            node_pattern, node_property_patterns, node_time_window_info = self.match_object_node(path.nodes[index + 1],
                                                                                                 time_window)
            path_pattern = path_pattern + node_pattern
            property_patterns.extend(node_property_patterns)
            path_time_window_info.update(node_time_window_info)

        if path.variable:
            path_pattern = path.variable + " = " + path_pattern
        return path_pattern, property_patterns, path_time_window_info

    def match_object_node(self, object_node: ObjectNode, time_window: AtTimeClause | BetweenClause = None) -> (
            str, List[str], dict[str, str]):
        # 对象节点模式, 对象节点的有效时间限制
        object_pattern, object_time_window_info = self.match_node(object_node, time_window)
        node_time_window_info = object_time_window_info

        # 对象节点属性模式
        property_patterns = []
        for property_node, value_node in object_node.properties.items():
            property_pattern, property_time_window_info = self.match_node(property_node, time_window)
            value_pattern, value_time_window_info = self.match_node(value_node, time_window)
            property_patterns.append(
                '(' + object_node.variable + ")-[:OBJECT_PROPERTY]->" + property_pattern + "-[:PROPERTY_VALUE]->" + value_pattern)
            # 属性节点的有效时间限制
            node_time_window_info.update(property_time_window_info)
            # 值节点的有效时间限制
            node_time_window_info.update(value_time_window_info)

        return object_pattern, property_patterns, node_time_window_info

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
        node_time_window_info = {}
        if node.time_window is not None:
            node_time_window_info = {node.variable: self.expression_converter.convert_at_t_element(node.time_window)}
        elif time_window is not None:
            node_time_window_info = {node.variable: None}

        return node_pattern, node_time_window_info

    def match_relationship(self, relationship: SRelationship, time_window: AtTimeClause | BetweenClause = None) -> (
    str, dict[str, str]):
        if relationship.variable is None:
            relationship.variable = self.variables_manager.get_random_variable()
        # 关系模式
        relationship_pattern = relationship.variable
        for label in relationship.labels:
            relationship_pattern = relationship_pattern + ':' + label
        if relationship.length[0] != 1 or relationship.length[1] != 1:
            relationship_pattern = relationship_pattern + '*'
            if relationship.length[0] is not None or relationship.length[1] is not None:
                if relationship.length[0] == relationship.length[1]:
                    relationship_pattern = relationship_pattern + str(relationship.length[0])
                else:
                    if relationship.length[0]:
                        relationship_pattern = relationship_pattern + str(relationship.length[0])
                    relationship_pattern = relationship_pattern + ".."
                    if relationship.length[1]:
                        relationship_pattern = relationship_pattern + str(relationship.length[1])
        if len(relationship.properties) != 0:
            relationship_pattern = relationship_pattern + '{'
            for index, (property_name, property_value) in enumerate(relationship.properties.items()):
                if index != 0:
                    relationship_pattern = relationship_pattern + ", "
                property_value_string = self.expression_converter.convert_expression(property_value)
                relationship_pattern = relationship_pattern + property_name + " : " + property_value_string
            relationship_pattern = relationship_pattern + '}'
        if relationship_pattern != "":
            relationship_pattern = "-[" + relationship_pattern + "]-"
        else:
            relationship_pattern = '-' + relationship_pattern + '-'
        if relationship.direction == SRelationship.LEFT:
            relationship_pattern = '<' + relationship_pattern
        elif relationship.direction == SRelationship.RIGHT:
            relationship_pattern = relationship_pattern + '>'

        # 关系的有效时间限制
        relationship_time_window_info = {}
        if relationship.time_window is not None:
            relationship_time_window_info = {relationship.variable: self.expression_converter.convert_at_t_element(relationship.time_window)}
        elif time_window is not None:
            relationship_time_window_info = {relationship.variable: None}

        return relationship_pattern, relationship_time_window_info

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
        for index, relationship in enumerate(path.relationships):
            if path.nodes[index + 1].variable is None:
                path.nodes[index + 1].variable = self.variables_manager.get_random_variable()
            if relationship.variable is None:
                relationship.variable = self.variables_manager.get_random_variable()
            object_node_pattern, property_node_patterns, value_node_patterns = self.create_object_node(
                path.nodes[index + 1], time_window)
            all_object_node_pattern.append(object_node_pattern)
            all_property_node_patterns.extend(property_node_patterns)
            all_value_node_patterns.extend(value_node_patterns)
            relationship_pattern = self.create_relationship(relationship, path.nodes[index], path.nodes[index + 1], time_window)
            path_pattern = path_pattern + relationship_pattern + '(' + path.nodes[index + 1].variable + ')'
        if path.variable:
            path_pattern = path.variable + " = " + path_pattern
        return all_object_node_pattern, all_property_node_patterns, all_value_node_patterns, path_pattern

    def create_object_node(self, object_node: ObjectNode, time_window: Expression = None) -> (
            str, List[str], List[str]):
        property_node_patterns, value_node_patterns = [], []
        if object_node.variable in self.variables_manager.updating_variables:
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
                raise SyntaxError("Variable `" + object_node.variable + "` already declared")
            object_node_pattern = '(' + object_node.variable + ')'
        return object_node_pattern, property_node_patterns, value_node_patterns

    def create_node(self, node: SNode, time_window: AtTimeClause = None, parent_node: SNode = None) -> str:
        if node.variable is None:
            node.variable = self.variables_manager.get_random_variable()
        node_pattern = node.variable
        # 添加节点标签
        for label in node.labels:
            node_pattern = node_pattern + ':' + label
        # 添加节点内容
        if node.__class__ == PropertyNode:
            node_pattern = node_pattern + "{content: \"" + node.content + "\""
        elif node.__class__ == ValueNode:
            node_pattern = node_pattern + "{content: " + self.expression_converter.convert_expression(node.content)
        # 添加节点有效时间
        if node.time_window:
            interval_from_string = "scypher.timePoint(" + self.expression_converter.convert_time_point_literal(
                node.time_window.interval_from) + ')'
            interval_to_string = "scypher.timePoint(" + self.expression_converter.convert_time_point_literal(
                node.time_window.interval_to) + ')'
        elif time_window:
            interval_from_string = self.expression_converter.convert_expression(time_window.time_point)
            interval_to_string = "scypher.timePoint(\"NOW\")"
        else:
            interval_from_string = "scypher.operateTime()"
            interval_to_string = "scypher.timePoint(\"NOW\")"
        if node.__class__ == ObjectNode:
            node_pattern = node_pattern + "{intervalFrom: " + interval_from_string + ", intervalTo: " + interval_to_string + "}"
        elif node.__class__ in [PropertyNode, ValueNode]:
            # 调用函数检查属性节点和值节点的有效时间是否满足约束
            node_pattern = node_pattern + "{intervalFrom: scypher.getIntervalFromOfSubordinateNode(" + parent_node.variable + ", " + interval_from_string + "), "
            node_pattern = node_pattern + "intervalTo: scypher.getIntervalToOfSubordinateNode(" + parent_node.variable + ", " + interval_to_string + ")}"

        node_pattern = '(' + node_pattern + ')'
        return node_pattern

    def create_relationship(self, relationship: SRelationship, from_node: ObjectNode = None, to_node: ObjectNode = None,
                            time_window: AtTimeClause = None) -> str:
        if len(relationship.labels) == 0:
            raise SyntaxError(
                "Exactly one relationship type must be specified for CREATE. Did you forget to prefix your relationship type with a ':'?")
        if relationship.variable:
            relationship_pattern = relationship.variable
        else:
            relationship_pattern = ""
        # 添加关系的标签
        for label in relationship.labels:
            relationship_pattern = relationship_pattern + ':' + label
        # 添加关系的属性
        relationship_pattern = relationship_pattern + '{'
        for property_key, property_value in relationship.properties.items():
            relationship_pattern = relationship_pattern + property_key + ": " + self.expression_converter.convert_expression(
                property_value) + ", "
        # 用于检查关系的有效时间是否符合约束，以及是否有重复关系
        relationship_info = {"labels": relationship.labels, "properties": list(relationship.properties.keys())}
        if relationship.time_window:
            interval_from_string = "scypher.timePoint(" + self.expression_converter.convert_time_point_literal(
                relationship.time_window.interval_from) + ')'
            interval_to_string = "scypher.timePoint(" + self.expression_converter.convert_time_point_literal(
                relationship.time_window.interval_to) + ')'
        elif time_window:
            interval_from_string = self.expression_converter.convert_expression(time_window.time_point)
            interval_to_string = "scypher.timePoint(\"NOW\")"
        else:
            interval_from_string = "scypher.operateTime()"
            interval_to_string = "scypher.timePoint(\"NOW\")"
        relationship_pattern = relationship_pattern + "intervalFrom: scypher.getIntervalFromOfRelationship(" + from_node.variable + ", " + to_node.variable + ", " + convert_dict_to_str(
            relationship_info) + ", " + interval_from_string + "), "
        relationship_pattern = relationship_pattern + "intervalTo: scypher.getIntervalToOfRelationship(" + from_node.variable + ", " + to_node.variable + ", " + convert_dict_to_str(
            relationship_info) + ", " + interval_to_string + ")}"

        relationship_pattern = '-[' + relationship_pattern + ']-'
        if relationship.direction == SRelationship.LEFT:
            relationship_pattern = '<' + relationship_pattern
        elif relationship.direction == SRelationship.RIGHT:
            relationship_pattern = relationship_pattern + '>'

        return relationship_pattern
