from transformer.generator.expression_converter import ExpressionConverter
from transformer.generator.variables_manager import VariablesManager
from transformer.ir.s_cypher_clause import AtTimeClause, BetweenClause
from transformer.ir.s_graph import *


class GraphConverter:
    def __init__(self, variables_manager: VariablesManager, expression_converter: ExpressionConverter):
        self.variables_manager = variables_manager
        self.expression_converter = expression_converter

    def match_path(self, path: SPath, time_window: AtTimeClause | BetweenClause = None) -> (str, List[str], list):
        # 路径模式，属性节点和值节点的模式，路径有效时间限制
        path_pattern, property_patterns, path_time_window_info = self.match_object_node(path.nodes[0], time_window)
        for index, relationship in enumerate(path.relationships):
            # 生成关系模式
            relationship_pattern, relationship_time_window_info = self.match_relationship(relationship, time_window)
            path_pattern = path_pattern + relationship_pattern
            if relationship_time_window_info:
                if path_time_window_info is None:
                    path_time_window_info = []
                path_time_window_info.append(relationship_time_window_info)
            # 生成节点模式
            node_pattern, node_property_patterns, node_time_window_info = self.match_object_node(path.nodes[index + 1],
                                                                                                 time_window)
            path_pattern = path_pattern + node_pattern
            property_patterns.extend(node_property_patterns)
            if node_time_window_info:
                if path_time_window_info is None:
                    path_time_window_info = []
                path_time_window_info.extend(node_time_window_info)

        if path.variable:
            path_pattern = path.variable + " = " + path_pattern

        return path_pattern, property_patterns, path_time_window_info

    def match_object_node(self, object_node: ObjectNode, time_window: AtTimeClause | BetweenClause = None) -> (
            str, List[List[str]], list):
        # 对象节点模式, 对象节点的有效时间限制
        object_pattern, object_time_window_info = self.match_node(object_node, time_window)
        node_time_window_info = []
        if object_time_window_info:
            node_time_window_info.append(object_time_window_info)

        # 对象节点属性模式
        property_patterns = []
        for property_node, value_node in object_node.properties.items():
            property_pattern, property_time_window_info = self.match_node(property_node, time_window)
            value_pattern, value_time_window_info = self.match_node(value_node, time_window)
            property_patterns.append(
                '(' + object_node.variable + ")-[:OBJECT_PROPERTY]->" + property_pattern + "-[:PROPERTY_VALUE]->" + value_pattern)
            # 属性节点的有效时间限制
            if property_time_window_info:
                node_time_window_info.append(property_time_window_info)
            # 值节点的有效时间限制
            if value_time_window_info:
                node_time_window_info.append(value_time_window_info)
        if len(node_time_window_info) == 0:
            node_time_window_info = None
        return object_pattern, property_patterns, node_time_window_info

    def match_node(self, node: SNode, time_window: AtTimeClause | BetweenClause = None) -> (str, List[str]):
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
        node_time_window_info = None
        if node.__class__ == ObjectNode:
            if node.time_window:
                node_time_window_info = [node.variable,
                                         self.expression_converter.convert_at_t_element(node.time_window)]
            elif time_window:
                node_time_window_info = [node.variable, None]
        elif node.time_window:
            node_time_window_info = [node.variable, self.expression_converter.convert_at_t_element(node.time_window)]
        return node_pattern, node_time_window_info

    def match_relationship(self, relationship: SRelationship, time_window: AtTimeClause | BetweenClause = None) -> (
            str, List[str]):
        if relationship.variable is None:
            relationship.variable = self.variables_manager.get_random_variable()
        # 关系模式
        relationship_pattern = relationship.variable
        for index, label in enumerate(relationship.labels):
            if index == 0:
                relationship_pattern = relationship_pattern + ':'
            else:
                relationship_pattern = relationship_pattern + '|'
            relationship_pattern = relationship_pattern + label
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
        relationship_time_window_info = None
        if relationship.time_window is not None:
            relationship_time_window_info = [
                relationship.variable, self.expression_converter.convert_at_t_element(relationship.time_window)]
        elif time_window is not None:
            relationship_time_window_info = [relationship.variable, None]

        return relationship_pattern, relationship_time_window_info

    def create_path(self, path: SPath, time_window: AtTimeClause = None) -> (List[str], List[str], List[str], str):
        all_object_node_pattern, all_property_node_patterns, all_value_node_patterns = [], [], []
        for object_node in path.nodes:
            if object_node.variable in self.variables_manager.updating_variables.keys():
                # 该对象节点是在更新语句中定义的，需要创建对象节点、属性节点和值节点（和相连边），否则不需要创建，仅用于路径创建
                if self.variables_manager.updating_variables[object_node.variable] is False:
                    # 如果未创建过该对象节点
                    object_node_pattern, property_node_patterns, value_node_patterns = self.create_object_node(
                        path.nodes[0], time_window)
                    all_object_node_pattern.append(object_node_pattern)
                    all_property_node_patterns.extend(property_node_patterns)
                    all_value_node_patterns.extend(value_node_patterns)
                    self.variables_manager.updating_variables[object_node.variable] = True
                    self.variables_manager.updating_object_nodes[object_node.variable] = object_node
        if path.variable or len(path.nodes) > 1:
            # 如果设置了路径名，或对象节点多于1形成路径
            path_pattern = '(' + path.nodes[0].variable + ')'
            for index, relationship in enumerate(path.relationships):
                relationship_pattern = self.create_relationship(relationship, path.nodes[index], path.nodes[index + 1],
                                                                time_window)
                path_pattern = path_pattern + relationship_pattern + '(' + path.nodes[index + 1].variable + ')'
            if path.variable:
                path_pattern = path.variable + " = " + path_pattern
        else:
            path_pattern = None
        return all_object_node_pattern, all_property_node_patterns, all_value_node_patterns, path_pattern

    def create_object_node(self, object_node: ObjectNode, time_window: Expression = None) -> (
            str, List[str], List[str]):
        property_node_patterns, value_node_patterns = [], []
        object_node_pattern = self.create_node(object_node, time_window, None)
        for property_node, value_node in object_node.properties.items():
            property_pattern = self.create_node(property_node, time_window, object_node)
            property_node_patterns.append('(' + object_node.variable + ")-[:OBJECT_PROPERTY]->" + property_pattern)
            value_pattern = self.create_node(value_node, time_window, property_node)
            value_node_patterns.append('(' + property_node.variable + ")-[:PROPERTY_VALUE]->" + value_pattern)
        return object_node_pattern, property_node_patterns, value_node_patterns

    def create_node(self, node: SNode, time_window: AtTimeClause = None, parent_node: None = None) -> str:
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
            if node.time_window.interval_to:
                node_interval = {
                    "from": "scypher.timePoint(" + self.expression_converter.convert_time_point_literal(
                        node.time_window.interval_from) + ')',
                    "to": "scypher.timePoint(" + self.expression_converter.convert_time_point_literal(
                        node.time_window.interval_to) + ')'
                }
            else:
                raise SyntaxError("Must appoint a interval when set the effective time of the node")
        elif time_window:
            node_interval = {
                "from": self.expression_converter.convert_expression(time_window.time_point),
                "to": "scypher.timePoint(\"NOW\")"
            }
        else:
            node_interval = {
                "from": "scypher.operateTime()", "to": "scypher.timePoint(\"NOW\")"
            }
        node.effective_time = node_interval
        if node.__class__ == ObjectNode:
            node_pattern = node_pattern + "{intervalFrom: " + node_interval["from"] + ", intervalTo: " + node_interval[
                "to"] + "}"
        elif node.__class__ in [PropertyNode, ValueNode]:
            # 调用函数检查属性节点和值节点的有效时间是否满足约束
            if parent_node.time_window:
                parent_node_effective_time = {
                    "from": self.expression_converter.convert_time_point_literal(parent_node.time_window.interval_from),
                    "to": self.expression_converter.convert_time_point_literal(parent_node.time_window.interval_to)}
            else:
                if parent_node.variable not in self.variables_manager.updating_variables.keys():
                    parent_node_effective_time = {"from": parent_node.variable + ".intervalFrom",
                                                  "to": parent_node.variable + ".intervalTo"}
                elif time_window:
                    parent_node_effective_time = {
                        "from": self.expression_converter.convert_expression(time_window.time_point),
                        "to": "scypher.timePoint(\"NOW\")"}
                else:
                    parent_node_effective_time = {"from": "scypher.operateTime()", "to": "scypher.timePoint(\"NOW\")"}
            node_pattern = node_pattern + ", intervalFrom: scypher.getIntervalFromOfSubordinateNode(" + \
                           parent_node_effective_time["from"] + ", " + node_interval["from"] + "), "
            node_pattern = node_pattern + "intervalTo: scypher.getIntervalToOfSubordinateNode(" + \
                           parent_node_effective_time["to"] + ", " + node_interval["to"] + ")}"

        node_pattern = '(' + node_pattern + ')'
        return node_pattern

    def create_relationship(self, relationship: SRelationship, start_node: ObjectNode = None,
                            end_node: ObjectNode = None, time_window: AtTimeClause = None) -> str:
        if len(relationship.labels) == 0:
            raise SyntaxError(
                "Exactly one relationship type must be specified for CREATE. Did you forget to prefix your relationship type with a ':'?")
        elif len(relationship.labels) > 1:
            raise SyntaxError("Relationship type expressions in patterns are only allowed in MATCH clause")
        if relationship.length != (1, 1):
            raise SyntaxError("Variable length relationships cannot be used in CREATE")
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
        if relationship.time_window:
            relationship_effective_time = {
                "from": "scypher.timePoint(" + self.expression_converter.convert_time_point_literal(
                    relationship.time_window.interval_from) + ')'}
            if relationship.time_window.interval_to:
                relationship_effective_time[
                    "to"] = "scypher.timePoint(" + self.expression_converter.convert_time_point_literal(
                    relationship.time_window.interval_to) + ')'
            else:
                relationship_effective_time["to"] = "scypher.timePoint(\"NOW\")"
        elif time_window:
            relationship_effective_time = {
                "from": self.expression_converter.convert_expression(time_window.time_point),
                "to": "scypher.timePoint(\"NOW\")"
            }
        else:
            relationship_effective_time = {
                "from": "scypher.operateTime()", "to": "scypher.timePoint(\"NOW\")"
            }
        # 获取开始节点的有效时间
        if start_node.variable not in self.variables_manager.updating_variables.keys():
            start_node_effective_time = {"from": start_node.variable + ".intervalFrom",
                                         "to": start_node.variable + ".intervalTo"}
        else:
            start_node_effective_time = self.variables_manager.updating_object_nodes[start_node.variable].effective_time

        # 获取结束节点的有效时间
        if end_node.variable not in self.variables_manager.updating_variables.keys():
            end_node_effective_time = {"from": end_node.variable + ".intervalFrom",
                                       "to": end_node.variable + ".intervalTo"}
        else:
            end_node_effective_time = self.variables_manager.updating_object_nodes[end_node.variable].effective_time

        # getIntervalFromOfRelationship和getIntervalToOfRelationship用于检查关系的有效时间是否符合约束，以及是否有重复关系
        relationship_pattern = relationship_pattern + "intervalFrom: scypher.getIntervalFromOfRelationship(" + \
                               start_node_effective_time["from"] + ", " + end_node_effective_time["from"] + ", " + \
                               start_node.variable + ", " + end_node.variable + ", \"" + relationship.labels[
                                   0] + "\", " + \
                               relationship_effective_time["from"] + "), "
        relationship_pattern = relationship_pattern + "intervalTo: scypher.getIntervalToOfRelationship(" + \
                               start_node_effective_time["to"] + ", " + end_node_effective_time["to"] + ", " + \
                               start_node.variable + ", " + end_node.variable + ", \"" + relationship.labels[
                                   0] + "\", " + \
                               relationship_effective_time["to"] + ")}"
        relationship_pattern = '-[' + relationship_pattern + ']-'
        if relationship.direction == SRelationship.LEFT:
            relationship_pattern = '<' + relationship_pattern
        elif relationship.direction == SRelationship.RIGHT:
            relationship_pattern = relationship_pattern + '>'

        return relationship_pattern
