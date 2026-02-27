import sys

def derives_to_lambda(production, productions):
    if production == ["lambda"]:
        return True

    for symbol in production:
        if symbol not in productions:
            return False
        can_derive = False
        for prod in productions[symbol]:
            if derives_to_lambda(prod, productions):
                can_derive = True
                break
        if not can_derive:
            return False

    return True

def first_set(X, beta, productions, T=None):
    if T is None:
        T = set()

    if X not in productions:
        return {X}, T

    first_X = set()
    for production in productions[X]:
        first_prod, T = first_set(production[0], production[1:], productions, T)
        first_X.update(first_prod)
    if derives_to_lambda(production, productions):
        first_beta, T = first_set(beta[0], beta[1:], productions, T) if beta else ({"lambda"}, T)
        first_X.update(first_beta)

    first_X.discard("lambda")
    return first_X, T

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
    # print(f"Grammer Non-Terminal\n{non_terminal}")
    # print(f"Grammer Terminals\n{terminal}")
    # print("\nGrammer Rules")

    # #Printing + find start symbol
    # i = 1
    # startSymbol = None
    # for key in productions:
    #     for production in productions[key]:
    #         if '$' in production:
    #             startSymbol = key
    #         print(f"({i}) {key} -> {production}")
    #         i+=1

    # print(f"\nGrammer Start Symbol or Goal: {startSymbol}")

    # Derives to lambda Test
    # print("Derives to lambda test:")
    # for key in productions:
    #     for production in productions[key]:
    #         if derives_to_lambda(production, productions):
    #             print(f"{key} -> {production} derives to lambda")

    # First Set Test
    print("First Set Test:")
    for key in productions:
        first, _ = first_set(key, [], productions)
        print(f"First({key}) = {first}")
