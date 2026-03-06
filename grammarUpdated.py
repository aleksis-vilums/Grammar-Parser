import sys

def derives_to_lambda(term, productions, T=set()):
    if term == "lambda":
        return True
    if term not in productions:
        return False

    if term in T:
        return False
    T.add(term)
    for production in productions[term]:
        if (production == ["lambda"]):
            return True
        hasTerminal = False
        for symbol in production:
            if symbol not in productions or symbol == "$":
                hasTerminal = True
                break
        if hasTerminal:
            continue
        # All symbols are nonterminals
        allDerive = True
        for symbol in production:
            if not derives_to_lambda(symbol, productions, T):
                allDerive = False
        if allDerive:
            return True
    return False

def first_set(X, beta, productions, T=set()):
    if X not in productions:
        return {X}, T

    first_X = set()

    if X not in T:
        T.add(X)
        for production in productions[X]:
            first_prod, I = first_set(production[0], production[1:], productions, T)
            first_X = first_X.union(first_prod)
    if derives_to_lambda(X, productions, set()):
        first_beta, I = first_set(beta[0], beta[1:], productions, T) if beta else ({"lambda"}, T)
        first_X = first_X.union(first_beta)

    first_X.discard("lambda")
    return first_X, T

def follow_set(A, productions, T=set()):
    if A in T:
        return set(), T

    T.add(A)
    follow_A = set()

    for lhs, rhs in productions.items():
        for production in rhs:
            for i, symbol in enumerate(production):
                if symbol == A:
                    pi = production[i+1:] #All the symbols after A

                    if len(pi) > 0:
                        G, I = first_set(pi[0], pi[1:], productions, set())
                        follow_A = follow_A.union(G)
                    if len(pi) == 0 or (all(derives_to_lambda(sym, productions, set()) for sym in pi) and all(sym in productions for sym in pi)):
                        G, I = follow_set(lhs, productions, T)
                        follow_A = follow_A.union(G)

    follow_A.discard("lambda")
    return follow_A, T

def parse_grammar(file_path):
    try: 
        with open(file_path, 'r', encoding='utf-8') as file:
            #Split the content on white space
            content = file.read().split()

            #Array of non-terimnal
            non_terminal = []
            #Arrray of terminal
            terminal = []
            #Map/dict of productions
            # non-teminal (key) -> List of productions (value)
            productions = {} 
            currLHS = None
            currRHS = []

            #While the content is not empty
            i = 0
            while i < len(content):
                token = content[i]

                #Check for terminal or non-terminal
                if (any(c.isupper() for c in token)):
                    if token not in non_terminal:
                        non_terminal.append(token)
                elif token not in {"lambda", "$", "|", "->"}:
                    terminal.append(token)

                #Check for a new production
                if i + 1 < len(content) and content[i+1] == "->":
                    #If RHS production is built then save it
                    if currLHS is not None and currRHS:
                        productions[currLHS].append(currRHS)
                        currRHS = []

                    currLHS = token

                    #If LHS is not in productions then add new list of productions (empty)
                    if currLHS not in productions:
                        productions[currLHS] = []

                    #Skip "->" token
                    i+=2
                    continue

                #Or operator for multiple productions
                if token == "|":
                    #If currRHS exists then append to the productions according to the key and reset RHS
                    if currRHS:
                        productions[currLHS].append(currRHS)
                        currRHS = []
                    i+=1
                    continue

                #Add token to RHS production
                currRHS.append(token)
                i+=1

            #Final push of the last production if exists
            if currLHS is not None and currRHS:
                productions[currLHS].append(currRHS)
        
        return non_terminal, terminal, productions
    except FileNotFoundError:
        print(f"Error finding path {file_path}")
        return None, None, None
    except Exception as e:
        print(f"Error: {e}")
        return None, None, None

def predictSet(key, production, productions):
    predSet = set()
    derivesLambda = False

    for sym in production:
        first_sym, _ = first_set(sym, [], productions, set())
        predSet |= (first_sym - {'lambda'})
        if not derives_to_lambda(sym, productions, set()):
            derivesLambda = False
            break
        derivesLambda = True

    if derivesLambda:
        follow, _ = follow_set(key, productions, set())
        predSet |= follow

    return predSet

def isLLOne(productions):
    for key in productions:
        otherPredictSets = []
        for production in productions[key]:
            predSet = predictSet(key, production, productions)
            for otherPredictSet in otherPredictSets:
                if otherPredictSet & predSet: #Intersection therefore, violation
                    return False
            otherPredictSets.append(predSet)
    return True

def create_ll_table(productions, terminals):
    non_terminals = list(productions.keys())
    # + 1 because we need to include $
    ll_table = [["∅"] * (len(terminals) + 1) for _ in range(len(non_terminals))]
    
    production_number = 0 # Lists are 0 indexed so should really start from 0
    
    for i, non_terminal in enumerate(non_terminals):
        for production in productions[non_terminal]:
            predictionSet = predictSet(non_terminal, production, productions)
            for val in predictionSet:
                if val == "$": # I made $ index the very last (len terminals)
                    index = len(terminals)
                if val in terminals:
                    index = terminals.index(val)
                ll_table[i][index] = production_number
            production_number += 1
    
    return ll_table

# I just created this node class so I could more easily figure out the parent by storing it
class Node:
    def __init__(self, parent):
        self.parent = parent
        self.children = []

    def to_string(self):
        s = "["
        for c in self.children:
            if isinstance(c, Node):
                s += c.to_string() + ", "
            elif isinstance(c, str):
                s += c + ","
            else:
                s += ": ".join(c) + ", "
        s += "]"
        return s
    
    def to_lists(self):
        l = []
        for c in self.children:
            if isinstance(c, Node):
                l.append(c.to_lists())
            elif isinstance(c, str):
                l.append(c)
            else:
                l.append(": ".join(c))
        return l

def create_parse_tree(productions_map, terminals, start, parse_table, token_stream_filename):
    current_node = Node(None)
    k = [] # k is stack
    k.append(start)

    # map nonterminals to their order to figure out where in the parse table we should look
    # More efficient to do it beforehand
    # Also convert productions into a list instead of a map
    nonterms_to_order = {}
    productions_list = []
    for i, non_terminal in enumerate(productions_map.keys()):
        nonterms_to_order[non_terminal] = i
        for p in productions_map[non_terminal]:
            productions_list.append(p)

    # probably a better way to do this but I'm being lazy: read all the lines into a list
    lines = []
    with open(token_stream_filename, 'r') as file:
        for line in file:
            if len(line) != 0:
                lines.append(line.strip().split(" ")) # Split, because some lines might have srcValue
    # Reverse the lines because I'm treating them like a stack later (pop + look at last element)
    # and i need to read them in order
    lines.reverse() 
    # would probably be better to import python's deque

    while len(k) != 0:
        x = k.pop()
        # If x is a nonterminal, apply a production
        if x in productions_map.keys(): # Not efficient but whatever, I don't really care
            if len(lines) == 0:
                raise Exception(f"Can't parse: The token stream ran out of tokens before completing the derivation")
            if lines[-1][0] == "$":
                term_index = len(terminals)
            else:
                term_index = terminals.index(lines[-1][0]) # [0] because we are comparing to token not srcValue
            prod_number = parse_table[nonterms_to_order[x]][term_index] 
            if prod_number == "∅":
                raise Exception(f"Can't parse: Nonterminal {x} doesn't have a production for {lines[-1][0]}") # Could have line number
            k.append("MARKER") # should probably have more robust way to do this because MARKER could technically be a token
            production = productions_list[prod_number]
            for thingy in reversed(production): # append in reverse order
                k.append(thingy)
            n = Node(current_node) # create new node
            current_node.children.append(n) # append as rightmost child
            current_node = n # Then move down to this child
        elif x != "MARKER": # x is terminal or lambda
            if len(lines) == 0:
                raise Exception(f"Can't parse: The token stream ran out of tokens before completing the derivation")
            if x != "lambda": # x is terminal
                if x != lines[-1][0]:
                    raise Exception(f"Cant parse: Need to match the terminal on the stack, {x}, with {lines[-1][0]}")
                # psuedo code says x = lines.pop() but I think it's supposed to say "add the terminal as the rhs child"
                x = lines.pop()
            current_node.children.append(x)
        else: # x is MARKER
            current_node = current_node.parent

    return current_node.children[0] # current_node is root, only child is start

if __name__ == "__main__":
    if len(sys.argv) > 2:
        file_path = sys.argv[1]
        token_filename = sys.argv[2]
    else:
        print("Please include two file paths as an argument (grammar definition and token stream)")
        exit(1)
    
    non_terminal, terminal, productions = parse_grammar(file_path)
    # Find start symbol (need to start from the start symbol when parsing)
    start_symbol = None
    for key, nonterm_prods in productions.items():
        if '$' in nonterm_prods[0]: # all productions for start should have $
            start_symbol = key
            break
    if start_symbol is None:
        raise Exception("Could not find start symbol")

    #If parsing failed, exit
    if non_terminal is None:
        exit(1)

    # Grammar Printing
    #print(f"Grammer Non-Terminal\n{non_terminal}")
    #print(f"Grammer Terminals\n{terminal}")
    #print("\nGrammer Rules")

    # #Printing + find start symbol
    # i = 0 # lists are 0 indexed in python so should start from 0
    # startSymbol = None
    # for key in productions:
    #    for production in productions[key]:
    #        if '$' in production:
    #            startSymbol = key
    #        print(f"({i}) {key} -> {production}")
    #        i+=1

    #print(f"\nGrammer Start Symbol or Goal: {startSymbol}")

    #Predict Set
    # print("Predict Set Test:")
    # for key in productions:
    #     for production in productions[key]:
    #         predictionSet = predictSet(key, production, productions)
    #         print(f"Predict Set({key}): {predictionSet}")

    if not isLLOne(productions):
        raise Exception("The grammar isn't LL(1)")

    # First Set Test
    #print("First Set Test:")
    #for key in productions:
    #    first, _ = first_set(key, [], productions, set())
    #    print(f"First({key}) = {first}")

    
    #Follow Set Test
    #print("Follow Set Test")
    #for key in productions:
    #    follow, _ = follow_set(key, productions, set())
    #    print(f"Follow({key}) = {follow}")

    # Create LL Table
    ll_table = create_ll_table(productions, terminal)

    # print(f"  {'|'.join(terminal)}|$")
    # for i, key in enumerate(productions):
    #     print(f"{key}|{'|'.join(map(str, ll_table[i]))}")

    print("Parse tree:")
    parse_tree = create_parse_tree(productions, terminal, start_symbol, ll_table, token_filename)
    print(parse_tree.to_string())

