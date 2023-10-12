from __future__ import annotations
from transformer.exceptions.s_exception import ClauseError
from transformer.ir.s_clause_component import *
from transformer.ir.s_expression import Expression


class OrderByClause:
    # dict[排序的元素，排序方式
    def __init__(self, sort_items: dict[Expression, str]):
        if len(sort_items) == 0:
            raise ValueError("The sort items can't be empty.")
        for item in sort_items.values():
            # 若未指定排序方式，将sort_item.value设为None
            if item and item.upper() not in ["ASCENDING", "ASC", "DESCENDING", "DESC"]:
                raise ValueError("Uncertain sorting method.")
        self.sort_items = sort_items


class ReturnClause:
    def __init__(self, projection_items: List[ProjectionItem], is_distinct: bool = False,
                 order_by_clause: OrderByClause = None, skip_expression: Expression = None,
                 limit_expression: Expression = None):
        if len(projection_items) == 0:
            raise ValueError("The projection items can't be empty.")
        self.projection_items = projection_items
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
            raise ValueError("The patterns can't be empty.")
        self.patterns = patterns
        self.is_optional = is_optional
        self.where_expression = where_expression
        if time_window.__class__ == AtTimeClause:
            self.time_window = time_window.time_point
        elif time_window.__class__ == BetweenClause:
            self.time_window = time_window.interval
        else:
            self.time_window = None


class UnwindClause:
    def __init__(self, expression: Expression, variable: str):
        self.expression = expression
        self.variable = variable


class YieldClause:
    def __init__(self, yield_items: List[YieldItem], where_expression: Expression = None):
        if len(yield_items) == 0:
            raise ValueError("The yield items can't be empty.")
        self.yield_items = yield_items
        self.where_expression = where_expression


class CallClause:

    def __init__(self, procedure_name: str, input_items: List[Expression] = None, yield_clause: YieldClause = None):
        if procedure_name in ["interval", "interval.intersection", "interval.range", "interval.elapsedTime",
                              "timePoint"]:
            procedure_name = "scypher." + procedure_name
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
    def __init__(self, patterns: List[Pattern]):
        if len(patterns) == 0:
            raise ValueError("The patterns can't be empty.")
        self.patterns = patterns


class DeleteClause:
    def __init__(self, delete_items: List[DeleteItem]):
        if len(delete_items) == 0:
            raise ValueError("The delete items can't be empty.")
        self.delete_items = delete_items


class StaleClause:
    # stale_item和delete_item的形式是相同的
    def __init__(self, stale_items: List[DeleteItem]):
        if len(stale_items) == 0:
            raise ValueError("The stale items can't be empty.")
        self.stale_items = stale_items


class SetClause:
    def __init__(self, set_items: List[SetItem]):
        if len(set_items) == 0:
            raise ValueError("The set items can't be empty.")
        self.set_items = set_items


class MergeClause:
    def __init__(self, patterns: List[Pattern], actions: dict[str, SetClause] = None):
        if len(patterns) == 0:
            raise ValueError("The patterns can't be empty.")
        self.patterns = patterns
        if actions is None:
            actions = []
        self.actions = actions


class RemoveClause:
    def __init__(self, object_variable: Atom, property_variable: str = None, labels: List[str] = None):
        if property_variable is None and labels is None:
            raise ValueError("Only can remove the labels or properties of object nodes.")
        self.object_variable = object_variable
        # 为(SP? oC_PropertyLookup) + 的字符串表示
        self.property_variable = property_variable
        if labels is None:
            labels = []
        self.labels = labels


# 更新查询
class UpdatingClause:
    def __init__(self,
                 update_clause: CreateClause | DeleteClause | StaleClause | SetClause | MergeClause | RemoveClause,
                 at_time_clause: AtTimeClause = None):
        self.update_clause = update_clause
        self.at_time_clause = at_time_clause


# 最后的子句为return或update的查询模块，单一查询
class SingleQueryClause:
    def __init__(self, reading_clauses: List[ReadingClause] = None, updating_clauses: List[UpdatingClause] = None,
                 return_clause: ReturnClause = None):
        if (updating_clauses is None or len(updating_clauses) == 0) and return_clause is None:
            raise ClauseError("The updating clauses and the return_clause can't be empty at the same time.")
        if reading_clauses is None:
            reading_clauses = []
        self.reading_clauses = reading_clauses
        if updating_clauses is None:
            updating_clauses = []
        self.updating_clauses = updating_clauses
        self.return_clause = return_clause


class WithClause:
    def __init__(self, projection_items: List[ProjectionItem], is_distinct: bool = False,
                 order_by_clause: OrderByClause = None, skip_expression: Expression = None,
                 limit_expression: Expression = None):
        if len(projection_items) == 0:
            raise ValueError("The projection items can't be empty.")
        self.projection_items = projection_items
        self.is_distinct = is_distinct
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
            raise ValueError("The multi-query clauses can't be empty.")
        if is_all is None:
            is_all = []
        if len(multi_query_clauses) != len(is_all) + 1:
            raise ClauseError("The numbers of the clauses and union operations are not matched.")
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
