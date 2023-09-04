from transformer.grammar_parser.s_cypherListener import s_cypherListener
from transformer.grammar_parser.s_cypherParser import s_cypherParser
from transformer.ir.s_cypher_clause import *
from transformer.ir.s_pattern import *


# This class records important information about the query
class SCypherWalker(s_cypherListener):
    def __init__(self, parser: s_cypherParser):
        self.parser = parser
        # node
        self.node_patterns = []
        self.node_labels = []
        self.properties_pattern = []
        # time
        self.at_t_element = None
        # match
        self.match_patterns = []
        self.match_is_optional = False
        self.match_where_clause = None
        self.match_time_window = None

    def enterOC_Match(self, ctx: s_cypherParser.OC_MatchContext):
        if ctx.OPTIONAL() is not None:
            self.match_is_optional = True
        if ctx.oC_Pattern() is not None:
            pass
        if ctx.s_AtTime():
            pass
        elif ctx.s_Between():
            pass
        if ctx.oC_Where():
            pass

    def enterOC_Where(self, ctx: s_cypherParser.OC_WhereContext):
        expression = ctx.oC_Expression().getText()
        self.match_where_clause = WhereClause(expression)

    def enterOC_PatternPart(self, ctx: s_cypherParser.OC_PatternPartContext):
        variable = ""
        pattern = None
        if ctx.oC_Variable():
            variable = ctx.oC_Variable().getText()
            if ctx.s_PathFunctionPattern():
                pattern = ctx.s_PathFunctionPattern().getText()
            elif ctx.oC_AnonymousPatternPart():
                pattern = ctx.oC_AnonymousPatternPart().getText()
        else:
            pattern = ctx.oC_AnonymousPatternPart()

    def enterOC_NodePattern(self, ctx: s_cypherParser.OC_NodePatternContext):
        node_variable = ""
        node_label_list = []
        at_time_element = None
        property_list = []
        if ctx.oC_Variable():
            node_variable = ctx.oC_Variable().getText()
        if ctx.oC_NodeLabels():
            node_labels = ctx.oC_NodeLabels()
            for node_label in node_labels:
                node_label_list.append(node_label.getText())
        if ctx.s_AtTElement():
            at_time_element = self.at_t_element
        if ctx.s_Properties():
            property_list = self.properties_pattern
        self.node_patterns.append(NodePattern(node_variable, node_label_list, at_time_element, property_list))

    def enterS_AtTElement(self, ctx:s_cypherParser.S_AtTElementContext):
        self.at_t_element = AtTElement()
        if ctx.s_TimePointLiteral() is not None:
            self.at_t_element.at_time = ctx.s_TimePointLiteral().getText()
        elif ctx.NOW() is not None:
            self.at_t_element.at_time = ctx.NOW().getText()

    def enterS_PropertiesPattern(self, ctx:s_cypherParser.S_PropertiesPatternContext):
        property_key_names = []
        property_at_t_elements = []
        property_expressions = []
        if ctx.oC_PropertyKeyName() is not None:
            prop_key_names = ctx.oC_PropertyKeyName()
            for prop_key_name in prop_key_names:
                property_key_names.append(prop_key_name.getText())
        if ctx.s_AtTElement() is not None:
            prop_at_t_elements = ctx.s_AtTElement()
            for prop_at_t_element in prop_at_t_elements:
                property_at_t_elements.append(prop_at_t_element.getText())
        if ctx.oC_Expression() is not None:
            prop_expressions = ctx.oC_Expression()
            for prop_expression in prop_expressions:
                property_expressions.append(prop_expression.getText())
        # 添加时间与键值对应匹配的判断
        for key_name, at_t_element, expression in zip(property_key_names, property_at_t_elements, property_expressions):
            self.properties_pattern.append(PropertiesPattern(key_name, at_t_element, expression))

    def enterOC_RelationshipDetail(self, ctx:s_cypherParser.OC_RelationshipDetailContext):
        variable = ctx.oC_Variable().getText

    def enterOC_AnonymousPatternPart(self, ctx: s_cypherParser.OC_AnonymousPatternPartContext):
        pass

    def enterS_AtTime(self, ctx:s_cypherParser.S_AtTimeContext):
        pass

    def enterOC_Return(self, ctx):
        print("return:")
        items = ctx.oC_ProjectionBody().oC_ProjectionItems().oC_ProjectionItem()
        for item in items:
            print(item.getText())
