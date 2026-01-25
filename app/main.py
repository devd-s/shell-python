import sys

builtins_cmds = ["type", "echo", "exit"]

def main():
    while True:
        sys.stdout.write("$ ")
        pass
        command = input()
        tokens= command.split()
        if command == "exit":
            break
        elif tokens[0] == "type":
            if tokens[1] not in builtins_cmds:
                print (f"{tokens[1]}: not found")
            else:
                print(f"{tokens[1]} is a shell builtin")
        elif tokens[0] == "echo":
            print(" ".join(tokens[1:]))
        else:
            print (f"{command}: command not found")
       


if __name__ == "__main__":
    main()
