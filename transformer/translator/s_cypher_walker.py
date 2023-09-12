from transformer.grammar_parser.s_cypherListener import s_cypherListener
from transformer.grammar_parser.s_cypherParser import s_cypherParser
from transformer.ir.s_cypher_clause import *
from transformer.ir.s_datetime import *
from transformer.ir.s_graph import *


# This class records important information about the query
class SCypherWalker(s_cypherListener):
    def __init__(self, parser: s_cypherParser):
        self.parser = parser
        # node
        self.properties = dict()  # 对象节点的属性 dict[PropertyNode, ValueNode]
        self.property_node_list = []  # 属性节点列表
        self.value_node_list = []  # 值节点列表
        # time
        self.at_time = None
        self.interval = None
        # pattern
        self.patterns = []
        self.object_node_list = []
        self.edge_list = None
        # path
        self.path_function_name = ""
        # clauses
        self.multi_query_clauses = []
        self.match_clause = None
        self.with_clause = None

        self.where_clause = None
        self.reading_clause = None
        self.unwind_clause = None
        self.inner_call_clause = None
        self.order_by_clause = None
        self.skip_clause = None
        self.limit_clause = None

        self.return_clause = None
        self.projection_items = []

        self.updating_clause = None
        self.single_query_clause = None
        self.with_query_clause = None
        self.union_query_clause = None
        self.stand_alone_call_clause = None
        self.time_window_limit_clause = None

    def exitOC_Union(self, ctx: s_cypherParser.OC_UnionContext):
        # multi_query_clauses: List[MultiQueryClause],
        # is_all: List[bool]
        # ---------test match--------
        is_all_list = []
        if "UNION ALL" in ctx.UNION().getText():
            is_all_list.append(True)
        else:
            is_all_list.append(False)
        self.union_query_clause = UnionQueryClause(self.multi_query_clauses, is_all_list)

    def exitOC_MultiPartQuery(self, ctx: s_cypherParser.OC_MultiPartQueryContext):
        # single_query_clause: SingleQueryClause = None,
        # with_query_clauses: List[WithQueryClause] = None
        pass

    def exitOC_SingleQuery(self, ctx: s_cypherParser.OC_SingleQueryContext):
        # reading_clauses: List[ReadingClause] = None,
        # updating_clauses: List[UpdatingClause] = None,
        # return_clause: ReadingClause
        # -----------------是不是要换成ReturnClause-------------
        pass

    def exitOC_With(self, ctx:s_cypherParser.OC_WithContext):
        #  with_clause: WithClause,
        #  reading_clauses: List[ReadingClause] = None,
        #  updating_clauses: List[UpdatingClause] = None
        pass

    def enterOC_ReadingClause(self, ctx: s_cypherParser.OC_ReadingClauseContext):
        match_clause = None
        unwind_clause = None
        in_query_call_clause = None
        if ctx.oC_Match() is not None:
            self.reading_clause = ReadingClause(self.match_clause)
        elif ctx.oC_Unwind() is not None:
            self.reading_clause = ReadingClause(self.unwind_clause)
        elif ctx.oC_InQueryCall() is not None:
            self.reading_clause = ReadingClause(self.inner_call_clause)
        else:
            pass

    def exitOC_ReadingClause(self, ctx:s_cypherParser.OC_ReadingClauseContext):
        # reading_clause: MatchClause | UnwindClause | CallClause
        pass

    def exitOC_Match(self, ctx: s_cypherParser.OC_MatchContext):
        is_optional = False
        patterns = []
        time_window = None
        where_clause = None
        if ctx.OPTIONAL() is not None:
            is_optional = True
        if ctx.oC_Pattern() is not None:
            patterns = self.patterns
        if ctx.s_AtTime() is not None:
            time_window = self.at_time
        elif ctx.s_Between() is not None:
            time_window = self.interval
        if ctx.oC_Where() is not None:
            where_clause = self.where_clause
        self.match_clause = MatchClause(patterns, is_optional, where_clause, time_window)

    def enterOC_Where(self, ctx: s_cypherParser.OC_WhereContext):
        expression = ctx.oC_Expression().getText()
        self.where_clause = WhereClause(expression)

    def enterS_Between(self, ctx: s_cypherParser.S_BetweenContext):
        # 时间区间左右节点的获取待添加
        self.interval = ctx.oC_Expression().getText()

    def enterS_AtTime(self, ctx: s_cypherParser.S_AtTimeContext):
        self.at_time = ctx.oC_Expression().getText()

    def enterOC_Unwind(self, ctx:s_cypherParser.OC_UnwindContext):
        self.unwind_clause = ctx.UNWIND().getText()

    def enterOC_InQueryCall(self, ctx:s_cypherParser.OC_InQueryCallContext):
        self.inner_call_clause = ctx.CALL().getText()

    @staticmethod
    def getInterval(interval_str) -> Interval:
        index = 0
        interval_from = interval_to = ""
        find_from = find_to = False
        while index < len(interval_str):
            if interval_str[index] == " ":
                index = index + 1
                continue
            elif interval_str[index] == '(':
                find_from = True
            elif interval_str[index] == ',':
                find_to = True
                find_from = False
            elif interval_str[index] == ')':
                break
            elif find_from:
                interval_from += interval_str[index]
            elif find_to:
                interval_to += interval_str[index]
            index = index + 1
        if interval_to == "NOW":
            interval = Interval(LocalDateTime(interval_from.strip('"')), TimePoint.NOW)
        else:
            interval = Interval(LocalDateTime(interval_from.strip('"')), LocalDateTime(interval_to.strip('"')))
        return interval

    # 获取对象节点
    def exitOC_NodePattern(self, ctx: s_cypherParser.OC_NodePatternContext):
        # node_content = ""  # 对象节点内容
        node_label_list = []  # 对象节点标签
        interval = None  # 对象节点时间
        properties = []  # 对象节点属性
        # if ctx.oC_Variable() is not None:
        #     node_content = ctx.oC_Variable().getText()
        if ctx.oC_NodeLabels() is not None:
            node_labels = ctx.oC_NodeLabels()
            if isinstance(node_labels, list):
                for node_label in node_labels:
                    node_label_list.append(node_label.getText().strip(':'))
            else:
                node_label_list.append(node_labels.getText().strip(':'))
        if ctx.s_AtTElement() is not None:
            n_interval = ctx.s_AtTElement()
            interval_str = n_interval.getText()
            interval = self.getInterval(interval_str)
        if ctx.s_Properties() is not None:
            properties = self.properties
        self.object_node_list.append(ObjectNode(node_label_list, None, interval, properties))

    def exitS_PropertiesPattern(self, ctx: s_cypherParser.S_PropertiesPatternContext):
        # 将属性节点和值节点组合成对象节点的属性
        for prop_node, val_node in zip(self.property_node_list, self.value_node_list):
            self.properties[prop_node] = val_node

    # 获取属性节点
    def enterS_PropertyNode(self, ctx: s_cypherParser.S_PropertyNodeContext):
        property_contents = []  # 属性节点内容
        property_intervals = []  # 属性节点时间
        # 获取属性节点内容
        if ctx.oC_PropertyKeyName() is not None:
            prop_contents = ctx.oC_PropertyKeyName()
            if isinstance(prop_contents, list):
                for prop_content in prop_contents:
                    property_contents.append(prop_content.getText())
            else:
                property_contents = [prop_contents.getText()]
        # 获取属性节点的时间
        if ctx.s_AtTElement() is not None:
            prop_intervals = ctx.s_AtTElement()
            if isinstance(prop_intervals, list):
                for prop_interval in prop_intervals:
                    interval_str = prop_interval.getText()
                    property_intervals.append(self.getInterval(interval_str))
            else:
                property_intervals = [self.getInterval(prop_intervals.getText())]
        # 构造属性节点列表
        for prop_content, prop_interval in zip(property_contents, property_intervals):
            self.property_node_list.append(PropertyNode(prop_content, None, prop_interval))

    # 获取值节点
    def enterS_ValueNode(self, ctx: s_cypherParser.S_ValueNodeContext):
        value_contents = []  # 值节点内容
        value_intervals = []  # 值节点时间
        # 获取值节点内容
        if ctx.oC_Expression() is not None:
            val_contents = ctx.oC_Expression()
            if isinstance(val_contents, list):
                for val_content in val_contents:
                    value_contents.append(val_content.getText())
            else:
                value_contents = [val_contents.getText()]
        # 获取值节点的时间
        if ctx.s_AtTElement() is not None:
            val_intervals = ctx.s_AtTElement()
            if isinstance(val_intervals, list):
                for val_interval in val_intervals:
                    interval_str = val_interval.getText()
                    value_intervals.append(self.getInterval(interval_str))
            else:
                value_intervals = [self.getInterval(val_intervals.getText())]
        # 构造值节点
        for val_content, val_interval in zip(value_contents, value_intervals):
            self.value_node_list.append(ValueNode(val_content, None, val_interval))

    # 获取时间
    def enterS_AtTElement(self, ctx: s_cypherParser.S_AtTElementContext):
        time_list = ctx.s_TimePointLiteral()
        now = ctx.NOW()
        if len(time_list) == 2 and now is None:
            interval_from = time_list[0].getText().strip('"')
            interval_to = time_list[1].getText().strip('"')
        elif len(time_list) == 1 and now is not None:
            interval_from = time_list[0].getText().strip('"')
            interval_to = ctx.NOW().getText().strip('"')
        else:
            raise FormatError("Invalid time format!")
        if interval_to == "NOW":
            self.interval = Interval(LocalDateTime(interval_from), TimePoint.NOW)
        else:
            self.interval = Interval(LocalDateTime(interval_from), LocalDateTime(interval_to))

    def enterOC_RelationshipDetail(self, ctx: s_cypherParser.OC_RelationshipDetailContext):
        variable = ""
        if ctx.oC_Variable() is not None:
            variable = ctx.oC_Variable().getText()
        interval = Interval(self.interval.interval_from, self.interval.interval_to)
        lengths = ctx.oC_RangeLiteral().oC_IntegerLiteral()
        length_tuple = tuple()
        for length in lengths:
            length_tuple.__add__(length)
        labels = ctx.oC_RelationshipTypes()
        labels_list = []
        for label in labels:
            labels_list.append(label.getText())
        properties = ctx.oC_Properties()
        property_list = []
        for property_ in property_list:
            property_list.append(property_.getText())
        self.edge_list = SEdge('UNDIRECTED', variable, labels, length_tuple, interval, properties)

    def exitOC_RelationshipPattern(self, ctx:s_cypherParser.OC_RelationshipPatternContext):
        direction = 'UNDIRECTED'
        if ctx.oC_LeftArrowHead() is not None and ctx.oC_RightArrowHead() is None:
            direction = 'LEFT'
        elif ctx.oC_LeftArrowHead() is None and ctx.oC_RightArrowHead() is not None:
            direction = 'RIGHT'
        self.edge_list.direction = direction

    # def exitOC_AnonymousPatternPart(self, ctx: s_cypherParser.OC_AnonymousPatternPartContext):
    #     if self.object_node_list is not None:
    #         self.match_patterns.append(self.object_node_list)
    #         if self.edge_list is not None:
    #             self.match_patterns.append(self.edge_list)
    #     else:
    #         self.match_patterns.append(ctx.oC_PatternElement().getText())

    def exitOC_Pattern(self, ctx: s_cypherParser.OC_PatternContext):
        # nodes: List[ObjectNode],
        # edges: List[SEdge] = None,
        # variable: str = None
        nodes = self.object_node_list
        edges = self.edge_list
        self.patterns.append(Pattern(SPath(nodes, edges)))

    def enterOC_Expression(self, ctx: s_cypherParser.OC_ExpressionContext):
        pass

    def exitOC_Return(self, ctx: s_cypherParser.OC_ReturnContext):
        # projection_items: List[ProjectionItem],
        # is_distinct: bool = False,
        # order_by_clause: OrderByClause = None,
        # skip_clause: SkipClause = None,
        # limit_clause: LimitClause = None
        projection_items = self.projection_items
        is_distinct = False
        if ctx.oC_ProjectionBody().DISTINCT() is not None:
            is_distinct = True
        order_by_clause = self.order_by_clause
        skip_clause = self.skip_clause
        limit_clause = self.limit_clause
        self.return_clause = ReturnClause(projection_items, is_distinct, order_by_clause, skip_clause, limit_clause)

    def enterOC_ProjectionItems(self, ctx:s_cypherParser.OC_ProjectionItemsContext):
        # is_all: bool = False,
        # expression: Exception = None,
        # variable: str = None
        is_all = False
        if '*' in ctx.getText():
            is_all = True
        projection_item = ctx.oC_ProjectionItem()
        variable = None
        if isinstance(projection_item, list):
            for item in projection_item:
                expression = item.oC_Expression().getText()
                if item.oC_Variable is not None:
                    variable = item.oC_Variable()
                self.projection_items.append(ProjectionItem(is_all, expression, variable))
        else:
            expression = projection_item.oC_Expression().getText()
            variable = projection_item.oC_Variable().getText()
            self.projection_items.append(ProjectionItem(is_all, expression, variable))

