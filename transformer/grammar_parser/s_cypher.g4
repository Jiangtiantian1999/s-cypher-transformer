grammar s_cypher;
import cypher;

oC_Query : oC_RegularQuery
         | oC_StandaloneCall
         | s_TimeWindowLimit
         ;

oC_MultiPartQuery
              :  s_WithPartQuery+ oC_SinglePartQuery ;

oC_Match : ( OPTIONAL SP )? MATCH SP? oC_Pattern ( SP? ( s_AtTime | s_Between ) )? ( SP? oC_Where )? ;

oC_UpdatingClause : s_Create | s_Merge | s_Set | oC_Remove | s_Stale | s_Delete ;

s_Create : CREATE SP? oC_Pattern ( SP? s_AtTime )? ;

s_Merge : MERGE SP? oC_PatternPart ( SP oC_MergeAction )* ( SP? s_AtTime )? ;

s_Set : SET SP? oC_SetItem ( SP? ',' SP? oC_SetItem )* ( SP? s_AtTime )? ;

s_Stale : STALE SP? s_StaleItem ( SP? ',' SP? s_StaleItem )* ( SP? s_AtTime )? ;

oC_SetItem : ( oC_PropertyExpression ( SP? s_AtTElement )? SP? '=' SP? oC_Expression )
           | ( oC_Variable SP? '=' SP? oC_Expression )
           | ( oC_Variable SP? '+=' SP? oC_Expression )
           | ( oC_Variable SP? oC_NodeLabels )
           | ( oC_Variable SP? s_AtTElement )
           | ( oC_Variable ( SP? s_AtTElement )? SP? '.' SP? s_SetPropertyItemOne )
           | ( oC_Variable ( SP? s_AtTElement )? SP? '.' SP? s_SetPropertyItemTwo SP? s_SetValueItem )
           ;

s_SetPropertyItemOne : oC_PropertyKeyName SP? s_AtTElement ;

s_SetPropertyItemTwo : oC_PropertyKeyName ( SP? s_AtTElement )? ;

s_SetValueItem : PoundValue SP? s_AtTElement ;

s_StaleItem : oC_Expression ( s_PropertyLookupName SP? PoundValue )? ;

s_Delete : ( DETACH SP )? DELETE SP? s_DeleteItem ( SP? ',' SP? s_DeleteItem )* ( SP? ( s_AtTime | s_Between ) )? ;

s_DeleteItem : oC_Expression ( s_PropertyLookupName ( SP? ( PoundValue | s_AtTElement ) )? )? ;

oC_RemoveItem : ( oC_Variable oC_NodeLabels )
              | oC_PropertyExpression
              ;

s_AtTime : AT_TIME SP? oC_Expression;

s_Between : BETWEEN SP? oC_Expression;

s_TimeWindowLimit : s_Snapshot
                  | s_Scope
                  ;

oC_InQueryCall : CALL SP oC_ExplicitProcedureInvocation ( SP? YIELD SP s_YieldItems )? ;

oC_StandaloneCall : CALL SP ( oC_ExplicitProcedureInvocation | oC_ImplicitProcedureInvocation ) ( SP? YIELD SP ( '*' | s_YieldItems ) )? ;

s_YieldItems : s_YieldItem ( SP? ',' SP? s_YieldItem )* ( SP? oC_Where )? ;

s_YieldItem : oC_ProcedureResultField ( SP AS SP oC_Variable )? ;

s_WithPartQuery : ( oC_ReadingClause SP? )* ( oC_UpdatingClause SP? )* s_With SP? ;

s_With : WITH oC_ProjectionBody ( SP? oC_Where )? ;

oC_ExistentialSubquery : EXISTS SP? '{' SP? ( oC_RegularQuery | ( oC_Pattern ( SP? oC_Where )? ) ) SP? '}' ;

oC_FilterExpression : oC_IdInColl ( SP? oC_Where )? ;

s_Snapshot : SNAPSHOT SP? oC_Expression ;

s_Scope : SCOPE SP? oC_Expression ;

oC_PatternPart : oC_Variable SP? '=' SP? s_PathFunctionPattern
               | oC_Variable SP? '=' SP? oC_AnonymousPatternPart
               | oC_AnonymousPatternPart
               ;

s_PathFunctionPattern : oC_FunctionName SP? '(' SP? s_SinglePathPattern SP? ')' ;

s_SinglePathPattern : oC_NodePattern SP? oC_RelationshipPattern SP? oC_NodePattern ;

oC_NodePattern : '(' SP? ( oC_Variable SP? )? ( oC_NodeLabels SP? )? ( s_AtTElement SP? )? ( s_Properties SP? )? ')' ;

s_Properties : s_PropertiesPattern
              | oC_Parameter
              ;

s_PropertiesPattern : '{' ( SP? s_PropertyNode SP? ':' SP? s_ValueNode ( SP? ',' SP? s_PropertyNode SP? ':' SP? s_ValueNode )* )? SP? '}' ;

s_PropertyNode : oC_PropertyKeyName ( SP? s_AtTElement )? ;

s_ValueNode : oC_Expression SP? ( '(' SP? s_AtTElement SP? ')' )? ;

oC_RelationshipDetail : '[' SP? ( oC_Variable SP? )? ( oC_RelationshipTypes SP? )? oC_RangeLiteral? ( s_AtTElement SP? )? ( oC_Properties SP? )? ']' ;

oC_ComparisonExpression
                    :  oC_StringListNullPredicateExpression ( SP? s_ComparisonOperator SP? oC_StringListNullPredicateExpression )* ;

oC_StringListNullPredicateExpression : oC_AddOrSubtractExpression ( s_TimePredicateExpression | oC_StringPredicateExpression | oC_ListPredicateExpression | oC_NullPredicateExpression )? ;

oC_AddOrSubtractExpression
                       :  oC_MultiplyDivideModuloExpression ( ( SP? s_AddOrSubtractOperator SP? oC_MultiplyDivideModuloExpression ) )* ;

s_MultiplyDivideModuloOperator : '*' | '/' | '%' ;

s_PowerOfOperator : '^' ;

s_AddOrSubtractOperator : '+' | '-' ;

s_ComparisonOperator : '=' | '<>' | '<' | '<=' | '>' | '>=' ;

oC_MultiplyDivideModuloExpression
                              :  oC_PowerOfExpression ( ( SP? s_MultiplyDivideModuloOperator SP? oC_PowerOfExpression ) )* ;

oC_PowerOfExpression
                 :  oC_UnaryAddOrSubtractExpression ( SP? s_PowerOfOperator SP? oC_UnaryAddOrSubtractExpression )* ;

oC_ListOperatorExpression : ( oC_PropertyOrLabelsExpression | s_AtTExpression ) ( s_SingleIndexExpression | s_DoubleIndexExpression )* ;

s_SingleIndexExpression : SP? '[' SP? s_LeftExpression SP? ']' ;

s_DoubleIndexExpression : SP? '[' SP? s_LeftExpression? SP? '..' SP? s_RightExpression? SP? ']' ;

s_LeftExpression : oC_Expression ;

s_RightExpression : oC_Expression ;

oC_PropertyOrLabelsExpression : oC_Atom ( SP? oC_PropertyLookup )* ( SP? ( oC_NodeLabels | s_AtTElement ) )? ;

s_AtTExpression : oC_Atom ( SP? oC_PropertyLookup )* ( s_PropertyLookupName ( SP? ( PoundValue | s_AtTElement ) )? )? SP? s_PropertyLookupTime ;

s_PropertyLookupName : SP? oC_PropertyLookup ;

s_PropertyLookupTime : AtT ( SP? oC_PropertyLookup )* ;

s_TimePredicateExpression : SP ( DURING | OVERLAPS ) SP oC_AddOrSubtractExpression ;

s_AtTElement : AtT SP? '(' ( SP? s_TimePointLiteral SP? ',' )? SP? ( s_TimePointLiteral | NOW ) SP? ')';

s_TimePointLiteral : StringLiteral
                   | oC_MapLiteral
                   ;

oC_FunctionInvocation
                  :  oC_FunctionName SP? '(' SP? ( DISTINCT SP? )? ( s_FunctionInvocationExpression SP? ( ',' SP? s_FunctionInvocationExpression SP? )* )? ')' ;

s_FunctionInvocationExpression: oC_Expression ;

oC_ListLiteral
           :  '[' SP? ( s_ListLiteralExpression SP? ( ',' SP? s_ListLiteralExpression SP? )* )? ']' ;

s_ListLiteralExpression : oC_Expression ;

oC_MapLiteral
          :  '{' SP? ( s_MapKeyValue ( ',' SP? s_MapKeyValue )* )? '}' ;

s_MapKeyValue
          :  oC_PropertyKeyName SP? ':' SP? oC_Expression SP? ;

oC_SymbolicName : UnescapedSymbolicName
                | EscapedSymbolicName
                | HexLetter
                | COUNT
                | FILTER
                | EXTRACT
                | ANY
                | NONE
                | SINGLE
                | NOW
                | WHEN
                ;

AtT : '@T' | '@t' ;

PoundValue : '#' ( 'V' | 'v' ) ( 'A' | 'a' ) ( 'L' | 'l' ) ( 'U' | 'u' ) ( 'E' | 'e' ) ;

oC_ReservedWord : ALL
                | ASC
                | ASCENDING
                | BY
                | CREATE
                | DELETE
                | DESC
                | DESCENDING
                | DETACH
                | EXISTS
                | LIMIT
                | MATCH
                | MERGE
                | ON
                | OPTIONAL
                | ORDER
                | REMOVE
                | RETURN
                | SET
                | L_SKIP
                | WHERE
                | WITH
                | UNION
                | UNWIND
                | AND
                | AS
                | CONTAINS
                | DISTINCT
                | ENDS
                | IN
                | IS
                | NOT
                | OR
                | STARTS
                | XOR
                | FALSE
                | TRUE
                | NULL
                | CONSTRAINT
                | DO
                | FOR
                | REQUIRE
                | UNIQUE
                | CASE
                | WHEN
                | THEN
                | ELSE
                | END
                | MANDATORY
                | SCALAR
                | OF
                | ADD
                | DROP
                | NOW
                | AT_TIME
                | SNAPSHOT
                | BETWEEN
                | SCOPE
                | STALE
                | DURING
                | OVERLAPS
                ;

NOW : 'NOW' ;

AT_TIME : ( 'A' | 'a' ) ( 'T' | 't' ) SP ( 'T' | 't' ) ( 'I' | 'i' ) ( 'M' | 'm' ) ( 'E' | 'e' ) ;

SNAPSHOT : ( 'S' | 's' ) ( 'N' | 'n' ) ( 'A' | 'a' ) ( 'P' | 'p') ( 'S' | 's' ) ( 'H' | 'h' ) ( 'O' | 'o') ( 'T' | 't' ) ;

BETWEEN : ( 'B' | 'b' ) ( 'E' | 'e' ) ( 'T' | 't' ) ( 'W' | 'w' ) ( 'E' | 'e' ) ( 'E' | 'e' ) ( 'N' | 'n' ) ;

SCOPE : ( 'S' | 's' ) ( 'C' | 'c' ) ( 'O' | 'o' ) ( 'P' | 'p') ( 'E' | 'e' ) ;

STALE : ( 'S' | 's' ) ( 'T' | 't' ) ( 'A' | 'a' ) ( 'L' | 'l' ) ( 'E' | 'e' ) ;

DURING : ( 'D' | 'd' ) ( 'U' | 'u' ) ( 'R' | 'r' ) ( 'I' | 'i' ) ( 'N' | 'n' ) ( 'G' | 'g' ) ;

OVERLAPS : ( 'O' | 'o' ) ( 'V' | 'v' ) ( 'E' | 'e' ) ( 'R' | 'r' ) ( 'L' | 'l' ) ( 'A' | 'a' ) ( 'P' | 'p' ) ( 'S' | 's' ) ;