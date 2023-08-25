# Generated from cql.g4 by ANTLR 4.7.2
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .cqlParser import cqlParser
else:
    from cqlParser import cqlParser

# This class defines a complete generic visitor for a parse tree produced by cqlParser.

class cqlVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by cqlParser#definition.
    def visitDefinition(self, ctx:cqlParser.DefinitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#library.
    def visitLibrary(self, ctx:cqlParser.LibraryContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#libraryDefinition.
    def visitLibraryDefinition(self, ctx:cqlParser.LibraryDefinitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#usingDefinition.
    def visitUsingDefinition(self, ctx:cqlParser.UsingDefinitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#includeDefinition.
    def visitIncludeDefinition(self, ctx:cqlParser.IncludeDefinitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#localIdentifier.
    def visitLocalIdentifier(self, ctx:cqlParser.LocalIdentifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#accessModifier.
    def visitAccessModifier(self, ctx:cqlParser.AccessModifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#parameterDefinition.
    def visitParameterDefinition(self, ctx:cqlParser.ParameterDefinitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#codesystemDefinition.
    def visitCodesystemDefinition(self, ctx:cqlParser.CodesystemDefinitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#valuesetDefinition.
    def visitValuesetDefinition(self, ctx:cqlParser.ValuesetDefinitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#codesystems.
    def visitCodesystems(self, ctx:cqlParser.CodesystemsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#codesystemIdentifier.
    def visitCodesystemIdentifier(self, ctx:cqlParser.CodesystemIdentifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#libraryIdentifier.
    def visitLibraryIdentifier(self, ctx:cqlParser.LibraryIdentifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#codeDefinition.
    def visitCodeDefinition(self, ctx:cqlParser.CodeDefinitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#conceptDefinition.
    def visitConceptDefinition(self, ctx:cqlParser.ConceptDefinitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#codeIdentifier.
    def visitCodeIdentifier(self, ctx:cqlParser.CodeIdentifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#codesystemId.
    def visitCodesystemId(self, ctx:cqlParser.CodesystemIdContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#valuesetId.
    def visitValuesetId(self, ctx:cqlParser.ValuesetIdContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#versionSpecifier.
    def visitVersionSpecifier(self, ctx:cqlParser.VersionSpecifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#codeId.
    def visitCodeId(self, ctx:cqlParser.CodeIdContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#typeSpecifier.
    def visitTypeSpecifier(self, ctx:cqlParser.TypeSpecifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#namedTypeSpecifier.
    def visitNamedTypeSpecifier(self, ctx:cqlParser.NamedTypeSpecifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#modelIdentifier.
    def visitModelIdentifier(self, ctx:cqlParser.ModelIdentifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#listTypeSpecifier.
    def visitListTypeSpecifier(self, ctx:cqlParser.ListTypeSpecifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#intervalTypeSpecifier.
    def visitIntervalTypeSpecifier(self, ctx:cqlParser.IntervalTypeSpecifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#tupleTypeSpecifier.
    def visitTupleTypeSpecifier(self, ctx:cqlParser.TupleTypeSpecifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#tupleElementDefinition.
    def visitTupleElementDefinition(self, ctx:cqlParser.TupleElementDefinitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#choiceTypeSpecifier.
    def visitChoiceTypeSpecifier(self, ctx:cqlParser.ChoiceTypeSpecifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#statement.
    def visitStatement(self, ctx:cqlParser.StatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#expressionDefinition.
    def visitExpressionDefinition(self, ctx:cqlParser.ExpressionDefinitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#contextDefinition.
    def visitContextDefinition(self, ctx:cqlParser.ContextDefinitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#functionDefinition.
    def visitFunctionDefinition(self, ctx:cqlParser.FunctionDefinitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#operandDefinition.
    def visitOperandDefinition(self, ctx:cqlParser.OperandDefinitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#functionBody.
    def visitFunctionBody(self, ctx:cqlParser.FunctionBodyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#querySource.
    def visitQuerySource(self, ctx:cqlParser.QuerySourceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#aliasedQuerySource.
    def visitAliasedQuerySource(self, ctx:cqlParser.AliasedQuerySourceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#alias.
    def visitAlias(self, ctx:cqlParser.AliasContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#queryInclusionClause.
    def visitQueryInclusionClause(self, ctx:cqlParser.QueryInclusionClauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#withClause.
    def visitWithClause(self, ctx:cqlParser.WithClauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#withoutClause.
    def visitWithoutClause(self, ctx:cqlParser.WithoutClauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#retrieve.
    def visitRetrieve(self, ctx:cqlParser.RetrieveContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#contextIdentifier.
    def visitContextIdentifier(self, ctx:cqlParser.ContextIdentifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#codePath.
    def visitCodePath(self, ctx:cqlParser.CodePathContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#codeComparator.
    def visitCodeComparator(self, ctx:cqlParser.CodeComparatorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#terminology.
    def visitTerminology(self, ctx:cqlParser.TerminologyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#qualifier.
    def visitQualifier(self, ctx:cqlParser.QualifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#query.
    def visitQuery(self, ctx:cqlParser.QueryContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#sourceClause.
    def visitSourceClause(self, ctx:cqlParser.SourceClauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#letClause.
    def visitLetClause(self, ctx:cqlParser.LetClauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#letClauseItem.
    def visitLetClauseItem(self, ctx:cqlParser.LetClauseItemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#whereClause.
    def visitWhereClause(self, ctx:cqlParser.WhereClauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#returnClause.
    def visitReturnClause(self, ctx:cqlParser.ReturnClauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#aggregateClause.
    def visitAggregateClause(self, ctx:cqlParser.AggregateClauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#startingClause.
    def visitStartingClause(self, ctx:cqlParser.StartingClauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#sortClause.
    def visitSortClause(self, ctx:cqlParser.SortClauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#sortDirection.
    def visitSortDirection(self, ctx:cqlParser.SortDirectionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#sortByItem.
    def visitSortByItem(self, ctx:cqlParser.SortByItemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#qualifiedIdentifier.
    def visitQualifiedIdentifier(self, ctx:cqlParser.QualifiedIdentifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#qualifiedIdentifierExpression.
    def visitQualifiedIdentifierExpression(self, ctx:cqlParser.QualifiedIdentifierExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#qualifierExpression.
    def visitQualifierExpression(self, ctx:cqlParser.QualifierExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#simplePath.
    def visitSimplePath(self, ctx:cqlParser.SimplePathContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#simpleLiteral.
    def visitSimpleLiteral(self, ctx:cqlParser.SimpleLiteralContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#expression.
    def visitExpression(self, ctx:cqlParser.ExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#dateTimePrecision.
    def visitDateTimePrecision(self, ctx:cqlParser.DateTimePrecisionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#dateTimeComponent.
    def visitDateTimeComponent(self, ctx:cqlParser.DateTimeComponentContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#pluralDateTimePrecision.
    def visitPluralDateTimePrecision(self, ctx:cqlParser.PluralDateTimePrecisionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#expressionTerm.
    def visitExpressionTerm(self, ctx:cqlParser.ExpressionTermContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#caseExpressionItem.
    def visitCaseExpressionItem(self, ctx:cqlParser.CaseExpressionItemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#dateTimePrecisionSpecifier.
    def visitDateTimePrecisionSpecifier(self, ctx:cqlParser.DateTimePrecisionSpecifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#relativeQualifier.
    def visitRelativeQualifier(self, ctx:cqlParser.RelativeQualifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#offsetRelativeQualifier.
    def visitOffsetRelativeQualifier(self, ctx:cqlParser.OffsetRelativeQualifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#exclusiveRelativeQualifier.
    def visitExclusiveRelativeQualifier(self, ctx:cqlParser.ExclusiveRelativeQualifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#quantityOffset.
    def visitQuantityOffset(self, ctx:cqlParser.QuantityOffsetContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#temporalRelationship.
    def visitTemporalRelationship(self, ctx:cqlParser.TemporalRelationshipContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#intervalOperatorPhrase.
    def visitIntervalOperatorPhrase(self, ctx:cqlParser.IntervalOperatorPhraseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#term.
    def visitTerm(self, ctx:cqlParser.TermContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#qualifiedInvocation.
    def visitQualifiedInvocation(self, ctx:cqlParser.QualifiedInvocationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#qualifiedFunction.
    def visitQualifiedFunction(self, ctx:cqlParser.QualifiedFunctionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#invocation.
    def visitInvocation(self, ctx:cqlParser.InvocationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#function.
    def visitFunction(self, ctx:cqlParser.FunctionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#ratio.
    def visitRatio(self, ctx:cqlParser.RatioContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#literal.
    def visitLiteral(self, ctx:cqlParser.LiteralContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#intervalSelector.
    def visitIntervalSelector(self, ctx:cqlParser.IntervalSelectorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#tupleSelector.
    def visitTupleSelector(self, ctx:cqlParser.TupleSelectorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#tupleElementSelector.
    def visitTupleElementSelector(self, ctx:cqlParser.TupleElementSelectorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#instanceSelector.
    def visitInstanceSelector(self, ctx:cqlParser.InstanceSelectorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#instanceElementSelector.
    def visitInstanceElementSelector(self, ctx:cqlParser.InstanceElementSelectorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#listSelector.
    def visitListSelector(self, ctx:cqlParser.ListSelectorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#displayClause.
    def visitDisplayClause(self, ctx:cqlParser.DisplayClauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#codeSelector.
    def visitCodeSelector(self, ctx:cqlParser.CodeSelectorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#conceptSelector.
    def visitConceptSelector(self, ctx:cqlParser.ConceptSelectorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#keyword.
    def visitKeyword(self, ctx:cqlParser.KeywordContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#reservedWord.
    def visitReservedWord(self, ctx:cqlParser.ReservedWordContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#keywordIdentifier.
    def visitKeywordIdentifier(self, ctx:cqlParser.KeywordIdentifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#obsoleteIdentifier.
    def visitObsoleteIdentifier(self, ctx:cqlParser.ObsoleteIdentifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#functionIdentifier.
    def visitFunctionIdentifier(self, ctx:cqlParser.FunctionIdentifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#typeNameIdentifier.
    def visitTypeNameIdentifier(self, ctx:cqlParser.TypeNameIdentifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#referentialIdentifier.
    def visitReferentialIdentifier(self, ctx:cqlParser.ReferentialIdentifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#referentialOrTypeNameIdentifier.
    def visitReferentialOrTypeNameIdentifier(self, ctx:cqlParser.ReferentialOrTypeNameIdentifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#identifierOrFunctionIdentifier.
    def visitIdentifierOrFunctionIdentifier(self, ctx:cqlParser.IdentifierOrFunctionIdentifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#identifier.
    def visitIdentifier(self, ctx:cqlParser.IdentifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#externalConstant.
    def visitExternalConstant(self, ctx:cqlParser.ExternalConstantContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#paramList.
    def visitParamList(self, ctx:cqlParser.ParamListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#quantity.
    def visitQuantity(self, ctx:cqlParser.QuantityContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#unit.
    def visitUnit(self, ctx:cqlParser.UnitContext):
        return self.visitChildren(ctx)



del cqlParser