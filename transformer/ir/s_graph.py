from typing import List, Tuple

from transformer.exceptions.s_exception import TranslateError
from transformer.ir.s_expression import Expression, AtTElement


class SNode:
    def __init__(self, labels: List[str], content: str | Expression = None, variable: str = None,
                 time_window: AtTElement = None):
        # 节点标签，至少有一个区别节点类型的标签（Object, Property或Value），对象节点的内容以标签形式存储
        self.labels = labels
        # 节点内容, 对象节点的内容以标签形式存储，即对象节点的content属性为null; 属性节点的内容为属性名，为str类型; 值节点的内容为属性值，为Expression类型
        self.content = content
        # 表示节点的变量名
        self.variable = variable
        # 节点在图模式中被限制的有效时间
        self.time_window = time_window


class PropertyNode(SNode):
    def __init__(self, content: str, variable: str = None, time_window: AtTElement = None):
        super().__init__(['Property'], content, variable, time_window)


class ValueNode(SNode):
    def __init__(self, content: Expression, variable: str = None, time_window: AtTElement = None):
        super().__init__(['Value'], content, variable, time_window)


class ObjectNode(SNode):

    def __init__(self, labels: List[str] = None, variable: str = None, time_window: AtTElement = None,
                 properties: dict[PropertyNode, ValueNode] = None):
        if labels is None:
            labels = []
        labels.append('Object')
        super().__init__(labels, None, variable, time_window)
        if properties is None:
            properties = {}
        self.properties = properties


class SRelationship:
    LEFT = 'LEFT'
    RIGHT = 'RIGHT'
    UNDIRECTED = 'UNDIRECTED'

    def __init__(self, direction: str, variable: str = None, labels: List[str] = None, length: Tuple[int, int] = (1, 1),
                 time_window: AtTElement = None, properties: dict[str, Expression] = None):
        if direction.upper() not in [self.LEFT, self.RIGHT, self.UNDIRECTED]:
            raise TranslateError("Direction of relationships must be 'LEFT', 'RIGHT' or 'UNDIRECTED'")
        if length[0] is not None and length[1] is not None and (length[0] < 0 or length[0] > length[1]):
            raise TranslateError("The length range of relationship is incorrect")
        self.direction = direction
        self.variable = variable
        if labels is None:
            labels = []
        self.labels = labels  # 相当于content
        # 没有指名长度时设为None，例如，*2.. -> (2, None)， * -> (None, None) *..2 -> (None, 2)
        self.length = length
        self.time_window = time_window
        if properties is None:
            properties = {}
        self.properties = properties


class SPath:
    def __init__(self, nodes: List[ObjectNode], relationships: List[SRelationship] = None, variable: str = None):
        if relationships is None:
            relationships = []
        if len(nodes) != len(relationships) + 1:
            raise TranslateError("The numbers of the nodes and relationships are not matched")
        self.nodes = nodes
        self.relationships = relationships
        self.variable = variable
