import re

GOVER=20

# The original expression
expr = "aix || android || dragonfly || freebsd || netbsd || openbsd || solaris || gc"

# Dictionary of known variables and their boolean values
# Assume only 'linux' and 'amd64' are true; everything else is false by default
variables = {
    "linux": True,
    "amd64": True,
    "unix": True,
    # everything else defaults to False if not present
}

def evaluate(expr, vard):

    # 1) Convert C-style logical operators to Python's logical operators
    #    - "||" -> " or "
    #    - "&&" -> " and "
    #    - "!"  -> " not "
    # 1) Replace the C-style operators with Python's
    expr_replaced = re.sub(r"\|\|", " or ", expr)
    expr_replaced = re.sub(r"\&\&", " and ", expr_replaced)
    expr_replaced = re.sub(r"!",   " not ", expr_replaced)

    # 2) Replace variable references with get_var_value('...')
    #    but *exclude* the newly added Python keywords (or, and, not).
    pattern = r"\b(?!or\b|and\b|not\b)[a-zA-Z_]\w*\b"
    pattern = r"\b(?!or\b|and\b|not\b)[a-zA-Z_]\w*(?:\.[a-zA-Z_]\w*)*\b"
    pattern = r"\b(?!or\b|and\b|not\b)[a-zA-Z0-9_]\w*(?:\.(?:[a-zA-Z_]\w*|\d+))*\b"

 
    # Helper function: returns True or False from our variables dict
    def get_var_value(var_name):
        if var_name.startswith("go1."):
            intv = int(var_name.split("go1.")[1])
            if GOVER >= intv:
                return True
        return vard.get(var_name, False)

    def replace_var(match):
        var_name = match.group(0)
        return f"get_var_value('{var_name}')"

    py_expr = re.sub(pattern, replace_var, expr_replaced)

    # Now py_expr will be something like:
    # get_var_value('aix') or ( not get_var_value('android') and get_var_value('linux') ) ...
    # print("Transformed Python expression:", py_expr)

    # Evaluate the expression
    result = eval(py_expr)

    # print("Final result:", result)
    return result

def check_dependency(dvars, allvars, expr):
    depends = None, None
    for i, var1 in enumerate(dvars):
        for j, var2 in enumerate(dvars):
            if j <= i: continue

            allvars[var1] = True
            allvars[var2] = True
            tt = evaluate(expr, allvars)

            allvars[var1] = True
            allvars[var2] = False
            tf = evaluate(expr, allvars)

            allvars[var1] = False
            allvars[var2] = False
            ff = evaluate(expr, allvars)

            allvars[var1] = False
            allvars[var2] = True
            ft = evaluate(expr, allvars)

            depends_on_var1 = tt != ft or tf != ff
            depends_on_var2 = tt != tf or ft != ff

            assert not (depends_on_var1 and depends_on_var2)
            if depends_on_var1:
                depends = var1, tt
            elif depends_on_var2:
                depends = var2, tt
    return depends


def gen_junc_constraint(ln):

    if "ignore" in ln or "junction" in ln:
        return None

    expr = ln.split("//go:build ")[1].split("//")[0]

    # vs1 = variables.copy()
    # vs2 = variables.copy()
    # vs1["linux"] = False
    # vs2["linux"] = True
    # if evaluate(expr, vs1) == evaluate(expr, vs2):
    #     return None

    if "linux" in ln:
        return ln.replace("linux", "(linux || junction)")

    return None

    dep, tval = check_dependency(["gc", "gccgo", "race"], variables.copy(), expr)
    if dep:
        return f"//go:build ({expr}) || ({"" if tval else "!"}{dep} && junction)"

    if evaluate(expr, variables):
        return f"//go:build ({expr}) || junction"
    else:
        return f"//go:build ({expr}) && !junction"

import os

GOARCH_NAMES = [
    "386",
    "amd64",
    "arm",
    "arm64",
    "loong64",
    "mips",
    "mipsle",
    "mips64",
    "mips64le",
    "ppc64",
    "ppc64le",
    "riscv64",
    "s390x",
    "sparc64",
    "wasm",
]

GOOS_NAMES = [
    "darwin",
    "dragonfly",
    "illumos",
    "ios",
    "js",
    "wasip1",
    "linux",
    "android",
    "solaris",
    "freebsd",
    "nacl",
    "netbsd",
    "openbsd",
    "plan9",
    "windows",
    "aix",
]

def has_os_or_arch_name(string, ignore_linux_amd64 = False):
    for nm in GOARCH_NAMES + GOOS_NAMES:
        if ignore_linux_amd64 and nm in ["linux", "amd64"]:
            continue
        if nm in string:
            return True
    return False

def writelines(file_path, lines):

    # print(file_path)
    # with open("/home/friedj/goroot/src/../junction_patches.diff", "r") as f:
    #     d1 = f.read()

    # if file_path.strip(".") not in d1:
    #     return

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        f.write("\n")

def process_file(root, basename):
    """
    Opens the given file and processes it line by line.
    Here, we simply print the filename and the line.
    You can modify this function to perform any processing.
    """
    file_path = os.path.join(root, basename)
    outc = None

    if has_os_or_arch_name(basename, True):
        # print("skip 1", file_path)
        return

    if "vgetrandom" in basename or "rt0" in basename:
        return

    is_linux_ver = "linux" in basename and "nonlinux" not in basename

    constraint_line_nr = None
    plusbuild = False

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()

        if is_linux_ver:
            jlines = lines[:]

        for i, line in enumerate(lines):
            if constraint_line_nr is None and line.startswith("//go:build "):
                constraint_line_nr = i
                if is_linux_ver or not has_os_or_arch_name(line):
                    continue
                outc = gen_junc_constraint(line.strip())
                if outc:
                    lines[i] = outc
                continue

            if line.startswith("// +build "):
                lxs = line.split("// +build ")[1].split()
                adds = []
                new_j = []
                for lx in lxs:
                    if not "linux" in lx:
                        adds.append(lx)
                        new_j.append(lx)
                        continue

                    if "!linux" in lx:
                       assert not is_linux_ver
                       adds.append(lx + ",!junction")
                       continue

                    if is_linux_ver:
                        new_j.append(lx.replace("linux", "junction") + ",!linux")
                        adds.append(lx + ",!junction")
                    else:
                        adds.append(lx)
                        adds.append(lx.replace("linux", "junction"))
                if adds != lxs:
                    lines[i] = "// +build " + " ".join(adds)
                    if is_linux_ver:
                        jlines[i] = "// +build " + " ".join(new_j)
                    plusbuild = True

        if is_linux_ver:
            # assert not plusbuild
            jname = os.path.join(root, basename.replace("linux", "junction"))
            if constraint_line_nr is not None:
                nc = lines[constraint_line_nr].split("//go:build ")[1].split("//")[0]
                lines[constraint_line_nr] = f"//go:build ({nc}) && !junction"
                writelines(file_path, lines)

                nc = nc.replace("linux", "junction")
                jlines[constraint_line_nr] = f"//go:build ({nc}) && !linux"
                writelines(jname, jlines)
            else:
                if not plusbuild:
                  lines = ["// +build !junction"] + lines
                  jlines = ["// +build junction"] + jlines
                writelines(file_path, lines)
                writelines(jname, jlines)

            return


        if constraint_line_nr is not None or plusbuild:
            writelines(file_path, lines)

    except Exception as e:
        print(f"Error reading {file_path}: {e}")

def find_files(directory):
    """
    Recursively walks through the directory, finding .go and .s files.
    """
    for root, dirs, files in os.walk(directory):
        for file in files:
            if "junction" in file:
                continue
            # Check if the file has a .go or .s extension
            if file.endswith('.go') or file.endswith('.s'):
                process_file(root, file)

if __name__ == '__main__':
    # Specify the directory to search. Replace '.' with the desired directory.
    search_directory = '.'
    find_files(search_directory)
