from __future__ import annotations
from transformer.ir.s_datetime import *
from transformer.ir.s_clause_component import *
from transformer.ir.s_graph import *


class AtTElement:
    def __init__(self, time_from: Time, time_to: Time | NOW):
        self.time_from = time_from
        self.time_to = time_to


class PropertiesPattern:
    def __init__(self, property_key_name: list[str], at_t_element: AtTElement = None, expression: Expression = None):
        self.property_key_name = property_key_name
        self.at_t_element = at_t_element
        self.expression = expression


class NodePattern:
    def __init__(self, variable: str = None, node_labels: list[str] = None, at_t_element: AtTElement = None,
                 properties: PropertiesPattern = None):
        self.variable = variable
        self.node_labels = node_labels
        self.at_t_element = at_t_element
        self.properties = properties


class RelationshipPattern:
    def __init__(self, relationship_detail: SEdge):
        self.relationship_detail = relationship_detail


class PatternElementChain:
    def __init__(self, rel_pattern: RelationshipPattern, node_pattern: NodePattern):
        self.rel_pattern = rel_pattern
        self.node_pattern = node_pattern


class PathFunctionPattern:
    def __init__(self, function_name: str, single_path_pattern: SinglePathPattern):
        self.function_name = function_name
        self.single_path_pattern = single_path_pattern


class SinglePathPattern:
    def __init__(self, node_pattern_left: NodePattern, rel_pattern: RelationshipPattern, node_pattern_right: NodePattern):
        self.node_pattern_left = node_pattern_left
        self.rel_pattern = rel_pattern
        self.node_pattern_right = node_pattern_right

