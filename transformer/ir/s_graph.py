from typing import List, Tuple

from transformer.exceptions.s_exception import GraphError
from transformer.ir.s_datetime import Interval
from transformer.ir.s_expression import Expression


class SNode:
    def __init__(self, labels: List[str], content: str | Expression = None, variable: str = None,
                 interval: Interval = None):
        # 节点标签，至少有一个区别节点类型的标签（Object, Property或Value），对象节点的内容以标签形式存储
        self.labels = labels
        # 节点内容, 对象节点的内容以标签形式存储，即对象节点的content属性为null; 属性节点的内容为属性名，为str类型; 值节点的内容为属性值，为Expression类型
        self.content = content
        # 表示节点的变量名
        self.variable = variable
        # 节点有效时间
        self.interval = interval


class PropertyNode(SNode):
    def __init__(self, content: str, variable: str = None, interval: Interval = None):
        super().__init__(['Property'], content, variable, interval)


class ValueNode(SNode):
    def __init__(self, content: Expression, variable: str = None, interval: Interval = None):
        super().__init__(['Value'], content, variable, interval)


class ObjectNode(SNode):

    def __init__(self, labels: List[str] = None, variable: str = None, interval: Interval = None,
                 properties: dict[PropertyNode, ValueNode] = None):
        if labels is None:
            labels = []
        labels.append('Object')
        super().__init__(labels, None, variable, interval)
        if properties is None:
            properties = {}
        self.properties = properties

    def get_variables_dict(self) -> dict:
        variables_dict = {}
        if self.variable:
            variables_dict[self.variable] = self
        for key, value in self.properties.items():
            if key.variable:
                variables_dict[key.variable] = key
            if value.variable:
                variables_dict[value.variable] = value
        return variables_dict


class SEdge:
    LEFT = 'LEFT'
    RIGHT = 'RIGHT'
    UNDIRECTED = 'UNDIRECTED'

    def __init__(self, direction, variable: str = None, labels: List[str] = None, length: Tuple[int, int] = (1, 1),
                 interval: Interval = None, properties: dict = None):
        if direction not in [self.LEFT, self.RIGHT, self.UNDIRECTED]:
            raise ValueError("Direction of edges must in 'LEFT', 'RIGHT' and 'UNDIRECTED'.")
        if length[0] < 0 or length[0] > length[1]:
            raise ValueError("The length range of edge is incorrect.")
        self.direction = direction
        self.variable = variable
        if labels is None:
            labels = []
        self.labels = labels  # 相当于content
        self.length = length
        self.interval = interval
        if properties is None:
            properties = []
        self.properties = properties


class SPath:
    def __init__(self, nodes: List[ObjectNode], edges: List[SEdge] = None, variable: str = None):
        if edges is None:
            edges = []
        if len(nodes) != len(edges) + 1:
            raise GraphError("The numbers of the nodes and edges are not matched.")
        self.nodes = nodes
        self.edges = edges
        self.variable = variable

    def get_variables_dict(self) -> dict:
        variables_dict = {}
        if self.variable:
            variables_dict = {self.variable: self}
        for node in self.nodes:
            variables_dict.update(node.get_variables_dict())
        for edge in self.edges:
            if edge.variable:
                variables_dict[edge.variable] = edge
        return variables_dict
