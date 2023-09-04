from __future__ import annotations
from transformer.ir.s_datetime import *
from transformer.ir.s_clause_component import *


class TimePointLiteral:
    pass


class AtTElement:
    def __init__(self, at_time: TimePointLiteral | NOW = None):
        self.at_time = at_time


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


class PathFunctionPattern:
    pass


class SinglePathPattern:
    pass
