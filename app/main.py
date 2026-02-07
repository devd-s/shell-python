import sys
import os
import shlex
import readline
import subprocess
from pathlib import Path

builtins_cmds = ["type", "echo", "exit"]

def execute_builtins(cmd_tokens, stdin_data=None):
    if cmd_tokens[0] == "echo":
        joiner = " ".join(cmd_tokens[1:])
        output = joiner.replace("\\n", "\n")
        return output + "\n"
    elif cmd_tokens[0] == "type":
        if len(cmd_tokens) < 2:
            return ""
        target_cmd = cmd_tokens[1]
        if target_cmd in builtins_cmds:
            return (f"{cmd_tokens[1]} is a shell builtin\n")
        elif path_exists(cmd_tokens[1]) is not None:
            return (f"{cmd_tokens[1]} is {path_exists(cmd_tokens[1])}\n")
        else:
            return (f"{cmd_tokens[1]}: not found\n")
    return ""

def execute_pipe(command: str) -> bool:
    parts = [p.strip() for p in command.split("|")]

    if len(parts) <= 1:
        return False

    stages = [shlex.split(p,posix=True) for p in parts if p.strip()]

    if not stages:
        return True

    procs: list[subprocess.Poopen] = []
    prev_in = None

    for i, cmds in enumerate(stages):
        is_last = (i == len(stages) - 1 )

        if cmds[0] in builtins_cmds:
            stdin_data = prev_in.read() if prev_in is not None else None
            if prev_in is not None:
                prev_in.close()
                prev_in = None

            output = execute_builtins(cmds,stdin_data)

            if is_last:
                sys.stdout.write(output)
                sys.stdout.flush()

                for p in procs:
                    p.wait()
                return True
            
            r_fd,w_fd = os.pipe()
            os.write(w_fd, output.encode())
            os.close(w_fd)
            prev_in = os.fdopen(r_fd,"r")
            continue
        ex = subprocess.Popen(cmds, stdin=prev_in, stdout=None if is_last else subprocess.PIPE, text=True)

        if prev_in is not None:
            prev_in.close()

        procs.append(ex)
        prev_in = ex.stdout

    for p in procs:
        p.wait()
    
    if prev_in is not None:
        prev_in.close()

    return True

def display_match(substitution, matches, longest_match_length):
    print()
    print (" ".join(matches))
    print (f"$ {readline.get_line_buffer()}", end="", flush=True)

def find_executables_in_path(prefix: str) -> list[str]:
    matches = [
        file.name
        for directory in os.environ.get("PATH").split(os.pathsep)
        if directory
        for file in Path(directory).glob(f"{prefix}*")
        if file.is_file() and os.access(file,os.X_OK)
    ]
    return sorted(set(matches))

def bash_complete(text: str, state: int) -> str:
    options_available_builtin = [ val + " " for val in builtins_cmds if val.startswith(text)]
    options_available_executable = [ val + " " for val in find_executables_in_path(text)]
    all_matches=  options_available_executable + options_available_builtin
    return all_matches[state] if state < len(all_matches) else None

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
    # global first_tab_pressed, last_completion_text
    readline.parse_and_bind("tab: complete")
    readline.set_completer(bash_complete)
    readline.set_completion_display_matches_hook(display_match)
    while True:
        sys.stdout.write("$ ")
        pass
        command = input()
        tokens= shlex.split(command, posix=True)
#        multi_args = shlex.split(command)
#        executable_cmnd = multi_args[0]
        if command == "exit":
            break
        elif "|" in command:
            execute_pipe(command)
        elif ">" in command:
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
