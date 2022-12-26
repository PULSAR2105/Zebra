import re

import lexer
import errors as err

operators = ["=", "+", "-", "*", "/", "//", "%", "^", "<", ">", "<=", ">=", "!=", "==","and", "or", "xor", "in"]
operators_priority = [["="],
                      ["and", "or", "xor", "in"],
                      ["<", ">", "<=", ">=", "!=", "=="],
                      ["+", "-"],
                      ["*", "/", "//", "%"],
                      ["^"]]

opening_characters = ["(", "[", "{"]
closing_characters = [")", "]", "}"]
opening_closing_characters = opening_characters + closing_characters

# the lowest level of brackets is determined
def determine_lower_para_influences(tokens):
    parentheses_influence = 0
    influences = []

    for t in tokens:
        if t == "(":
            parentheses_influence += 1
            influences.append(parentheses_influence)
        elif t == ")":
            influences.append(parentheses_influence)
            parentheses_influence -= 1
        else:
            influences.append(parentheses_influence)

    # si le niveau d'influence des parenthèses est supérieur à 0
    # on soustrait 1, n fois
    if min(influences) > 0:
        for i in range(min(influences)):
            tokens = tokens[1:-1]
            for iflu in range(len(influences)):
                influences[iflu] = influences[iflu] - 1

        return tokens, min(influences), influences

    return tokens, min(influences), influences

# search for the lowest priority operator outside the parentheses
def search_min_priority(tokens, operators, operators_priority):
    tokens, min_para_influence, influences = determine_lower_para_influences(tokens)

    # we check if there are any operators left
    good = False
    for token in tokens:
        if token in operators:
            good = True
    if not good:
        return None, -1

    # the lowest priority operator is sought
    for operators in operators_priority:
        for i in range(len(tokens)):
            for operator in operators:
                if tokens[len(tokens) - 1 - i] in operators:
                    if tokens[len(tokens) - 1 - i] == operator and influences[len(tokens) - 1 - i] == min_para_influence:
                        return operator, len(tokens) - 1 - i

# we search if tokens list are a big function, ex: ["sin", "(", "10", ")"]
def if_one_function(tokens):
    # first check
    if type(tokens) == list and len(tokens) > 1:
        if type(tokens[0]) == str:
            if re.match(r"\w+", tokens[0]) and tokens[1] == "(" and  not tokens[0] in operators:
                # if the last parenthesis is to the function^
                influ = 0
                for i in range(1, len(tokens)):
                    if tokens[i] == "(":
                        influ += 1
                    if tokens[i] == ")":
                        influ -= 1

                    if influ == 0 and i == len(tokens) - 1:
                        return True
                    elif influ == 0 and i != len(tokens) - 1:
                        return False
            else:
                return False
        else:
            return False
    else:
        return False

# Parser
def line_parser(tokens):

    # we check for the presence of functions
    if if_one_function(tokens):
        # we get the function and its arguments
        action = tokens[0]

        # get arguments
        arguments = []
        i = 2 # 2 because we skip the fonction name and the first "("
        check_point = 2
        while tokens[i] != ")":
            if tokens[i] in [","]:
                arguments.append(tokens[check_point:i])
                check_point = i+1
            i += 1

        if tokens[check_point:i] != []:
            arguments.append(tokens[check_point:i])

        # arguments are parsed
        for i in range(len(arguments)):
            arguments[i] = line_parser(arguments[i])

        # "*" is for unpack all elements
        return [action, *arguments]

    # we find the operator who is made in LAST
    operator, pos = search_min_priority(tokens, operators, operators_priority)

    tokens, min_para_influence, influences = determine_lower_para_influences(tokens)

    # if there are no operators left
    if operator == None and pos == -1:
        return tokens[0]
    elif operator == "-" and pos == 0:
        action = operator
        arguments = [tokens[1:]]
        arguments[0] = line_parser(arguments[0])
    else:
        # the arguments are listed according to the operator/action
        action = operator
        arguments = [tokens[:pos], tokens[pos + 1:]]

        arguments[0] = line_parser(arguments[0])
        arguments[1] = line_parser(arguments[1])

    # "*" is for unpack all elements
    return [action, *arguments]

# we create the tree of an entire file
def parser_global(lines, indent_level):
    global_tree = []
    i = 0
    while i < len(lines) and lines[i].startswith(" " * indent_level):
        # we get the line
        line = lines[i]

        # conditions are managed
        if line[:indent_level * 4 + 3] == "    " * indent_level + "if ":
            # we create the tree of the condition
            condition = re.match(r".+\:", line[indent_level * 4 + 3:]).group()[:-1]
            condition = line_parser(lexer.line_lexer(condition))
            # we create the tree of the suite
            i += 1
            suite = parser_global(lines[i:], indent_level + 1)
            i += len(suite)
            global_tree.append(["if", condition] + suite)

        # we manage the while loop
        elif line[:indent_level * 4 + 5] == "    " * indent_level + "while ":
            # we create the tree of the condition
            condition = re.match(r".+\:", line[indent_level * 4 + 5:]).group()[:-1]
            condition = line_parser(lexer.line_lexer(condition))
            # we create the tree of the suite
            i += 1
            suite = parser_global(lines[i:], indent_level + 1)
            i += len(suite)
            global_tree.append(["while", condition] + suite)

        else:
            # we create the tree of the line
            global_tree.append(line_parser(lexer.line_lexer(line)))

        i += 1

    return global_tree

# Test
data = "b = -(10 - value * (--3*32) - sin(5*10-19, 2) + (-a) + fact(10, 10) * cos(10 + 1) * 'abcde' - 10 - sun.value)"

# we check if there are errors natively in the line
err.string_error(data)
# we do the syntactic analysis
tokens = lexer.line_lexer(data)
print(tokens)
# the syntax is checked
err.errors(tokens)
# we create the instruction tree
tree = line_parser(tokens)
print(tree)

# infinite mode
while True:
    data = input(">>> ")
    err.string_error(data)
    tokens = lexer.line_lexer(data)
    print(tokens)
    err.errors(tokens)
    tree = line_parser(tokens)
    print(tree)