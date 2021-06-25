from enum import Enum
from typing import Any, Generator, Iterable, Iterator, NamedTuple, Tuple, Union
from string import digits


# ----------------------------
# region: Tokenizing


class TokenType(Enum):
    NUMBER = 0
    PLUS = 1
    MINUS = 2
    STAR = 3
    SLASH = 4
    CARET = 5
    LPAREN = 6
    RPAREN = 7
    EOF = 8
    pass


class Token(NamedTuple):
    type: TokenType
    value: Any = None

    def __repr__(self) -> str:
        if self.value is None:
            return f"({self.type.name})"
        return f"({self.type.name}:{self.value})"


def generate_tokens(text: Iterable[str]) -> Generator[Token, None, None]:
    textiter = iter(text)
    for char in textiter:
        num = None

        if char in digits:  # numbers
            num = char
            for char in textiter:
                if char not in digits:
                    break
                num += char
            yield Token(TokenType.NUMBER, float(num))

        if char in " \n\t":  # skip whitespace
            continue

        # operators
        if char == "+":
            yield Token(TokenType.PLUS)
        elif char == "-":
            yield Token(TokenType.MINUS)
        elif char == "*":
            yield Token(TokenType.STAR)
        elif char == "/":
            yield Token(TokenType.SLASH)
        elif char == "^":
            yield Token(TokenType.CARET)
        elif num is None:
            raise Exception("Unrecognized symbol: '%s'" % char)


# endregion #


# ----------------------------
# region: Parsing


Node = Union["NumberNode", "BinaryOpNode", "UnaryOpNode"]


class NumberNode(NamedTuple):
    value: float

    def __repr__(self) -> str:
        return f"{self.value}"


class BinaryOpNode(NamedTuple):
    left: Node
    op: Token
    right: Node

    def __repr__(self) -> str:
        return f"({self.left}, {self.op}, {self.right})"


class UnaryOpNode(NamedTuple):
    op: Token
    node: Node

    def __repr__(self) -> str:
        return f"({self.op}, {self.node})"


def expr(tokens: Iterator) -> Tuple[Token, Node]:
    """expr   : term ((PLUS|MINUS) term)*"""

    token, left = term(tokens)

    while token.type in (TokenType.PLUS, TokenType.MINUS):
        optok = token
        token, right = term(tokens)
        left = BinaryOpNode(left, optok, right)

    return token, left


def term(tokens: Iterator) -> Tuple[Token, Node]:
    """term   : factor ((SLASH|STAR) factor)*"""

    token, left = factor(tokens)

    while token.type in (TokenType.STAR, TokenType.SLASH):
        optok = token
        token, right = factor(tokens)
        left = BinaryOpNode(left, optok, right)

    return token, left


def factor(tokens: Iterator) -> Tuple[Token, Node]:
    """
    factor : (PLUS|MINUS) factor
           | power
    """

    token = next(tokens, Token(TokenType.EOF))

    if token.type in (TokenType.PLUS, TokenType.MINUS):
        optok = token
        token, right = factor(tokens)
        right = UnaryOpNode(optok, right)
        return token, right

    return power(tokens, token)


def power(tokens: Iterator, token: Token) -> Tuple[Token, Node]:
    """power  : atom (CARET factor)*"""

    token, left = atom(tokens, token)

    while token.type is TokenType.CARET:
        optok = token
        token, right = factor(tokens)
        left = BinaryOpNode(left, optok, right)

    return token, left


def atom(tokens: Iterator, token: Token) -> Tuple[Token, Node]:
    """
    atom   : NUMBER
           | LPAREN expr RPAREN
    """

    if token.type is TokenType.NUMBER:
        num = token
        token = next(tokens, Token(TokenType.EOF))
        return token, NumberNode(num.value)

    if token.type is TokenType.LPAREN:
        token, result = expr(tokens)
        if token.type is not TokenType.RPAREN:
            raise Exception("Missing )")
        token = next(tokens, Token(TokenType.EOF))
        return token, result

    raise Exception("Error")


# endregion #


# ----------------------------
# region: Interpreting


def visit(node: Node):
    method = f"visit_{node.__class__.__name__}"

    _dict = globals()
    if method in _dict:
        return _dict[method](node)

    raise Exception(f"visit: Error {type(node)}")


def visit_NumberNode(node: NumberNode):
    return node.value


def visit_BinaryOpNode(node: BinaryOpNode):
    if node.op.type is TokenType.PLUS:
        return visit(node.left) + visit(node.right)
    if node.op.type is TokenType.MINUS:
        return visit(node.left) - visit(node.right)
    if node.op.type is TokenType.STAR:
        return visit(node.left) * visit(node.right)
    if node.op.type is TokenType.SLASH:
        return visit(node.left) / visit(node.right)
    if node.op.type is TokenType.CARET:
        return visit(node.left) ** visit(node.right)


def visit_UnaryOpNode(node: UnaryOpNode):
    if node.op.type is TokenType.PLUS:
        return visit(node.node)
    if node.op.type is TokenType.MINUS:
        return -visit(node.node)


# endregion #


def main(stdin):
    print("Press <Ctrl-D> to Terminate input")
    text = stdin.read()
    if not text:
        return
    tokens = generate_tokens(text)
    last_token, node = expr(tokens)
    assert last_token.type is TokenType.EOF
    value = visit(node)
    print(value)


if __name__ == "__main__":
    from sys import stdin
    main(stdin)