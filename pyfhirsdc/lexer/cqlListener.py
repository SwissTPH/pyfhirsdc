# Generated from cql.g4 by ANTLR 4.7.2
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .cqlParser import cqlParser
else:
    from cqlParser import cqlParser

# This class defines a complete listener for a parse tree produced by cqlParser.
class cqlListener(ParseTreeListener):

    # Enter a parse tree produced by cqlParser#definition.
    def enterDefinition(self, ctx:cqlParser.DefinitionContext):
        pass

    # Exit a parse tree produced by cqlParser#definition.
    def exitDefinition(self, ctx:cqlParser.DefinitionContext):
        pass


    # Enter a parse tree produced by cqlParser#library.
    def enterLibrary(self, ctx:cqlParser.LibraryContext):
        pass

    # Exit a parse tree produced by cqlParser#library.
    def exitLibrary(self, ctx:cqlParser.LibraryContext):
        pass


    # Enter a parse tree produced by cqlParser#libraryDefinition.
    def enterLibraryDefinition(self, ctx:cqlParser.LibraryDefinitionContext):
        pass

    # Exit a parse tree produced by cqlParser#libraryDefinition.
    def exitLibraryDefinition(self, ctx:cqlParser.LibraryDefinitionContext):
        pass


    # Enter a parse tree produced by cqlParser#usingDefinition.
    def enterUsingDefinition(self, ctx:cqlParser.UsingDefinitionContext):
        pass

    # Exit a parse tree produced by cqlParser#usingDefinition.
    def exitUsingDefinition(self, ctx:cqlParser.UsingDefinitionContext):
        pass


    # Enter a parse tree produced by cqlParser#includeDefinition.
    def enterIncludeDefinition(self, ctx:cqlParser.IncludeDefinitionContext):
        pass

    # Exit a parse tree produced by cqlParser#includeDefinition.
    def exitIncludeDefinition(self, ctx:cqlParser.IncludeDefinitionContext):
        pass


    # Enter a parse tree produced by cqlParser#localIdentifier.
    def enterLocalIdentifier(self, ctx:cqlParser.LocalIdentifierContext):
        pass

    # Exit a parse tree produced by cqlParser#localIdentifier.
    def exitLocalIdentifier(self, ctx:cqlParser.LocalIdentifierContext):
        pass


    # Enter a parse tree produced by cqlParser#accessModifier.
    def enterAccessModifier(self, ctx:cqlParser.AccessModifierContext):
        pass

    # Exit a parse tree produced by cqlParser#accessModifier.
    def exitAccessModifier(self, ctx:cqlParser.AccessModifierContext):
        pass


    # Enter a parse tree produced by cqlParser#parameterDefinition.
    def enterParameterDefinition(self, ctx:cqlParser.ParameterDefinitionContext):
        pass

    # Exit a parse tree produced by cqlParser#parameterDefinition.
    def exitParameterDefinition(self, ctx:cqlParser.ParameterDefinitionContext):
        pass


    # Enter a parse tree produced by cqlParser#codesystemDefinition.
    def enterCodesystemDefinition(self, ctx:cqlParser.CodesystemDefinitionContext):
        pass

    # Exit a parse tree produced by cqlParser#codesystemDefinition.
    def exitCodesystemDefinition(self, ctx:cqlParser.CodesystemDefinitionContext):
        pass


    # Enter a parse tree produced by cqlParser#valuesetDefinition.
    def enterValuesetDefinition(self, ctx:cqlParser.ValuesetDefinitionContext):
        pass

    # Exit a parse tree produced by cqlParser#valuesetDefinition.
    def exitValuesetDefinition(self, ctx:cqlParser.ValuesetDefinitionContext):
        pass


    # Enter a parse tree produced by cqlParser#codesystems.
    def enterCodesystems(self, ctx:cqlParser.CodesystemsContext):
        pass

    # Exit a parse tree produced by cqlParser#codesystems.
    def exitCodesystems(self, ctx:cqlParser.CodesystemsContext):
        pass


    # Enter a parse tree produced by cqlParser#codesystemIdentifier.
    def enterCodesystemIdentifier(self, ctx:cqlParser.CodesystemIdentifierContext):
        pass

    # Exit a parse tree produced by cqlParser#codesystemIdentifier.
    def exitCodesystemIdentifier(self, ctx:cqlParser.CodesystemIdentifierContext):
        pass


    # Enter a parse tree produced by cqlParser#libraryIdentifier.
    def enterLibraryIdentifier(self, ctx:cqlParser.LibraryIdentifierContext):
        pass

    # Exit a parse tree produced by cqlParser#libraryIdentifier.
    def exitLibraryIdentifier(self, ctx:cqlParser.LibraryIdentifierContext):
        pass


    # Enter a parse tree produced by cqlParser#codeDefinition.
    def enterCodeDefinition(self, ctx:cqlParser.CodeDefinitionContext):
        pass

    # Exit a parse tree produced by cqlParser#codeDefinition.
    def exitCodeDefinition(self, ctx:cqlParser.CodeDefinitionContext):
        pass


    # Enter a parse tree produced by cqlParser#conceptDefinition.
    def enterConceptDefinition(self, ctx:cqlParser.ConceptDefinitionContext):
        pass

    # Exit a parse tree produced by cqlParser#conceptDefinition.
    def exitConceptDefinition(self, ctx:cqlParser.ConceptDefinitionContext):
        pass


    # Enter a parse tree produced by cqlParser#codeIdentifier.
    def enterCodeIdentifier(self, ctx:cqlParser.CodeIdentifierContext):
        pass

    # Exit a parse tree produced by cqlParser#codeIdentifier.
    def exitCodeIdentifier(self, ctx:cqlParser.CodeIdentifierContext):
        pass


    # Enter a parse tree produced by cqlParser#codesystemId.
    def enterCodesystemId(self, ctx:cqlParser.CodesystemIdContext):
        pass

    # Exit a parse tree produced by cqlParser#codesystemId.
    def exitCodesystemId(self, ctx:cqlParser.CodesystemIdContext):
        pass


    # Enter a parse tree produced by cqlParser#valuesetId.
    def enterValuesetId(self, ctx:cqlParser.ValuesetIdContext):
        pass

    # Exit a parse tree produced by cqlParser#valuesetId.
    def exitValuesetId(self, ctx:cqlParser.ValuesetIdContext):
        pass


    # Enter a parse tree produced by cqlParser#versionSpecifier.
    def enterVersionSpecifier(self, ctx:cqlParser.VersionSpecifierContext):
        pass

    # Exit a parse tree produced by cqlParser#versionSpecifier.
    def exitVersionSpecifier(self, ctx:cqlParser.VersionSpecifierContext):
        pass


    # Enter a parse tree produced by cqlParser#codeId.
    def enterCodeId(self, ctx:cqlParser.CodeIdContext):
        pass

    # Exit a parse tree produced by cqlParser#codeId.
    def exitCodeId(self, ctx:cqlParser.CodeIdContext):
        pass


    # Enter a parse tree produced by cqlParser#typeSpecifier.
    def enterTypeSpecifier(self, ctx:cqlParser.TypeSpecifierContext):
        pass

    # Exit a parse tree produced by cqlParser#typeSpecifier.
    def exitTypeSpecifier(self, ctx:cqlParser.TypeSpecifierContext):
        pass


    # Enter a parse tree produced by cqlParser#namedTypeSpecifier.
    def enterNamedTypeSpecifier(self, ctx:cqlParser.NamedTypeSpecifierContext):
        pass

    # Exit a parse tree produced by cqlParser#namedTypeSpecifier.
    def exitNamedTypeSpecifier(self, ctx:cqlParser.NamedTypeSpecifierContext):
        pass


    # Enter a parse tree produced by cqlParser#modelIdentifier.
    def enterModelIdentifier(self, ctx:cqlParser.ModelIdentifierContext):
        pass

    # Exit a parse tree produced by cqlParser#modelIdentifier.
    def exitModelIdentifier(self, ctx:cqlParser.ModelIdentifierContext):
        pass


    # Enter a parse tree produced by cqlParser#listTypeSpecifier.
    def enterListTypeSpecifier(self, ctx:cqlParser.ListTypeSpecifierContext):
        pass

    # Exit a parse tree produced by cqlParser#listTypeSpecifier.
    def exitListTypeSpecifier(self, ctx:cqlParser.ListTypeSpecifierContext):
        pass


    # Enter a parse tree produced by cqlParser#intervalTypeSpecifier.
    def enterIntervalTypeSpecifier(self, ctx:cqlParser.IntervalTypeSpecifierContext):
        pass

    # Exit a parse tree produced by cqlParser#intervalTypeSpecifier.
    def exitIntervalTypeSpecifier(self, ctx:cqlParser.IntervalTypeSpecifierContext):
        pass


    # Enter a parse tree produced by cqlParser#tupleTypeSpecifier.
    def enterTupleTypeSpecifier(self, ctx:cqlParser.TupleTypeSpecifierContext):
        pass

    # Exit a parse tree produced by cqlParser#tupleTypeSpecifier.
    def exitTupleTypeSpecifier(self, ctx:cqlParser.TupleTypeSpecifierContext):
        pass


    # Enter a parse tree produced by cqlParser#tupleElementDefinition.
    def enterTupleElementDefinition(self, ctx:cqlParser.TupleElementDefinitionContext):
        pass

    # Exit a parse tree produced by cqlParser#tupleElementDefinition.
    def exitTupleElementDefinition(self, ctx:cqlParser.TupleElementDefinitionContext):
        pass


    # Enter a parse tree produced by cqlParser#choiceTypeSpecifier.
    def enterChoiceTypeSpecifier(self, ctx:cqlParser.ChoiceTypeSpecifierContext):
        pass

    # Exit a parse tree produced by cqlParser#choiceTypeSpecifier.
    def exitChoiceTypeSpecifier(self, ctx:cqlParser.ChoiceTypeSpecifierContext):
        pass


    # Enter a parse tree produced by cqlParser#statement.
    def enterStatement(self, ctx:cqlParser.StatementContext):
        pass

    # Exit a parse tree produced by cqlParser#statement.
    def exitStatement(self, ctx:cqlParser.StatementContext):
        pass


    # Enter a parse tree produced by cqlParser#expressionDefinition.
    def enterExpressionDefinition(self, ctx:cqlParser.ExpressionDefinitionContext):
        pass

    # Exit a parse tree produced by cqlParser#expressionDefinition.
    def exitExpressionDefinition(self, ctx:cqlParser.ExpressionDefinitionContext):
        pass


    # Enter a parse tree produced by cqlParser#contextDefinition.
    def enterContextDefinition(self, ctx:cqlParser.ContextDefinitionContext):
        pass

    # Exit a parse tree produced by cqlParser#contextDefinition.
    def exitContextDefinition(self, ctx:cqlParser.ContextDefinitionContext):
        pass


    # Enter a parse tree produced by cqlParser#functionDefinition.
    def enterFunctionDefinition(self, ctx:cqlParser.FunctionDefinitionContext):
        pass

    # Exit a parse tree produced by cqlParser#functionDefinition.
    def exitFunctionDefinition(self, ctx:cqlParser.FunctionDefinitionContext):
        pass


    # Enter a parse tree produced by cqlParser#operandDefinition.
    def enterOperandDefinition(self, ctx:cqlParser.OperandDefinitionContext):
        pass

    # Exit a parse tree produced by cqlParser#operandDefinition.
    def exitOperandDefinition(self, ctx:cqlParser.OperandDefinitionContext):
        pass


    # Enter a parse tree produced by cqlParser#functionBody.
    def enterFunctionBody(self, ctx:cqlParser.FunctionBodyContext):
        pass

    # Exit a parse tree produced by cqlParser#functionBody.
    def exitFunctionBody(self, ctx:cqlParser.FunctionBodyContext):
        pass


    # Enter a parse tree produced by cqlParser#querySource.
    def enterQuerySource(self, ctx:cqlParser.QuerySourceContext):
        pass

    # Exit a parse tree produced by cqlParser#querySource.
    def exitQuerySource(self, ctx:cqlParser.QuerySourceContext):
        pass


    # Enter a parse tree produced by cqlParser#aliasedQuerySource.
    def enterAliasedQuerySource(self, ctx:cqlParser.AliasedQuerySourceContext):
        pass

    # Exit a parse tree produced by cqlParser#aliasedQuerySource.
    def exitAliasedQuerySource(self, ctx:cqlParser.AliasedQuerySourceContext):
        pass


    # Enter a parse tree produced by cqlParser#alias.
    def enterAlias(self, ctx:cqlParser.AliasContext):
        pass

    # Exit a parse tree produced by cqlParser#alias.
    def exitAlias(self, ctx:cqlParser.AliasContext):
        pass


    # Enter a parse tree produced by cqlParser#queryInclusionClause.
    def enterQueryInclusionClause(self, ctx:cqlParser.QueryInclusionClauseContext):
        pass

    # Exit a parse tree produced by cqlParser#queryInclusionClause.
    def exitQueryInclusionClause(self, ctx:cqlParser.QueryInclusionClauseContext):
        pass


    # Enter a parse tree produced by cqlParser#withClause.
    def enterWithClause(self, ctx:cqlParser.WithClauseContext):
        pass

    # Exit a parse tree produced by cqlParser#withClause.
    def exitWithClause(self, ctx:cqlParser.WithClauseContext):
        pass


    # Enter a parse tree produced by cqlParser#withoutClause.
    def enterWithoutClause(self, ctx:cqlParser.WithoutClauseContext):
        pass

    # Exit a parse tree produced by cqlParser#withoutClause.
    def exitWithoutClause(self, ctx:cqlParser.WithoutClauseContext):
        pass


    # Enter a parse tree produced by cqlParser#retrieve.
    def enterRetrieve(self, ctx:cqlParser.RetrieveContext):
        pass

    # Exit a parse tree produced by cqlParser#retrieve.
    def exitRetrieve(self, ctx:cqlParser.RetrieveContext):
        pass


    # Enter a parse tree produced by cqlParser#contextIdentifier.
    def enterContextIdentifier(self, ctx:cqlParser.ContextIdentifierContext):
        pass

    # Exit a parse tree produced by cqlParser#contextIdentifier.
    def exitContextIdentifier(self, ctx:cqlParser.ContextIdentifierContext):
        pass


    # Enter a parse tree produced by cqlParser#codePath.
    def enterCodePath(self, ctx:cqlParser.CodePathContext):
        pass

    # Exit a parse tree produced by cqlParser#codePath.
    def exitCodePath(self, ctx:cqlParser.CodePathContext):
        pass


    # Enter a parse tree produced by cqlParser#codeComparator.
    def enterCodeComparator(self, ctx:cqlParser.CodeComparatorContext):
        pass

    # Exit a parse tree produced by cqlParser#codeComparator.
    def exitCodeComparator(self, ctx:cqlParser.CodeComparatorContext):
        pass


    # Enter a parse tree produced by cqlParser#terminology.
    def enterTerminology(self, ctx:cqlParser.TerminologyContext):
        pass

    # Exit a parse tree produced by cqlParser#terminology.
    def exitTerminology(self, ctx:cqlParser.TerminologyContext):
        pass


    # Enter a parse tree produced by cqlParser#qualifier.
    def enterQualifier(self, ctx:cqlParser.QualifierContext):
        pass

    # Exit a parse tree produced by cqlParser#qualifier.
    def exitQualifier(self, ctx:cqlParser.QualifierContext):
        pass


    # Enter a parse tree produced by cqlParser#query.
    def enterQuery(self, ctx:cqlParser.QueryContext):
        pass

    # Exit a parse tree produced by cqlParser#query.
    def exitQuery(self, ctx:cqlParser.QueryContext):
        pass


    # Enter a parse tree produced by cqlParser#sourceClause.
    def enterSourceClause(self, ctx:cqlParser.SourceClauseContext):
        pass

    # Exit a parse tree produced by cqlParser#sourceClause.
    def exitSourceClause(self, ctx:cqlParser.SourceClauseContext):
        pass


    # Enter a parse tree produced by cqlParser#letClause.
    def enterLetClause(self, ctx:cqlParser.LetClauseContext):
        pass

    # Exit a parse tree produced by cqlParser#letClause.
    def exitLetClause(self, ctx:cqlParser.LetClauseContext):
        pass


    # Enter a parse tree produced by cqlParser#letClauseItem.
    def enterLetClauseItem(self, ctx:cqlParser.LetClauseItemContext):
        pass

    # Exit a parse tree produced by cqlParser#letClauseItem.
    def exitLetClauseItem(self, ctx:cqlParser.LetClauseItemContext):
        pass


    # Enter a parse tree produced by cqlParser#whereClause.
    def enterWhereClause(self, ctx:cqlParser.WhereClauseContext):
        pass

    # Exit a parse tree produced by cqlParser#whereClause.
    def exitWhereClause(self, ctx:cqlParser.WhereClauseContext):
        pass


    # Enter a parse tree produced by cqlParser#returnClause.
    def enterReturnClause(self, ctx:cqlParser.ReturnClauseContext):
        pass

    # Exit a parse tree produced by cqlParser#returnClause.
    def exitReturnClause(self, ctx:cqlParser.ReturnClauseContext):
        pass


    # Enter a parse tree produced by cqlParser#aggregateClause.
    def enterAggregateClause(self, ctx:cqlParser.AggregateClauseContext):
        pass

    # Exit a parse tree produced by cqlParser#aggregateClause.
    def exitAggregateClause(self, ctx:cqlParser.AggregateClauseContext):
        pass


    # Enter a parse tree produced by cqlParser#startingClause.
    def enterStartingClause(self, ctx:cqlParser.StartingClauseContext):
        pass

    # Exit a parse tree produced by cqlParser#startingClause.
    def exitStartingClause(self, ctx:cqlParser.StartingClauseContext):
        pass


    # Enter a parse tree produced by cqlParser#sortClause.
    def enterSortClause(self, ctx:cqlParser.SortClauseContext):
        pass

    # Exit a parse tree produced by cqlParser#sortClause.
    def exitSortClause(self, ctx:cqlParser.SortClauseContext):
        pass


    # Enter a parse tree produced by cqlParser#sortDirection.
    def enterSortDirection(self, ctx:cqlParser.SortDirectionContext):
        pass

    # Exit a parse tree produced by cqlParser#sortDirection.
    def exitSortDirection(self, ctx:cqlParser.SortDirectionContext):
        pass


    # Enter a parse tree produced by cqlParser#sortByItem.
    def enterSortByItem(self, ctx:cqlParser.SortByItemContext):
        pass

    # Exit a parse tree produced by cqlParser#sortByItem.
    def exitSortByItem(self, ctx:cqlParser.SortByItemContext):
        pass


    # Enter a parse tree produced by cqlParser#qualifiedIdentifier.
    def enterQualifiedIdentifier(self, ctx:cqlParser.QualifiedIdentifierContext):
        pass

    # Exit a parse tree produced by cqlParser#qualifiedIdentifier.
    def exitQualifiedIdentifier(self, ctx:cqlParser.QualifiedIdentifierContext):
        pass


    # Enter a parse tree produced by cqlParser#qualifiedIdentifierExpression.
    def enterQualifiedIdentifierExpression(self, ctx:cqlParser.QualifiedIdentifierExpressionContext):
        pass

    # Exit a parse tree produced by cqlParser#qualifiedIdentifierExpression.
    def exitQualifiedIdentifierExpression(self, ctx:cqlParser.QualifiedIdentifierExpressionContext):
        pass


    # Enter a parse tree produced by cqlParser#qualifierExpression.
    def enterQualifierExpression(self, ctx:cqlParser.QualifierExpressionContext):
        pass

    # Exit a parse tree produced by cqlParser#qualifierExpression.
    def exitQualifierExpression(self, ctx:cqlParser.QualifierExpressionContext):
        pass


    # Enter a parse tree produced by cqlParser#simplePath.
    def enterSimplePath(self, ctx:cqlParser.SimplePathContext):
        pass

    # Exit a parse tree produced by cqlParser#simplePath.
    def exitSimplePath(self, ctx:cqlParser.SimplePathContext):
        pass


    # Enter a parse tree produced by cqlParser#simpleLiteral.
    def enterSimpleLiteral(self, ctx:cqlParser.SimpleLiteralContext):
        pass

    # Exit a parse tree produced by cqlParser#simpleLiteral.
    def exitSimpleLiteral(self, ctx:cqlParser.SimpleLiteralContext):
        pass


    # Enter a parse tree produced by cqlParser#expression.
    def enterExpression(self, ctx:cqlParser.ExpressionContext):
        pass

    # Exit a parse tree produced by cqlParser#expression.
    def exitExpression(self, ctx:cqlParser.ExpressionContext):
        pass


    # Enter a parse tree produced by cqlParser#dateTimePrecision.
    def enterDateTimePrecision(self, ctx:cqlParser.DateTimePrecisionContext):
        pass

    # Exit a parse tree produced by cqlParser#dateTimePrecision.
    def exitDateTimePrecision(self, ctx:cqlParser.DateTimePrecisionContext):
        pass


    # Enter a parse tree produced by cqlParser#dateTimeComponent.
    def enterDateTimeComponent(self, ctx:cqlParser.DateTimeComponentContext):
        pass

    # Exit a parse tree produced by cqlParser#dateTimeComponent.
    def exitDateTimeComponent(self, ctx:cqlParser.DateTimeComponentContext):
        pass


    # Enter a parse tree produced by cqlParser#pluralDateTimePrecision.
    def enterPluralDateTimePrecision(self, ctx:cqlParser.PluralDateTimePrecisionContext):
        pass

    # Exit a parse tree produced by cqlParser#pluralDateTimePrecision.
    def exitPluralDateTimePrecision(self, ctx:cqlParser.PluralDateTimePrecisionContext):
        pass


    # Enter a parse tree produced by cqlParser#expressionTerm.
    def enterExpressionTerm(self, ctx:cqlParser.ExpressionTermContext):
        pass

    # Exit a parse tree produced by cqlParser#expressionTerm.
    def exitExpressionTerm(self, ctx:cqlParser.ExpressionTermContext):
        pass


    # Enter a parse tree produced by cqlParser#caseExpressionItem.
    def enterCaseExpressionItem(self, ctx:cqlParser.CaseExpressionItemContext):
        pass

    # Exit a parse tree produced by cqlParser#caseExpressionItem.
    def exitCaseExpressionItem(self, ctx:cqlParser.CaseExpressionItemContext):
        pass


    # Enter a parse tree produced by cqlParser#dateTimePrecisionSpecifier.
    def enterDateTimePrecisionSpecifier(self, ctx:cqlParser.DateTimePrecisionSpecifierContext):
        pass

    # Exit a parse tree produced by cqlParser#dateTimePrecisionSpecifier.
    def exitDateTimePrecisionSpecifier(self, ctx:cqlParser.DateTimePrecisionSpecifierContext):
        pass


    # Enter a parse tree produced by cqlParser#relativeQualifier.
    def enterRelativeQualifier(self, ctx:cqlParser.RelativeQualifierContext):
        pass

    # Exit a parse tree produced by cqlParser#relativeQualifier.
    def exitRelativeQualifier(self, ctx:cqlParser.RelativeQualifierContext):
        pass


    # Enter a parse tree produced by cqlParser#offsetRelativeQualifier.
    def enterOffsetRelativeQualifier(self, ctx:cqlParser.OffsetRelativeQualifierContext):
        pass

    # Exit a parse tree produced by cqlParser#offsetRelativeQualifier.
    def exitOffsetRelativeQualifier(self, ctx:cqlParser.OffsetRelativeQualifierContext):
        pass


    # Enter a parse tree produced by cqlParser#exclusiveRelativeQualifier.
    def enterExclusiveRelativeQualifier(self, ctx:cqlParser.ExclusiveRelativeQualifierContext):
        pass

    # Exit a parse tree produced by cqlParser#exclusiveRelativeQualifier.
    def exitExclusiveRelativeQualifier(self, ctx:cqlParser.ExclusiveRelativeQualifierContext):
        pass


    # Enter a parse tree produced by cqlParser#quantityOffset.
    def enterQuantityOffset(self, ctx:cqlParser.QuantityOffsetContext):
        pass

    # Exit a parse tree produced by cqlParser#quantityOffset.
    def exitQuantityOffset(self, ctx:cqlParser.QuantityOffsetContext):
        pass


    # Enter a parse tree produced by cqlParser#temporalRelationship.
    def enterTemporalRelationship(self, ctx:cqlParser.TemporalRelationshipContext):
        pass

    # Exit a parse tree produced by cqlParser#temporalRelationship.
    def exitTemporalRelationship(self, ctx:cqlParser.TemporalRelationshipContext):
        pass


    # Enter a parse tree produced by cqlParser#intervalOperatorPhrase.
    def enterIntervalOperatorPhrase(self, ctx:cqlParser.IntervalOperatorPhraseContext):
        pass

    # Exit a parse tree produced by cqlParser#intervalOperatorPhrase.
    def exitIntervalOperatorPhrase(self, ctx:cqlParser.IntervalOperatorPhraseContext):
        pass


    # Enter a parse tree produced by cqlParser#term.
    def enterTerm(self, ctx:cqlParser.TermContext):
        pass

    # Exit a parse tree produced by cqlParser#term.
    def exitTerm(self, ctx:cqlParser.TermContext):
        pass


    # Enter a parse tree produced by cqlParser#qualifiedInvocation.
    def enterQualifiedInvocation(self, ctx:cqlParser.QualifiedInvocationContext):
        pass

    # Exit a parse tree produced by cqlParser#qualifiedInvocation.
    def exitQualifiedInvocation(self, ctx:cqlParser.QualifiedInvocationContext):
        pass


    # Enter a parse tree produced by cqlParser#qualifiedFunction.
    def enterQualifiedFunction(self, ctx:cqlParser.QualifiedFunctionContext):
        pass

    # Exit a parse tree produced by cqlParser#qualifiedFunction.
    def exitQualifiedFunction(self, ctx:cqlParser.QualifiedFunctionContext):
        pass


    # Enter a parse tree produced by cqlParser#invocation.
    def enterInvocation(self, ctx:cqlParser.InvocationContext):
        pass

    # Exit a parse tree produced by cqlParser#invocation.
    def exitInvocation(self, ctx:cqlParser.InvocationContext):
        pass


    # Enter a parse tree produced by cqlParser#function.
    def enterFunction(self, ctx:cqlParser.FunctionContext):
        pass

    # Exit a parse tree produced by cqlParser#function.
    def exitFunction(self, ctx:cqlParser.FunctionContext):
        pass


    # Enter a parse tree produced by cqlParser#ratio.
    def enterRatio(self, ctx:cqlParser.RatioContext):
        pass

    # Exit a parse tree produced by cqlParser#ratio.
    def exitRatio(self, ctx:cqlParser.RatioContext):
        pass


    # Enter a parse tree produced by cqlParser#literal.
    def enterLiteral(self, ctx:cqlParser.LiteralContext):
        pass

    # Exit a parse tree produced by cqlParser#literal.
    def exitLiteral(self, ctx:cqlParser.LiteralContext):
        pass


    # Enter a parse tree produced by cqlParser#intervalSelector.
    def enterIntervalSelector(self, ctx:cqlParser.IntervalSelectorContext):
        pass

    # Exit a parse tree produced by cqlParser#intervalSelector.
    def exitIntervalSelector(self, ctx:cqlParser.IntervalSelectorContext):
        pass


    # Enter a parse tree produced by cqlParser#tupleSelector.
    def enterTupleSelector(self, ctx:cqlParser.TupleSelectorContext):
        pass

    # Exit a parse tree produced by cqlParser#tupleSelector.
    def exitTupleSelector(self, ctx:cqlParser.TupleSelectorContext):
        pass


    # Enter a parse tree produced by cqlParser#tupleElementSelector.
    def enterTupleElementSelector(self, ctx:cqlParser.TupleElementSelectorContext):
        pass

    # Exit a parse tree produced by cqlParser#tupleElementSelector.
    def exitTupleElementSelector(self, ctx:cqlParser.TupleElementSelectorContext):
        pass


    # Enter a parse tree produced by cqlParser#instanceSelector.
    def enterInstanceSelector(self, ctx:cqlParser.InstanceSelectorContext):
        pass

    # Exit a parse tree produced by cqlParser#instanceSelector.
    def exitInstanceSelector(self, ctx:cqlParser.InstanceSelectorContext):
        pass


    # Enter a parse tree produced by cqlParser#instanceElementSelector.
    def enterInstanceElementSelector(self, ctx:cqlParser.InstanceElementSelectorContext):
        pass

    # Exit a parse tree produced by cqlParser#instanceElementSelector.
    def exitInstanceElementSelector(self, ctx:cqlParser.InstanceElementSelectorContext):
        pass


    # Enter a parse tree produced by cqlParser#listSelector.
    def enterListSelector(self, ctx:cqlParser.ListSelectorContext):
        pass

    # Exit a parse tree produced by cqlParser#listSelector.
    def exitListSelector(self, ctx:cqlParser.ListSelectorContext):
        pass


    # Enter a parse tree produced by cqlParser#displayClause.
    def enterDisplayClause(self, ctx:cqlParser.DisplayClauseContext):
        pass

    # Exit a parse tree produced by cqlParser#displayClause.
    def exitDisplayClause(self, ctx:cqlParser.DisplayClauseContext):
        pass


    # Enter a parse tree produced by cqlParser#codeSelector.
    def enterCodeSelector(self, ctx:cqlParser.CodeSelectorContext):
        pass

    # Exit a parse tree produced by cqlParser#codeSelector.
    def exitCodeSelector(self, ctx:cqlParser.CodeSelectorContext):
        pass


    # Enter a parse tree produced by cqlParser#conceptSelector.
    def enterConceptSelector(self, ctx:cqlParser.ConceptSelectorContext):
        pass

    # Exit a parse tree produced by cqlParser#conceptSelector.
    def exitConceptSelector(self, ctx:cqlParser.ConceptSelectorContext):
        pass


    # Enter a parse tree produced by cqlParser#keyword.
    def enterKeyword(self, ctx:cqlParser.KeywordContext):
        pass

    # Exit a parse tree produced by cqlParser#keyword.
    def exitKeyword(self, ctx:cqlParser.KeywordContext):
        pass


    # Enter a parse tree produced by cqlParser#reservedWord.
    def enterReservedWord(self, ctx:cqlParser.ReservedWordContext):
        pass

    # Exit a parse tree produced by cqlParser#reservedWord.
    def exitReservedWord(self, ctx:cqlParser.ReservedWordContext):
        pass


    # Enter a parse tree produced by cqlParser#keywordIdentifier.
    def enterKeywordIdentifier(self, ctx:cqlParser.KeywordIdentifierContext):
        pass

    # Exit a parse tree produced by cqlParser#keywordIdentifier.
    def exitKeywordIdentifier(self, ctx:cqlParser.KeywordIdentifierContext):
        pass


    # Enter a parse tree produced by cqlParser#obsoleteIdentifier.
    def enterObsoleteIdentifier(self, ctx:cqlParser.ObsoleteIdentifierContext):
        pass

    # Exit a parse tree produced by cqlParser#obsoleteIdentifier.
    def exitObsoleteIdentifier(self, ctx:cqlParser.ObsoleteIdentifierContext):
        pass


    # Enter a parse tree produced by cqlParser#functionIdentifier.
    def enterFunctionIdentifier(self, ctx:cqlParser.FunctionIdentifierContext):
        pass

    # Exit a parse tree produced by cqlParser#functionIdentifier.
    def exitFunctionIdentifier(self, ctx:cqlParser.FunctionIdentifierContext):
        pass


    # Enter a parse tree produced by cqlParser#typeNameIdentifier.
    def enterTypeNameIdentifier(self, ctx:cqlParser.TypeNameIdentifierContext):
        pass

    # Exit a parse tree produced by cqlParser#typeNameIdentifier.
    def exitTypeNameIdentifier(self, ctx:cqlParser.TypeNameIdentifierContext):
        pass


    # Enter a parse tree produced by cqlParser#referentialIdentifier.
    def enterReferentialIdentifier(self, ctx:cqlParser.ReferentialIdentifierContext):
        pass

    # Exit a parse tree produced by cqlParser#referentialIdentifier.
    def exitReferentialIdentifier(self, ctx:cqlParser.ReferentialIdentifierContext):
        pass


    # Enter a parse tree produced by cqlParser#referentialOrTypeNameIdentifier.
    def enterReferentialOrTypeNameIdentifier(self, ctx:cqlParser.ReferentialOrTypeNameIdentifierContext):
        pass

    # Exit a parse tree produced by cqlParser#referentialOrTypeNameIdentifier.
    def exitReferentialOrTypeNameIdentifier(self, ctx:cqlParser.ReferentialOrTypeNameIdentifierContext):
        pass


    # Enter a parse tree produced by cqlParser#identifierOrFunctionIdentifier.
    def enterIdentifierOrFunctionIdentifier(self, ctx:cqlParser.IdentifierOrFunctionIdentifierContext):
        pass

    # Exit a parse tree produced by cqlParser#identifierOrFunctionIdentifier.
    def exitIdentifierOrFunctionIdentifier(self, ctx:cqlParser.IdentifierOrFunctionIdentifierContext):
        pass


    # Enter a parse tree produced by cqlParser#identifier.
    def enterIdentifier(self, ctx:cqlParser.IdentifierContext):
        pass

    # Exit a parse tree produced by cqlParser#identifier.
    def exitIdentifier(self, ctx:cqlParser.IdentifierContext):
        pass


    # Enter a parse tree produced by cqlParser#externalConstant.
    def enterExternalConstant(self, ctx:cqlParser.ExternalConstantContext):
        pass

    # Exit a parse tree produced by cqlParser#externalConstant.
    def exitExternalConstant(self, ctx:cqlParser.ExternalConstantContext):
        pass


    # Enter a parse tree produced by cqlParser#paramList.
    def enterParamList(self, ctx:cqlParser.ParamListContext):
        pass

    # Exit a parse tree produced by cqlParser#paramList.
    def exitParamList(self, ctx:cqlParser.ParamListContext):
        pass


    # Enter a parse tree produced by cqlParser#quantity.
    def enterQuantity(self, ctx:cqlParser.QuantityContext):
        pass

    # Exit a parse tree produced by cqlParser#quantity.
    def exitQuantity(self, ctx:cqlParser.QuantityContext):
        pass


    # Enter a parse tree produced by cqlParser#unit.
    def enterUnit(self, ctx:cqlParser.UnitContext):
        pass

    # Exit a parse tree produced by cqlParser#unit.
    def exitUnit(self, ctx:cqlParser.UnitContext):
        pass


