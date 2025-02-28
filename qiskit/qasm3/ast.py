# This code is part of Qiskit.
#
# (C) Copyright IBM 2021.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

# pylint: disable=invalid-name, super-init-not-called

"""QASM3 AST Nodes"""

import enum
from typing import Optional, List, Union


class ASTNode:
    """Base abstract class for AST nodes"""


class Statement(ASTNode):
    """
    statement
        : expressionStatement
        | assignmentStatement
        | classicalDeclarationStatement
        | branchingStatement
        | loopStatement
        | endStatement
        | aliasStatement
        | quantumStatement
    """

    pass


class Pragma(ASTNode):
    """
    pragma
        : '#pragma' LBRACE statement* RBRACE  // match any valid openqasm statement
    """

    def __init__(self, content):
        self.content = content


class CalibrationGrammarDeclaration(Statement):
    """
    calibrationGrammarDeclaration
        : 'defcalgrammar' calibrationGrammar SEMICOLON
    """

    def __init__(self, name):
        self.name = name


class Program(ASTNode):
    """
    program
        : header (globalStatement | statement)*
    """

    def __init__(self, header, statements=None):
        self.header = header
        self.statements = statements or []


class Header(ASTNode):
    """
    header
        : version? include*
    """

    def __init__(self, version, includes):
        self.version = version
        self.includes = includes


class Include(ASTNode):
    """
    include
        : 'include' StringLiteral SEMICOLON
    """

    def __init__(self, filename):
        self.filename = filename


class Version(ASTNode):
    """
    version
        : 'OPENQASM'(Integer | RealNumber) SEMICOLON
    """

    def __init__(self, version_number):
        self.version_number = version_number


class QuantumInstruction(ASTNode):
    """
    quantumInstruction
        : quantumGateCall
        | quantumPhase
        | quantumMeasurement
        | quantumReset
        | quantumBarrier
    """

    def __init__(self):
        pass


class Identifier(ASTNode):
    """
    Identifier : FirstIdCharacter GeneralIdCharacter* ;
    """

    def __init__(self, string):
        self.string = string


class PhysicalQubitIdentifier(Identifier):
    """
    Phisical qubit identifier
    """

    def __init__(self, identifier: Identifier):
        self.identifier = identifier


class Expression(ASTNode):
    """
    expression
        // include terminator/unary as base cases to simplify parsing
        : expressionTerminator
        | unaryExpression
        // expression hierarchy
        | xOrExpression
        | expression '|' xOrExpression
    """

    def __init__(self, something):
        self.something = something


class Range(ASTNode):
    """
    A range expression::

        <start>? (: <step>)? : <end>?
    """

    def __init__(
        self,
        start: Optional[Expression] = None,
        end: Optional[Expression] = None,
        step: Optional[Expression] = None,
    ):
        self.start = start
        self.step = step
        self.end = end


class SubscriptedIdentifier(Identifier):
    """
    An identifier with subscripted access.
    """

    def __init__(self, identifier: Identifier, subscript: Union[Range, Expression]):
        self.identifier = identifier
        self.subscript = subscript


class Constant(Expression, enum.Enum):
    """A constant value defined by the QASM 3 spec."""

    pi = enum.auto()
    euler = enum.auto()
    tau = enum.auto()


class QuantumMeasurement(ASTNode):
    """
    quantumMeasurement
        : 'measure' indexIdentifierList
    """

    def __init__(self, identifierList: List[Identifier]):
        self.identifierList = identifierList


class QuantumMeasurementAssignment(Statement):
    """
    quantumMeasurementAssignment
        : quantumMeasurement ARROW indexIdentifierList
        | indexIdentifier EQUALS quantumMeasurement  # eg: bits = measure qubits;
    """

    def __init__(self, identifier: Identifier, quantumMeasurement: QuantumMeasurement):
        self.identifier = identifier
        self.quantumMeasurement = quantumMeasurement


class ExpressionTerminator(Expression):
    """
    expressionTerminator
        : Constant
        | Integer
        | RealNumber
        | booleanLiteral
        | Identifier
        | StringLiteral
        | builtInCall
        | kernelCall
        | subroutineCall
        | timingTerminator
        | LPAREN expression RPAREN
        | expressionTerminator LBRACKET expression RBRACKET
        | expressionTerminator incrementor
    """

    pass


class Integer(Expression):
    """Integer : Digit+ ;"""


class Designator(ASTNode):
    """
    designator
        : LBRACKET expression RBRACKET
    """

    def __init__(self, expression: Expression):
        self.expression = expression


class BitDeclaration(ASTNode):
    """
    bitDeclaration
        : ( 'creg' Identifier designator? |   # NOT SUPPORTED
            'bit' designator? Identifier ) equalsExpression?
    """

    def __init__(self, identifier: Identifier, designator=None, equalsExpression=None):
        self.identifier = identifier
        self.designator = designator
        self.equalsExpression = equalsExpression


class QuantumDeclaration(ASTNode):
    """
    quantumDeclaration
        : 'qreg' Identifier designator? |   # NOT SUPPORTED
         'qubit' designator? Identifier
    """

    def __init__(self, identifier: Identifier, designator=None):
        self.identifier = identifier
        self.designator = designator


class AliasStatement(ASTNode):
    """
    aliasStatement
        : 'let' Identifier EQUALS indexIdentifier SEMICOLON
    """

    def __init__(self, identifier: Identifier, concatenation: List[Identifier]):
        self.identifier = identifier
        self.concatenation = concatenation


class QuantumGateModifierName(enum.Enum):
    """The names of the allowed modifiers of quantum gates."""

    ctrl = enum.auto()
    negctrl = enum.auto()
    inv = enum.auto()
    pow = enum.auto()


class QuantumGateModifier(ASTNode):
    """A modifier of a gate. For example, in ``ctrl @ x $0``, the ``ctrl @`` is the modifier."""

    def __init__(self, modifier: QuantumGateModifierName, argument: Optional[Expression] = None):
        self.modifier = modifier
        self.argument = argument


class QuantumGateCall(QuantumInstruction):
    """
    quantumGateCall
        : quantumGateModifier* quantumGateName ( LPAREN expressionList? RPAREN )? indexIdentifierList
    """

    def __init__(
        self,
        quantumGateName: Identifier,
        indexIdentifierList: List[Identifier],
        parameters: List[Expression] = None,
        modifiers: Optional[List[QuantumGateModifier]] = None,
    ):
        self.quantumGateName = quantumGateName
        self.indexIdentifierList = indexIdentifierList
        self.parameters = parameters or []
        self.modifiers = modifiers or []


class SubroutineCall(ExpressionTerminator):
    """
    subroutineCall
        : Identifier ( LPAREN expressionList? RPAREN )? indexIdentifierList
    """

    def __init__(
        self,
        identifier: Identifier,
        indexIdentifierList: List[Identifier],
        expressionList: List[Expression] = None,
    ):
        self.identifier = identifier
        self.indexIdentifierList = indexIdentifierList
        self.expressionList = expressionList or []


class QuantumBarrier(QuantumInstruction):
    """
    quantumBarrier
        : 'barrier' indexIdentifierList
    """

    def __init__(self, indexIdentifierList: List[Identifier]):
        self.indexIdentifierList = indexIdentifierList


class QuantumReset(QuantumInstruction):
    """A built-in ``reset q0;`` statement."""

    def __init__(self, identifier: Identifier):
        self.identifier = identifier


class ProgramBlock(ASTNode):
    """
    programBlock
        : statement | controlDirective
        | LBRACE(statement | controlDirective) * RBRACE
    """

    def __init__(self, statements: List[Statement]):
        self.statements = statements


class ReturnStatement(ASTNode):  # TODO probably should be a subclass of ControlDirective
    """
    returnStatement
        : 'return' ( expression | quantumMeasurement )? SEMICOLON;
    """

    def __init__(self, expression=None):
        self.expression = expression


class QuantumBlock(ProgramBlock):
    """
    quantumBlock
        : LBRACE ( quantumStatement | quantumLoop )* RBRACE
    """

    pass


class SubroutineBlock(ProgramBlock):
    """
    subroutineBlock
        : LBRACE statement* returnStatement? RBRACE
    """

    pass


class QuantumArgument(QuantumDeclaration):
    """
    quantumArgument
        : 'qreg' Identifier designator? | 'qubit' designator? Identifier
    """


class QuantumGateSignature(ASTNode):
    """
    quantumGateSignature
        : quantumGateName ( LPAREN identifierList? RPAREN )? identifierList
    """

    def __init__(
        self,
        name: Identifier,
        qargList: List[Identifier],
        params: Optional[List[Identifier]] = None,
    ):
        self.name = name
        self.qargList = qargList
        self.params = params


class QuantumGateDefinition(Statement):
    """
    quantumGateDefinition
        : 'gate' quantumGateSignature quantumBlock
    """

    def __init__(self, quantumGateSignature: QuantumGateSignature, quantumBlock: QuantumBlock):
        self.quantumGateSignature = quantumGateSignature
        self.quantumBlock = quantumBlock


class SubroutineDefinition(Statement):
    """
    subroutineDefinition
        : 'def' Identifier LPAREN anyTypeArgumentList? RPAREN
        returnSignature? subroutineBlock
    """

    def __init__(
        self,
        identifier: Identifier,
        subroutineBlock: SubroutineBlock,
        arguments=None,  # [ClassicalArgument]
    ):
        self.identifier = identifier
        self.arguments = arguments or []
        self.subroutineBlock = subroutineBlock


class CalibrationArgument(ASTNode):
    """
    calibrationArgumentList
        : classicalArgumentList | expressionList
    """

    pass


class CalibrationDefinition(Statement):
    """
    calibrationDefinition
        : 'defcal' Identifier
        ( LPAREN calibrationArgumentList? RPAREN )? identifierList
        returnSignature? LBRACE .*? RBRACE  // for now, match anything inside body
        ;
    """

    def __init__(
        self,
        name: Identifier,
        identifierList: List[Identifier],
        calibrationArgumentList: Optional[List[CalibrationArgument]] = None,
    ):
        self.name = name
        self.identifierList = identifierList
        self.calibrationArgumentList = calibrationArgumentList or []


class BooleanExpression(ASTNode):
    """
    programBlock
        : statement | controlDirective
        | LBRACE(statement | controlDirective) * RBRACE
    """


class RelationalOperator(ASTNode):
    """Relational operator"""


class LtOperator(RelationalOperator):
    """Less than relational operator"""


class EqualsOperator(RelationalOperator):
    """Greater than relational operator"""


class GtOperator(RelationalOperator):
    """Greater than relational operator"""


class ComparisonExpression(BooleanExpression):
    """
    comparisonExpression
        : expression  // if (expression)
        | expression relationalOperator expression
    """

    def __init__(self, left: Expression, relation: RelationalOperator, right: Expression):
        self.left = left
        self.relation = relation
        self.right = right


class BranchingStatement(Statement):
    """
    branchingStatement
        : 'if' LPAREN booleanExpression RPAREN programBlock ( 'else' programBlock )?
    """

    def __init__(
        self, booleanExpression: BooleanExpression, programTrue: ProgramBlock, programFalse=None
    ):
        self.booleanExpression = booleanExpression
        self.programTrue = programTrue
        self.programFalse = programFalse


class IOModifier(enum.Enum):
    """IO Modifier object"""

    input = enum.auto()
    output = enum.auto()


class IO(ASTNode):
    """UNDEFINED in the grammar yet"""

    def __init__(self, modifier: IOModifier, input_type, input_variable):
        self.modifier = modifier
        self.type = input_type
        self.variable = input_variable
