from __future__ import annotations

from transformer.ir.s_clause_component import *
from transformer.ir.s_expression import Expression


class OrderByClause:
    # dict[排序的元素，排序方式]
    def __init__(self, sort_items: dict[Expression, str]):
        if len(sort_items) == 0:
            raise TranslateError("The sort items can't be empty")
        for item in sort_items.values():
            # 若未指定排序方式，将sort_item.value设为None
            if item and item.upper() not in ["ASCENDING", "ASC", "DESCENDING", "DESC"]:
                raise TranslateError("Uncertain sorting method")
        self.sort_items = sort_items


class ReturnClause:
    def __init__(self, projection_items: List[ProjectionItem] = None, is_all: bool = False, is_distinct: bool = False,
                 order_by_clause: OrderByClause = None, skip_expression: Expression = None,
                 limit_expression: Expression = None):
        if projection_items is None:
            projection_items = []
        if len(projection_items) == 0 and is_all is False:
            raise TranslateError("The return items can't be empty")
        self.projection_items = projection_items
        # 第一个返回值为*
        self.is_all = is_all
        self.is_distinct = is_distinct
        self.order_by_clause = order_by_clause
        self.skip_expression = skip_expression
        self.limit_expression = limit_expression


class AtTimeClause:
    def __init__(self, time_point: Expression):
        self.time_point = time_point


class BetweenClause:
    def __init__(self, interval: Expression):
        self.interval = interval


class MatchClause:
    def __init__(self, patterns: List[Pattern], is_optional: bool = False, where_expression: Expression = None,
                 time_window: AtTimeClause | BetweenClause = None):
        if len(patterns) == 0:
            raise TranslateError("The patterns can't be empty")
        self.patterns = patterns
        self.is_optional = is_optional
        self.where_expression = where_expression
        self.time_window = time_window


class UnwindClause:
    def __init__(self, expression: Expression, variable: str):
        self.expression = expression
        self.variable = variable


class YieldClause:
    def __init__(self, yield_items: List[YieldItem] = None, is_all=False, where_expression: Expression = None):
        if yield_items is None:
            yield_items = []
        if len(yield_items) == 0 and is_all is False:
            raise TranslateError("The yield items can't be empty")
        self.yield_items = yield_items
        # 第一个返回值为*
        self.is_all = is_all
        self.where_expression = where_expression


class CallClause:
    def __init__(self, procedure_name: str, input_items: List[Expression] = None, yield_clause: YieldClause = None):
        self.procedure_name = procedure_name
        if input_items is None:
            input_items = []
        self.input_items = input_items
        self.yield_clause = yield_clause


# 读查询
class ReadingClause:
    def __init__(self, reading_clause: MatchClause | UnwindClause | CallClause):
        self.reading_clause = reading_clause


class CreateClause:
    def __init__(self, patterns: List[Pattern], at_time_clause: AtTimeClause = None):
        if len(patterns) == 0:
            raise TranslateError("The patterns can't be empty")
        self.patterns = patterns
        self.at_time_clause = at_time_clause


class DeleteClause:
    def __init__(self, delete_items: List[DeleteItem], is_detach=False,
                 time_window: AtTimeClause | BetweenClause = None):
        if len(delete_items) == 0:
            raise TranslateError("The delete items can't be empty")
        self.delete_items = delete_items
        # 删除节点时，是否删除相连关系
        self.is_detach = is_detach
        self.time_window = time_window


class StaleClause:
    def __init__(self, stale_items: List[StaleItem], at_time_clause: AtTimeClause = None):
        if len(stale_items) == 0:
            raise TranslateError("The stale items can't be empty")
        self.stale_items = stale_items
        self.at_time_clause = at_time_clause


class SetClause:
    def __init__(self, set_items: List[EffectiveTimeSetting | ExpressionSetting | LabelSetting],
                 at_time_clause: AtTimeClause = None):
        if len(set_items) == 0:
            raise TranslateError("The set items can't be empty")
        self.set_items = set_items
        self.at_time_clause = at_time_clause


class MergeClause:
    ON_MATCH = "ON MATCH"
    ON_CREATE = "ON CREATE"

    def __init__(self, pattern: Pattern, actions: dict[str, SetClause] = None, at_time_clause: AtTimeClause = None):
        self.pattern = pattern
        if actions is None:
            actions = {}
        for (action, set_clause) in actions.items():
            if action not in [MergeClause.ON_MATCH, MergeClause.ON_CREATE]:
                raise TranslateError("Uncertain action")
            if set_clause.at_time_clause is None:
                set_clause.at_time_clause = at_time_clause
        self.actions = actions
        self.at_time_clause = at_time_clause


class RemoveClause:
    def __init__(self, remove_items: List[LabelSetting | RemovePropertyExpression]):
        if len(remove_items) == 0:
            raise TranslateError("The remove items can't be empty")
        self.remove_items = remove_items


# 更新查询
class UpdatingClause:
    def __init__(self,
                 updating_clause: CreateClause | DeleteClause | StaleClause | SetClause | MergeClause | RemoveClause):
        self.updating_clause = updating_clause


# 最后的子句为return或update的查询模块，单一查询
class SingleQueryClause:
    def __init__(self, reading_clauses: List[ReadingClause] = None, updating_clauses: List[UpdatingClause] = None,
                 return_clause: ReturnClause = None):
        if (updating_clauses is None or len(updating_clauses) == 0) and return_clause is None:
            raise TranslateError("The updating clauses and the return clause can't be empty at the same time")
        if reading_clauses is None:
            reading_clauses = []
        self.reading_clauses = reading_clauses
        if updating_clauses is None:
            updating_clauses = []
        self.updating_clauses = updating_clauses
        self.return_clause = return_clause


class WithClause:
    def __init__(self, projection_items: List[ProjectionItem] = None, is_all: bool = False, is_distinct: bool = False,
                 where_expression: Expression = None, order_by_clause: OrderByClause = None,
                 skip_expression: Expression = None, limit_expression: Expression = None):
        if projection_items is None:
            projection_items = []
        if len(projection_items) == 0 and is_all is False:
            raise TranslateError("The with items can't be empty")
        self.projection_items = projection_items
        # 第一个返回值为*
        self.is_all = is_all
        self.is_distinct = is_distinct
        self.where_expression = where_expression
        self.order_by_clause = order_by_clause
        self.skip_expression = skip_expression
        self.limit_expression = limit_expression


# 最后的子句为with的查询模块
class WithQueryClause:
    def __init__(self, with_clause: WithClause, reading_clauses: List[ReadingClause] = None,
                 updating_clauses: List[UpdatingClause] = None):
        self.with_clause = with_clause
        if reading_clauses is None:
            reading_clauses = []
        self.reading_clauses = reading_clauses
        if updating_clauses is None:
            updating_clauses = []
        self.updating_clauses = updating_clauses


# 多个查询（用WITH子句连接）
class MultiQueryClause:
    def __init__(self, single_query_clause: SingleQueryClause, with_query_clauses: List[WithQueryClause] = None):
        # 最后的子句为return或update的查询模块
        self.single_query_clause = single_query_clause
        # 最后的子句为with的查询模块
        if with_query_clauses is None:
            with_query_clauses = []
        self.with_query_clauses = with_query_clauses


# 复合查询（用UNION或UNION ALL连接）
class UnionQueryClause:
    def __init__(self, multi_query_clauses: List[MultiQueryClause], is_all: List[bool] = None):
        if len(multi_query_clauses) == 0:
            raise TranslateError("The multi-query clauses can't be empty")
        if is_all is None:
            is_all = []
        if len(multi_query_clauses) != len(is_all) + 1:
            raise TranslateError("The numbers of the clauses and union operations are not matched")
        self.multi_query_clauses = multi_query_clauses
        # 是否为union all
        self.is_all = is_all


class SnapshotClause:
    def __init__(self, time_point: Expression):
        self.time_point = time_point


class ScopeClause:
    def __init__(self, interval: Expression):
        self.interval = interval


# 时间窗口限定
class TimeWindowLimitClause:
    def __init__(self, time_window_limit: SnapshotClause | ScopeClause):
        self.time_window_limit = time_window_limit


class SCypherClause:
    def __init__(self, query_clause: UnionQueryClause | CallClause | TimeWindowLimitClause):
        self.query_clause = query_clause
