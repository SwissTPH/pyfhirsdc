# Generated from fhirpath.g4 by ANTLR 4.7.2
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .fhirpathParser import fhirpathParser
else:
    from fhirpathParser import fhirpathParser

# This class defines a complete generic visitor for a parse tree produced by fhirpathParser.

class fhirpathVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by fhirpathParser#expression.
    def visitExpression(self, ctx:fhirpathParser.ExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by fhirpathParser#pse1.
    def visitPse1(self, ctx:fhirpathParser.Pse1Context):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by fhirpathParser#pse2.
    def visitPse2(self, ctx:fhirpathParser.Pse2Context):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by fhirpathParser#term.
    def visitTerm(self, ctx:fhirpathParser.TermContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by fhirpathParser#literal.
    def visitLiteral(self, ctx:fhirpathParser.LiteralContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by fhirpathParser#externalConstant.
    def visitExternalConstant(self, ctx:fhirpathParser.ExternalConstantContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by fhirpathParser#invocation.
    def visitInvocation(self, ctx:fhirpathParser.InvocationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by fhirpathParser#function.
    def visitFunction(self, ctx:fhirpathParser.FunctionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by fhirpathParser#paramList.
    def visitParamList(self, ctx:fhirpathParser.ParamListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by fhirpathParser#quantity.
    def visitQuantity(self, ctx:fhirpathParser.QuantityContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by fhirpathParser#unit.
    def visitUnit(self, ctx:fhirpathParser.UnitContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by fhirpathParser#dateTimePrecision.
    def visitDateTimePrecision(self, ctx:fhirpathParser.DateTimePrecisionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by fhirpathParser#pluralDateTimePrecision.
    def visitPluralDateTimePrecision(self, ctx:fhirpathParser.PluralDateTimePrecisionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by fhirpathParser#typeSpecifier.
    def visitTypeSpecifier(self, ctx:fhirpathParser.TypeSpecifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by fhirpathParser#qualifiedIdentifier.
    def visitQualifiedIdentifier(self, ctx:fhirpathParser.QualifiedIdentifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by fhirpathParser#identifier.
    def visitIdentifier(self, ctx:fhirpathParser.IdentifierContext):
        return self.visitChildren(ctx)



del fhirpathParser