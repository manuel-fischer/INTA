#!/usr/bin/env python3

import sys

#SCREEN_WIDTH = 80
SCREEN_WIDTH = 10**10
LS_LINE_DIGITS = 5

ERR_NUM = "argument should be numeric"
ERR_FILENAME = "argument should be a filename"
ERR_LINES = "expected single line number or range of line numbers"
ERR_LINE = "expected single line number"
ERR_FILE_UNBOUND = "editor not bound to any file"

def format_line(line, contents):
    ret = ""

    format_first = ("%%%ii %%%%s" % LS_LINE_DIGITS) % line
    format_add   = " "*(LS_LINE_DIGITS-1) + "+ %s"
    format_next  = " "*(LS_LINE_DIGITS-1) + "` %s"

    cont_len = SCREEN_WIDTH - LS_LINE_DIGITS - 2

    cur_format = format_first
    for ll in contents.split('\n'):
        cur_cur_format = cur_format
        while True:
            cur = ll[:cont_len]
            ll = ll[cont_len:]

            if ret: ret += '\n'
            ret += cur_cur_format % cur

            if not ll: break # inner

            cur_cur_format = format_next

        cur_format = format_add


    return ret


def multi_input(line):
    ret = ""

    format_first = ("%%%ii %%%%s" % LS_LINE_DIGITS) % line
    format_add   = " "*(LS_LINE_DIGITS-1) + "+ %s"

    cur_format = format_first

    first = True
    while True:
        content = input(cur_format%"")
        if content == ".": break
        if content and content == '.'*len(content): content = content[1:] # remove one dot
        if not first: ret += '\n'
        else: first = False
        ret += content
        cur_format = format_add
    return None if first else ret



def error(*a, **kw):
    print(*a, **kw, file = sys.stderr)

def info(*a, **kw):
    print(*a, **kw)

def as_number(s : str):
    try: return int(s)
    except ValueError: pass

    try: return float(s)
    except ValueError: pass

    return None

def parse_linerange(s):
    s = " %s " % s
    for kw in [" to ", " t "]:
        if kw in s:
            l = None
            u = None
            a, b = s.split(kw)
            if a: l = as_number(a)
            if b: u = as_number(b)
            return (l, u)
    n = as_number(s)
    return (n, n)

def parse_file_args(argv):
    if len(argv) == 1:
        filename = None
    else:
        filename = argv[1]
    return file(filename)


class file:
    __slots__ = """
        name
    """.split()

    def __init__(self, filename):
        self.name = filename

    @property
    def title(self): return self.name

    def read(self):
        if self.name == None: return ""
        with open(self.name, "rt") as f:
            contents = f.read()
            info("%i << %s"%(len(contents), f.name))
            return contents

    def write(self, contents):
        if self.name == None:
            error(ERR_FILE_UNBOUND)
            return
        with open(self.name, "wt") as f:
            f.write(contents)
            info("%i >> %s"%(len(contents), self.name))


class pseudo_file:
    __slots__ = """
        title
        contents
    """.split()

    def __init__(self, title, contents):
        self.title = title
        self.contents = contents

    def read(self):
        return self.contents

    def write(self, contents):
        self.contents = contents


inta_commands = {}
inta_commands_prefix = {}
def inta_command(name, prefix=False):
    prefix = False # ignore currently, not supported in inta.run
    def register(func):
        if prefix:
            inta_commands_prefix[name] = func
        else:
            inta_commands[name] = func
        return func
    return register


class util:
    def split_lines(data, step):
        splitted = data.split('\n')
        if splitted[-1] == "": splitted.pop()
        return {(i+1)*step : contents.rstrip() for i, contents in enumerate(splitted)}


class inta:
    __slots__ = """
        running
        lines
        step
        file
        allow_rebind
    """.split()

    def __init__(self, file, allow_rebind=True):
        #self.running
        self.lines = []
        self.step = 1
        self.file = file
        self.open(None)
        self.allow_rebind = allow_rebind

    def run(self):
        self.running = True
        while self.running:
            try:
                command = input(" ]")
                command = command.strip() # trailing spaces removed
                if not command: continue
                command_arr = command.split()
                prg = command_arr[0]
                #if prg[-1] == '.': # evaluate args
                #    try: args = eval(args)
                args = command[len(prg)+1:]
                line = as_number(prg)
                if line is not None:
                    self.set_line(line, args)
                else:
                    try:
                        prg_fun = inta_commands[prg]
                    except KeyError:
                        error("invalid command %s" % prg)
                        continue

                    try:
                        prg_fun(self, args)
                    except Exception as e:
                        error("Exception while executing command: " + str(e))
                        if input("rethrow[!]") == "!": raise

            except KeyboardInterrupt:
                pass

    def min_line(self):
        return min(self.lines.keys())

    def max_line(self):
        return max(self.lines.keys())

    def remove_line(self, line):
        del self.lines[line]

    def set_line(self, line, args):
        self.lines[line] = args

    def get_lines_sorted(self, lines=None):
        lst = sorted(list(self.lines.items()), key=lambda kv: kv[0])
        if lines is not None:
            l, u = lines
            if l is None: l = self.min_line()
            if u is None: u = self.max_line()
            def is_in_range(lc):
                line, contents = lc
                return l <= line <= u
            lst = list(filter(is_in_range, lst))
        return lst

    def remove_lines(self, lines):
        to_remove = self.get_lines_sorted(lines)
        for line, contents in to_remove:
            self.remove_line(line)


    def get_contents(self, lines=None):
        lines = self.get_lines_sorted(lines)
        return "".join(contents+"\n" for line, contents in lines)

    def block_after(self, line):
       lines = self.get_lines_sorted((line, None))
       line0 = lines[0]
       indent = lambda s: len(s) - len(s.lstrip())
       indent_line0 = indent(line0[1])
       if len(lines) == 1: return (line0[0]+step,None)
       first_line = lines[1]
       if indent(first_line[1]) <= indent_line0: return ((line0[0]+first_line[0])/2,)*2
       last_line = first_line
       for line in lines[2:]:
           if line[1] == "": continue
           if indent(line[1]) <= indent_line0: break
           last_line = line
       return (first_line[0], last_line[0])


    @inta_command("q")
    @inta_command("quit")
    @inta_command("exit")
    def exit(self, args):
        self.running = False


    @inta_command("wq")
    def save_quit(self, args):
        self.save(args)
        self.running = False

    @inta_command("o")
    @inta_command("open")
    def open(self, args):
        #if not args:
        #    perror(ERR_FILENAME)
        #    return

        if args: self.file = file(args)

        step = self.step
        all = self.file.read()
        self.lines = util.split_lines(all, step)


    @inta_command("w")
    @inta_command("save")
    def save(self, args):
        self.file.write(self.get_contents())

    @inta_command("re")
    @inta_command("rebind")
    def cmd_rebind(self, args):
        if not self.allow_rebind:
            error("rebinding not allowed")
            return
        self.file = file(args or None) # None instead of ""

    @inta_command("pwd")
    def cmd_print_title(self, args):
        print(self.file.title)

    @inta_command("n")
    @inta_command("numb")
    def numb(self, args):
        step = self.step
        if args:
            step = as_number(args)
            if not step:
                error(ERR_NUM)
                return

        self.lines = util.split_lines(self.get_contents(), step)


    @inta_command("l")
    @inta_command("ls")
    @inta_command("list")
    def list(self, args):
        lines = None
        if args:
            lines = parse_linerange(args)
        print("--", self.file.title, "--")
        for line, contents in self.get_lines_sorted(lines):
            print(format_line(line, contents))


    @inta_command("lz")
    @inta_command("k")
    def list_zero(self, args):
        lines = None
        if args:
            lines = parse_linerange(args)
        for line, contents in self.get_lines_sorted(lines):
            if contents and contents == contents.lstrip():
                print(format_line(line, contents))

    @inta_command("f")
    @inta_command("find")
    def cmd_find(self, args):
        lines = self.get_lines_sorted()
        for line, contents in lines:
            if args in contents:
                print(format_line(line, contents))

    @inta_command("rm")
    @inta_command("del")
    @inta_command("--", prefix=True)
    def cmd_remove_line(self, args):
        if not args: error(ERR_LINES)
        lines = parse_linerange(args)
        to_remove = self.get_lines_sorted(lines)
        for line, contents in to_remove:
            print(format_line(line, contents))
            self.remove_line(line)

    @inta_command("a")
    def append(self, args):
        next_line = self.max_line() + self.step
        app = self.set_line
        if args:
             next_line = as_number(args)
             app = self.append_line
        contents = multi_input(next_line)
        if contents is not None:
            app(next_line, contents)

    @inta_command(">>")
    def cmd_indent(self, args):
        # TODO `>> 3 on 1 to 10` or `>> 1 to 10 by 3`
        lines = parse_linerange(args)
        to_change = self.get_lines_sorted(lines)
        for line, contents in to_change:
            self.set_line(line, "    " + contents)

    @inta_command("<<")
    def cmd_deindent(self, args):
        lines = parse_linerange(args)
        to_change = self.get_lines_sorted(lines)
        for line, contents in to_change:
            for i in range(4):
                if not contents or not contents[0].isspace(): break
                contents = contents[1:]
            self.set_line(line, contents)

    @inta_command("v")
    def visit(self, args):
        pass # unindent following block and run inner instance of inta
        line_head = as_number(args)
        line_range = self.block_after(line_head)
        line_contents = self.get_contents(line_range)
        self.remove_lines(line_range)
        pfile = pseudo_file("%s:%i"%(self.file.title, line_range[0]), line_contents)
        inta(pfile, allow_rebind=False).run()
        contents = pfile.contents
        if contents == "": return
        if contents[-1:] == "\n": contents = contents[:-1]
        self.set_line(line_range[0], contents)


if __name__ == "__main__":
    from sys import argv
    inta(parse_file_args(argv)).run()
