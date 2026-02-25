import sys

if len(sys.argv) > 1:
    file_path = sys.argv[1]
else:
    print("Please include a file path as an argument")
    exit(1)


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


        #Printing
        print(f"Grammer Non-Terminal\n{non_terminal}")
        print(f"Grammer Terminals\n{terminal}")
        print("\nGrammer Rules")

        #Printing + find start symbol
        i = 1
        startSymbol = None
        for key in productions:
            for production in productions[key]:
                if '$' in production:
                    startSymbol = key
                print(f"({i}) {key} -> {production}")
                i+=1

        print(f"\nGrammer Start Symbol or Goal: {startSymbol}")
except FileNotFoundError:
    print(f"Error finding path {file_path}")
except Exception as e:
    print(f"Error: {e}")
