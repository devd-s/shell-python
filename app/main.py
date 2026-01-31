import sys
import os
import shlex
import readline
from pathlib import Path

builtins_cmds = ["type", "echo", "exit"]

# first_tab_pressed = False
# last_completion_text = None

def display_match(substitution, matches, longest_match_length):
    print()
    print ("  ".join(matches))
    print (f"$ {readline.get_line_buffer()}", end='', flush=True)

# def display_matches(substitution, matches, longest_match_length):
#     global first_tab_pressed

#     if not first_tab_pressed:
#         sys.stdout.write('\x07')
#         sys.stdout.flush()
#         first_tab_pressed = True

    
#         # second tab
# #        print ()

#     matches = [m.strip() for m in matches if m and m.strip()]
#     sorted_matches = sorted(set(matches))

#     sys.stdout.write('\n')
#     if sorted_matches:
#         sys.stdout.write("  ".join(sorted_matches) + "\n")
#     else:
#         sys.stdout.write('\n')

#     sys.stdout.write("$ " + readline.get_line_buffer())
#     sys.stdout.flush()

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
    global first_tab_pressed, last_completion_text
    if state == 0:
        if text != last_completion_text:
            last_completion_text = text
            first_tab_pressed = False
    
    options_available_builtin = [ val + " " for val in builtins_cmds if val.startswith(text)]
    options_available_executable = [ val + " " for val in find_executables_in_path(text)]
    all_matches=  options_available_executable + options_available_builtin
    return all_matches[state] if state < len(all_matches) else None
    #return options_available[state] if state < len(options_available) else None

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
    global first_tab_pressed, last_completion_text
    readline.parse_and_bind("tab: complete")
    readline.set_completer(bash_complete)
    readline.set_completion_display_matches_hook(display_matches)
    while True:
        sys.stdout.write("$ ")
        pass
        command = input()
        # Reset completion state after command execution
        first_tab_pressed = False
        last_completion_text = None
        tokens= shlex.split(command, posix=True)
#        multi_args = shlex.split(command)
#        executable_cmnd = multi_args[0]
        if command == "exit":
            break
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
