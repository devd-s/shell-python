import sys
import os
import shlex

builtins_cmds = ["type", "echo", "exit"]

def path_exists(cmd):
    env_path = os.environ.get("PATH", "")
    pathsep = env_path.split(os.pathsep)

    for directory in pathsep:
        if directory == "":
            directory = "."
    
        full_path = os.path.join(directory, cmd)

        if os.path.exists(full_path):
            if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                return full_path
    return None

def main():
    while True:
        sys.stdout.write("$ ")
        pass
        command = input()
#        tokens= command.split()
        tokens= shlex.split(command, posix=True)
#        multi_args = shlex.split(command)
#        executable_cmnd = multi_args[0]
        if command == "exit":
            break
        elif ">" in command or "<" in command:
            os.system(command)
        elif tokens[0] == "type":
            if tokens[1] in builtins_cmds:
                print(f"{tokens[1]} is a shell builtin")
            elif path_exists(tokens[1]) is not None:
                print(f"{tokens[1]} is {path_exists(tokens[1])}")
            else:
                print (f"{tokens[1]}: not found")
        elif tokens[0] == "echo":
            print(" ".join(tokens[1:]))
        elif path_exists(shlex.split(command)[0]):
            os.system(command)
        else:
            print (f"{command}: command not found")

if __name__ == "__main__":
    main()
