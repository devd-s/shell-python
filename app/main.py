import sys


def main():
    while True:
        sys.stdout.write("$ ")
        pass
        command = input()
        tokens= command.split()
        if command == "exit":
            break
        elif tokens[0] == "echo":
            print(" ".join(tokens[1:]))
        else:
            print (f"{command}: command not found")
       


if __name__ == "__main__":
    main()
