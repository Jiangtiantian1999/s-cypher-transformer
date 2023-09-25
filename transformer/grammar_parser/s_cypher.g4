grammar s_cypher;
import cypher;

oC_Query : oC_RegularQuery
         | oC_StandaloneCall
         | s_TimeWindowLimit
         ;

oC_Match : ( OPTIONAL SP )? MATCH SP? oC_Pattern ( SP? ( s_AtTime | s_Between ) )? ( SP? oC_Where )? ;

oC_UpdatingClause : ( oC_Create | oC_Merge | oC_Delete | oC_Set | oC_Remove | s_Stale) ( SP? s_AtTime )? ;

oC_SetItem : ( oC_Variable SP? s_AtTElement )
           | ( oC_Variable ( SP? s_AtTElement )? '.' s_SetPropertyItemOne )
           | ( oC_Variable ( SP? s_AtTElement )? '.' s_SetPropertyItemTwo SP? s_SetValueItem )
           | ( oC_Variable ( SP? s_AtTElement )? '.' s_SetPropertyItemTwo SP? '=' SP? s_SetValueItemExpression )
           | ( oC_PropertyExpression SP? '=' SP? oC_Expression )
           | ( oC_Variable SP? '=' SP? oC_Expression )
           | ( oC_Variable SP? '+=' SP? oC_Expression )
           | ( oC_Variable SP? oC_NodeLabels )
           ;

s_SetPropertyItemOne : oC_PropertyKeyName SP? s_AtTElement ;

s_SetPropertyItemTwo : oC_PropertyKeyName ( SP? s_AtTElement )? ;

s_SetValueItem : PoundValue SP? s_AtTElement ;

s_SetValueItemExpression : oC_Expression ( SP? s_AtTElement )? ;


s_Stale : STALE SP? s_StaleItem ( SP? ',' SP? s_StaleItem )* ;

s_StaleItem : oC_Expression '.' oC_PropertyKeyName SP? PoundValue
            | oC_Expression
            ;

oC_Delete :  ( DETACH SP )? DELETE SP? s_DeleteItem ( SP? ',' SP? s_DeleteItem )* ;

s_DeleteItem : oC_Expression '.' oC_PropertyKeyName SP? PoundValue
             | oC_Expression
             ;

s_AtTime : AT_TIME SP? oC_Expression;

s_Between : BETWEEN SP? oC_Expression;

s_TimeWindowLimit : s_Snapshot
                  | s_Scope
                  ;

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

s_PropertiesPattern : '{' SP? ( s_PropertyNode ':' s_ValueNode ( ',' SP? s_PropertyNode ':' s_ValueNode )* )? '}' ;

s_PropertyNode : oC_PropertyKeyName SP? ( s_AtTElement SP? )? ;

s_ValueNode : SP? oC_Expression SP? ( s_AtTElement SP? )? ;

oC_RelationshipDetail : '[' SP? ( oC_Variable SP? )? ( oC_RelationshipTypes SP? )? oC_RangeLiteral? ( s_AtTElement SP? )? ( oC_Properties SP? )? ']' ;

oC_StringListNullPredicateExpression : oC_AddOrSubtractExpression ( s_TimePredicateExpression | oC_StringPredicateExpression | oC_ListPredicateExpression | oC_NullPredicateExpression )? ;

oC_ListOperatorExpression : ( oC_PropertyOrLabelsExpression | s_AtTExpression ) ( oC_SingleIndexExpression | oC_DoubleIndexExpression )* ;

oC_SingleIndexExpression : SP? '[' oC_Expression ']' ;

oC_DoubleIndexExpression : SP? '[' oC_Expression? '..' oC_Expression? ']' ;

s_AtTExpression : oC_Atom ( ( SP? oC_PropertyLookup )+ ( SP? PoundValue )? )? SP? oC_PropertyLookupTime ;

oC_PropertyLookupTime: AtT ( SP? oC_PropertyLookup )* ;

s_TimePredicateExpression : SP ( DURING | OVERLAPS ) SP oC_AddOrSubtractExpression ;

s_AtTElement : AtT SP? '(' SP? s_TimePointLiteral SP? ',' SP? ( s_TimePointLiteral | NOW ) SP? ')';

s_TimePointLiteral : StringLiteral
                   | oC_MapLiteral
                   ;

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

AT_TIME : ( 'A' | 'a' ) ( 'T' | 't' ) '_' ( 'T' | 't' ) ( 'I' | 'i' ) ( 'M' | 'm' ) ( 'E' | 'e' ) ;

SNAPSHOT : ( 'S' | 's' ) ( 'N' | 'n' ) ( 'A' | 'a' ) ( 'P' | 'p') ( 'S' | 's' ) ( 'H' | 'h' ) ( 'O' | 'o') ( 'T' | 't' ) ;

BETWEEN : ( 'B' | 'b' ) ( 'E' | 'e' ) ( 'T' | 't' ) ( 'W' | 'w' ) ( 'E' | 'e' ) ( 'E' | 'e' ) ( 'N' | 'n' ) ;

SCOPE : ( 'S' | 's' ) ( 'C' | 'c' ) ( 'O' | 'o' ) ( 'P' | 'p') ( 'E' | 'e' ) ;

STALE : ( 'S' | 's' ) ( 'T' | 't' ) ( 'A' | 'a' ) ( 'L' | 'l' ) ( 'E' | 'e' ) ;

DURING : ( 'D' | 'd' ) ( 'U' | 'u' ) ( 'R' | 'r' ) ( 'I' | 'i' ) ( 'N' | 'n' ) ( 'G' | 'g' ) ;

OVERLAPS : ( 'O' | 'o' ) ( 'V' | 'v' ) ( 'E' | 'e' ) ( 'R' | 'r' ) ( 'L' | 'l' ) ( 'A' | 'a' ) ( 'P' | 'p' ) ( 'S' | 's' ) ;
