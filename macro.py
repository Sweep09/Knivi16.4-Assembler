macro_list = {}
MAX_DEPTH = 10
PRINT_LEN = False

labels = {}

def parse_macros(program: list[list[str]]):
    temp_program = []
    macro_instructions = []
    in_macro = False
    last_macro = None
    macro_params = 0

    for i,line in enumerate(program):
        if len(line) == 0 or line == '':
            continue
        if line[0] == '%macro':
            if in_macro:
                raise ValueError(f'Macro inside of macro. {line}')
            if macro_list.get(line[1]):
                raise ValueError(f'Macro name already defined. {line}')
            try:
                macro_params = line[2]
            except IndexError as e:
                raise ValueError(f'%macro expects parameter count. {line}') from e
            if not line[1][0].isalpha():
                raise ValueError(f'%macro expects name to start with a letter. {line}')
            if line[1].find('\\') != -1:
                raise ValueError(f'Invalid character in macro. {line}')
            in_macro = True
            last_macro = line
            #print(f'Macro found: ({line[1]}) Line {i}')
            continue

        if i == len(program)-1:
            if in_macro and line[0] != r'%end':
                raise ValueError(f'Macro never closed. {last_macro[1]}')

        if line[0] == r'%end':
            in_macro = False
            for idx,k in enumerate(macro_instructions):
                for idx2,j in enumerate(k):
                    if j in labels:
                        macro_instructions[idx][idx2] = labels[j]

            macro_list[last_macro[1]] = {
                'body':macro_instructions, 
                'params':macro_params,
                }
            #print(f'Macro closed: ({last_macro[1]}) Line {i}')
            macro_instructions = []
            continue

        if in_macro:
            if line[0][-1] == ':':
                if line[0].startswith('macro.') or line[0][0] == "%":
                    raise ValueError(f'Reserved label in macro label. {line}')
                # rename label
                labels[line[0][0:-1]] = f'macro.{last_macro[1]}.{line[0][0:-1]}'
                line[0] = labels[line[0][0:-1]] + ":"
            macro_instructions.append(line)
            continue

        temp_program.append(line)
    #print(f' macro_list: {macro_list}')
    return replace_macros(temp_program)

def reduce_strings(strings: list[str]) -> list[list[str]]:
    temp = []
    lengths = []
    last = ""
    single = False
    count = 0
    for string in strings:
        if last:
            if single:
                temp[-1] += string
                last = string
                single = False
                lengths[-1] += 1
                continue
            if string in "+-":
                temp[-1] += string
                last = string
                single = True
                lengths[-1] += 1
                continue
            if string in "++--":
                temp[-1] += string
                last = string
                lengths[-1] += 1
                continue
            lengths.append(1)
        last = string
        temp.append(last)

    return [temp,lengths]

def get_group(line, lengths, n):
    start = sum(lengths[:n-1])+1
    end   = start + lengths[n-1]
    return line[start:end]

def replace_macros(program: list[list[str]], depth=0):
    if depth > MAX_DEPTH:
        raise RecursionError('Max recursion exceeded.')
    new_prog = []
    for line in program:
        if not macro_list.get(line[0].split(".")[0]):
            new_prog.append(line)
            continue
        # append flags
        temp = line[0].split(".", maxsplit=1)
        line[0] = temp[0]
        if len(temp) > 1:
            new_temp = macro_list.get(line[0])['body'].copy()
            for i,m in enumerate(new_temp):
                m = m.copy()
                m[0] += "." + temp[1]
                new_temp[i] = m
        else:
            new_temp = macro_list.get(line[0])['body']

        parameters = int(macro_list.get(line[0])['params'])
        linecheck = reduce_strings(line)
        if len(linecheck[0])-1 != parameters:
            raise ValueError(f'Macro expected {parameters} parameters but '
                                f'got {len(linecheck[0])-1}. {linecheck[0]}')

        extended_part = []
        for i in new_temp:
            i = i.copy() # prevent modifying stored macro
            for t,v in enumerate(i):
                # replace param reference with value
                if v.find("%") != -1:
                    v_index = v.find("%")
                    if not v[v_index+1:].isdigit():
                        raise ValueError(f'Invalid parameter in macro. {i}, '
                                            f'{new_temp}, {labels}')
                    param = int(v[v_index+1:],0)

                    if 1 <= param <= parameters:
                        group = get_group(line,linecheck[1],param)
                        if v_index > 1:
                            group = [v[:v_index] + group[0]] + group[1:]
                            i[t:t+1] = group
                        else:
                            i[t:t+1] = group
            extended_part.append(i)
        new_prog.extend(replace_macros(extended_part, depth+1))
    return new_prog

def check_inclusions(program: list[list[str]], included_files=None,
                      depth=0, instruction_seen=False):
    if depth > MAX_DEPTH:
        raise RecursionError('Max recursion exceeded.')
    if included_files is None:
        included_files = set()

    new_prog = []
    inclusion_type = '<include>'
    for line in program:
        if len(line) > 1 and line[0] == inclusion_type:
            if not instruction_seen:
                print('\033[91m### WARNING: Code in included file will run first.\033[0m')
            fname = line[1].strip('"\'')
            if fname in included_files:
                continue

            included_files.add(fname)
            with open(fname,'r', encoding='utf-8') as f:
                f_lines = f.readlines()
                f_lines = rebuild_program(f_lines)
                if PRINT_LEN:
                    print(f"{fname}: {len(f_lines)} lines")
                else:
                    print(f'included "{fname}"')
                sub_prog = check_inclusions(f_lines,included_files,
                                            depth+1,instruction_seen)
                new_prog.extend(sub_prog)
        else:
            if len(line) > 0:
                if not instruction_seen:
                    instruction_seen = True
                new_prog.append(line)
    return new_prog

def smart_split(line: str):
    temp = ""
    optemp = ""
    tokens = []
    op2 = False
    opdone = False
    for i,char in enumerate(line):
        if char in "+-":
            if not op2:
                optemp += char
                op2 = True
            elif op2:
                optemp += char
                tokens.append(optemp)
                optemp = ""
                op2 = False
            if temp:
                tokens.append(temp)
                temp = ""
            continue

        if char == ":" and char != line[-1]:
            tokens.append(temp)
            temp = ""
            continue

        if op2:
            tokens.append(optemp)
            optemp = ""
            op2 = False
        if char in '[(':
            continue
        if char in '])':
            if i == len(line)-1:
                break
            continue

        temp += char
    if temp:
        tokens.append(temp)
    if not tokens:
        raise ValueError("Empty expression")
    return tokens

def rebuild_program(program: list[str]) -> list[list[str]]:
    line: str = None
    newprog = []
    label_group = None
    replacers = {}
    multiline = False
    temp2 = []

    for line in program:
        in_string = False
        temp = line.lstrip().split("#")[0].split(";")[0].split("//")[0].split(",")
        if not temp[0]:
            continue
        if temp[0].find("\"") != -1:
            temp = temp[0].split(" ")
        for j,t in enumerate(temp):
            t = t.strip()
            if in_string:
                temp2[-1] += " "
                temp2[-1] += t
                if t[-1] == "\"":
                    in_string = False
                continue

            if multiline:
                if t.find("*/") != -1:
                    multiline = False
                continue
            if t[0] == "\"" and len(t) > 3:
                in_string = True
                temp2.append(t)
                continue
            if j == 0:
                if len(t) > 1 and t[:2] == "/*":
                    multiline = True
                    continue
                temp2 = t.split(" ")
            elif t[0] in ('[','('):
                tem = smart_split(t)
                for tp in tem:
                    temp2.append(tp)
            elif t[-1] in (']',')'):
                temp2.append(t[:-1])
            else:
                temp2.append(t)

            if t[-1] == ":" and label_group is not None:
                replacers[temp2[0][:-1]] = f"{label_group}.{temp2[0][:-1]}"
                temp2 = [replacers[temp2[0][:-1]] + ":"]
                newprog.append(temp2)
                temp2 = [""]
                continue

            if t[-1] == "{":
                temp2 = t.split(" ")
                label_group = temp2[0]
                temp2 = [""]
                continue

            if t[-1] == "}":
                label_group = None
                temp2 = [""]
                continue

        temp = temp2
        if not temp[0]:
            continue
        newprog.append(temp)
    return second_pass(newprog, replacers)

def second_pass(file: list[list[str]], label_replace: list[str]):
    for line in file:
        for i,part in enumerate(line):
            if part in label_replace:
                line[i] = label_replace[part]
    return file

def pre_process(program):
    macro_program = check_inclusions(program)
    macroless_program = parse_macros(macro_program)
    return macroless_program
