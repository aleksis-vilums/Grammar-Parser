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
    ll_table = [["∅"] * len(terminals) for _ in range(len(non_terminals))]
    
    production_number = 1
    
    for i, non_terminal in enumerate(non_terminals):
        for j, production in enumerate(productions[non_terminal]):
            predictionSet = predictSet(non_terminal, production, productions)
            for val in predictionSet:
                if val == "$":
                    continue
                if val in terminals:
                    index = terminals.index(val)
                    ll_table[i][index] = production_number
            production_number += 1
    
    return ll_table

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        print("Please include a file path as an argument")
        exit(1)
    
    non_terminal, terminal, productions = parse_grammar(file_path)

    #If parsing failed, exit
    if non_terminal is None:
        exit(1)

    # Grammar Printing
    #print(f"Grammer Non-Terminal\n{non_terminal}")
    #print(f"Grammer Terminals\n{terminal}")
    #print("\nGrammer Rules")

    # #Printing + find start symbol
    #i = 1
    #startSymbol = None
    #for key in productions:
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

    # print(f"{isLLOne(productions)}")

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
    print(productions)
    ll_table = create_ll_table(productions, terminal)
    print(f"  {'|'.join(terminal)}")
    for i, key in enumerate(productions):
        print(f"{key}|{'|'.join(map(str, ll_table[i]))}")

