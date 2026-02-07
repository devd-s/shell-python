import sys
import os
import shlex
import readline
import subprocess
from pathlib import Path

builtins_cmds = ["type", "echo", "exit", "history", "pwd"]

History = []

last_append_index = 0

def hist_exit():
    """Save histfile on exit"""
    path = os.environ.get("HISTFILE")
    if not path:
        return 
    
    with open(path, "w", encoding="utf-8") as f:
        for cmd in History:
            f.write(cmd + "\n")

def read_histfile(): 
    """ To load histroy from hist file"""
    global last_append_index
    path = os.environ.get("HISTFILE")
    if not path:
        return 
    
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            cmd = line.strip("\n")
            if not cmd.strip():
                continue
            History.append(cmd)
            readline.add_history(cmd)
    
    last_append_index = len(History)


def history_append_file(path: str):
    """Append histroy to a file"""
    global last_append_index
    try:
        with open(path, "a", encoding="utf-8") as f:
            for cmd in History[last_append_index:]:
                if cmd.strip():
                    f.write(cmd + "\n")
        last_append_index = len(History)
    except OSError:
        print (f"histroy : {path}: could not write to file")   

def history_write_file(path: str):
    """Write histroy to a file"""
    try:
        with open(path, "w", encoding="utf-8") as f:
            for cmd in History:
                f.write(cmd + "\n")
    except OSError:
        print (f"histroy : {path}: could not write to file")    

def history_read_file(path: str):
    """Read histroy via file"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                cmd = line.strip("\n")
                if not cmd.strip():
                    continue
                History.append(cmd)
                readline.add_history(cmd)
    except FileNotFoundError:
        print (f"history: {path} : no such file")
    except OSError:
        print (f"history: {path} : could not read file")

def add_to_history(command: str):
    """Add a command to history"""
    if command.strip():
        History.append(command)

def get_history(n: int | None = None):
    """Print the command histroy"""
    total =len(History)
    start_ind = 0 if n is None else max(0, total-n)

    for ind, cmd in enumerate(History[start_ind:], start=start_ind+1):
        print (f"{ind:5d}  {cmd}")


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
    readline.set_auto_history(False)
    read_histfile()
    while True:
        command = input("$ ")
        readline.add_history(command)
        add_to_history(command)
        tokens= shlex.split(command, posix=True)
        if command == "exit":
            hist_exit()
            break
        elif "|" in command:
            execute_pipe(command)
        elif tokens[0] == "pwd":
            print (os.getcwd())
        elif tokens[0] == "cd":
            try:
                os.chdir(tokens[1])
            except FileNotFoundError:
                print ("cd: {tokens[1]}: No such file or directory")
        elif ">" in command:
            os.system(command)
        elif tokens[0] == "history":
            if len(tokens) == 3 and tokens[1] == "-r":
                history_read_file(tokens[2])
                continue
            if len(tokens) == 3 and tokens[1] == "-w":
                history_write_file(tokens[2])
                continue
            if len(tokens) == 3 and tokens[1] == "-a":
                history_append_file(tokens[2])
                continue
            if len(tokens) == 2:
                n = int(tokens[1])
                get_history(n)
                continue
            get_history()
            continue
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
