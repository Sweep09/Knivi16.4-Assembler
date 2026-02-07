import os
from tkinter import Tk, filedialog
import pyperclip as py
import constants as cts
from hugemem_encoder import list_to_huge_string
import macro as mc

root = Tk()
root.withdraw()

labels = {}
reserved_keywords = {"define", "setstatic", "CID"}
DATA_START = [0,0,0] # start, curr, end
data_words = ["db","dw","dd"]

def parse_types(opcode: str, inst: list) -> int:
    for i in inst[0:]:
        if i == "sp":
            i = "r15"

    if opcode[0] != 'j':
        opcode = cts.CODE_ASSO[opcode]
    else:
        opcode = cts.CODE_ASSO[opcode[0]]
    # account for modifiers
    temp = cts.OPCODES[inst[0]][0]<<23          # opcode
    if len(cts.OPCODES[inst[0]]) > 1:
        temp += cts.OPCODES[inst[0]][1]
    inst[0] = temp
    try:
        if opcode == cts.CODE_TYPES[0]: # DATA
            if inst[1] in cts.REGS:
                inst[1] = int(inst[1][1:],0)<<18    # tgt
            if inst[2] in cts.REGS:
                inst[2] = int(inst[2][1:],0)<<13    # opd1
            if len(inst) > 3:
                if inst[3] in cts.REGS:
                    inst[3] = int(inst[3][1:],0)        # opd2
                else:
                    if isinstance(inst[3],str) and not inst[3].isnumeric() and "0x" not in inst[3]:
                        if len(inst[3]) == 3 and inst[3][0] in ('\'', '"'):
                            inst[3] = ord(inst[3][1])
                    else:
                        inst[3] = int(inst[3],0)&0x1fff     # imm
                    inst.append(1<<17)                  # imm bit

        elif opcode == cts.CODE_TYPES[1]: # MEM
            if inst[0] == 192937984:
                print(inst)
            if inst[1] in cts.REGS:
                inst[1] = int(inst[1][1:],0)<<18        # tgt/opd3
            if len(inst) > 3:
                try:
                    inst[3] = get_op2_code(inst[3])<<11     # as
                except TypeError:
                    if isinstance(inst[3],str):
                        inst[3] = get_id_code(inst[3])<<12     # id
                        inst[3] |= 0x200
            if len(inst) >= 5:
                if inst[2] in cts.REGS:
                    inst[2] = int(inst[2][1:],0)<<13    # opd1
                if len(inst) == 6:
                    inst[5] = get_id_code(inst[5])<<12  # id
                    inst[5] |= 0x200
                if inst[4] in cts.REGS:
                    inst[4] = int(inst[4][1:],0)        # opd2
                else:
                    inst[4] = int(inst[4],0)&0xff       # imm
                    inst.append(1<<17)                  # imm bit
            elif len(inst) == 4:
                if inst[2] in cts.REGS:
                    inst[2] = int(inst[2][1:],0)<<13    # opd1
                    inst.append(1<<17)                  # set opd2 to 0
            else:
                if inst[2] in cts.REGS:
                    inst[2] = int(inst[2][1:],0)<<13    # opd1
                else:
                    inst[2] = int(inst[2],0)&0xff       # imm
                inst.append(1<<17)                      # always append for this len
            if inst[0] == 192937984:
                print(sum(inst))

        elif opcode == cts.CODE_TYPES[2]:
            pass

        elif opcode == cts.CODE_TYPES[3]: # J/THREAD
            if len(inst) > 1:
                if inst[1] in cts.REGS:
                    inst[1] = int(inst[1][1:],0)        # opd2
                else:
                    inst.append(1<<17)                  # imm bit
                    inst[1] = int(inst[1],0)&0xffff     # imm

        elif opcode == cts.CODE_TYPES[4]: # M
            if inst[1] in cts.REGS:
                inst[1] = int(inst[1][1:],0)<<18    # tgt
            if len(inst) > 2:
                if inst[2] in cts.REGS:
                    inst[2] = int(inst[2][1:],0)        # opd2
                elif inst[2] == "CID":
                    inst[2] = 3<<16                     # imm bit as well
                else:
                    inst.append(1<<17)                  # imm bit
                    if isinstance(inst[2],str) and "0x" not in inst[2]:
                        try:
                            inst[2] = int(inst[2],0)&0xffff     # imm
                        except ValueError:
                            if len(inst[2]) == 3 and inst[2][0] in ('\'', '"'):
                                inst[2] = ord(inst[2][1])
                    else:
                        inst[2] = int(inst[2],0)&0xffff     # imm

        elif opcode == cts.CODE_TYPES[5]: # SET
            if inst[1] in cts.REGS:
                inst[1] = int(inst[1][1:],0)<<13    # opd1
            if inst[2] in cts.REGS:
                inst[2] = int(inst[2][1:],0)        # opd2
            else:
                inst.append(1<<17)                  # imm bit
                if isinstance(inst[2],str) and not inst[2].isnumeric() and "0x" not in inst[2]:
                    if len(inst[2]) > 1 and inst[2][0] in ('\'', '"'):
                        inst[2] = ord(inst[2][1])
                    else:
                        inst[2] = ord(inst[2][0])
                else:
                    if int(inst[2],0) > 0x1fff:
                        raise ValueError(f"value too high {opcode}, {inst}")
                    inst[2] = int(inst[2],0)&0x1fff     # imm

        elif opcode == cts.CODE_TYPES[6]:   # NULL
            if len(inst) > 1:
                if inst[1] in cts.REGS:
                    inst[1] = int(inst[1][1:],0)<<18    # tgt

        elif opcode == cts.CODE_TYPES[7]:   # Core stuff
            if len(inst) > 1:
                inst[1] = int(inst[1],0)<<18        # tgt
            if len(inst) > 2:
                if inst[2] in cts.REGS:
                    inst[2] = int(inst[2][1:],0)<<13    # opd2
                else:
                    inst[2] = int(inst[2],0)&0xffff     # imm
                    inst.append(1<<17)

    except IndexError as e:
        raise IndexError(f"{opcode}, {inst}") from e

    try:
        summ = sum(inst)
    except TypeError as e:
        raise TypeError((opcode,inst)) from e
    return summ

def parse_flags(opflgs):
    if opflgs[0][0] != 'j':
        opflgs[0] = cts.CODE_ASSO[opflgs[0]]
    else:
        opflgs[0] = cts.CODE_ASSO[opflgs[0][0]]
    flags: dict = cts.FLAG_CATS[opflgs[0]]
    match len(opflgs):
        case 1:
            opflgs = []
        case 2:
            for _,v in enumerate(flags.keys()):
                if opflgs[1] == v:
                    opflgs[1] = flags[v]
                    break
        case 3:
            for _,v in enumerate(flags.keys()):
                if opflgs[1] == v:
                    opflgs[1] = flags[v]
                elif opflgs[2] == v:
                    opflgs[2] = flags[v]
        case 4:
            for _,v in enumerate(flags.keys()):
                if opflgs[1] == v:
                    opflgs[1] = flags[v]
                elif opflgs[2] == v:
                    opflgs[2] = flags[v]
                elif opflgs[3] == v:
                    opflgs[3] = flags[v]
        case _:
            raise ValueError(f"too many flags. {opflgs}")
    if len(opflgs) > 1:
        for i,v in enumerate(opflgs[1:]):
            if v in cts.CONDITIONS:
                opflgs[i+1] = cts.CONDITIONS[v]<<28
                break
            if isinstance(v,str):
                optemp = opflgs[:i+1]
                if len(opflgs) > 2:
                    for f in opflgs[i+2:]:
                        optemp.append(f)
                opflgs = optemp

    opflgs = opflgs[1:]
    return sum(opflgs)

def get_op2_code(op2):
    match op2:
        case '+':
            op2 = 0
        case '-':
            op2 = 1
    return op2

def get_id_code(id):
    match id:
        case '++':
            id = 0
        case '--':
            id = 1
        case _:
            raise ValueError(f"unknown id code. {id}")
    return id

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

        if char == ":" and i != len(line)-1:
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
            # if i == len(line)-1:
            #     break
            continue

        temp += char
    if temp:
        tokens.append(temp)
    if not tokens:
        raise ValueError("Empty expression")
    return tokens

def second_pass(line: list[str], linenum):
    if not line[0]:
        return ['']
    if len(line) == 1 and line[0][-1] == ':':
        if line[0][:-1] not in labels:
            check_reserved(line[0][:-1],line)
            labels[line[0][:-1]] = linenum
        else:
            raise ValueError(f"label already defined. {line[0][:-1]}, {labels}")
        return ['']

    if line[0] in data_words:
        check_reserved(line[1], line)
        labels[line[1]] = line[1]
    return line

def clean_labels(file: list[list[str]]):
    newfile = []
    linenum = 0
    for line in file:
        line = second_pass(line, linenum)
        if not line[0]:
            continue
        if not check_reserved(line[0],line,True) and line[0] not in data_words:
        # dont increment labels
            linenum += 1
        newfile.append(line)
    return newfile

def check_reserved(word, line, allow=False):
    if word in reserved_keywords:
        if not allow:
            raise ValueError(f"Attempt to overwrite reserved keyword. {word} in {line}")
        return word
    return None

def get_special(special_key, line: list[str]):
    match special_key:
        case "define":
            if line[2][0].isnumeric():
                labels[line[1]] = int(line[2],0)
            elif line[2][0] == "\"":
                labels[line[1]] = ord(line[2][1:-1])
            else:
                labels[line[1]] = line[2]

        case "setstatic":
            if line[1][0].isnumeric():
                DATA_START[0] = int(line[1],0)
                DATA_START[1] = int(line[1],0)
            else:
                raise ValueError(f"invalid static address. {line}")
        case _:
            raise ValueError(f"undefined reserved key. {special_key}")

def get_data(line) -> list[int]:
    dword = 0
    dwords = []
    i = 0
    escape = False
    match line[0]:
        case "db":
            for j, idx in enumerate(line[2:]):
                for char in idx:
                    if escape and char == "n":
                        char = "\n"
                        escape = False
                    elif escape:
                        escape = False
                    if char in ("'\""):
                        continue
                    if char == "\\":
                        escape = True
                        continue
                    dword += ord(char)<<(i*8)
                    if i == 3:
                        dwords.append(dword)
                        dword = 0
                    i = (i+1)%4
                if dword != 0:
                    dwords.append(dword)
            dwords.append(0)
        case "dw":
            for i,num in enumerate(line[2:]):
                if num[0] in "'\"":
                    for k,j in enumerate(num[1:-1]):
                        dword = ord(j)
                        if k&1:
                            dwords[-1] += dword<<16
                            continue
                        dwords.append(dword)
                    dwords.append(0)
                else:
                    dword = int(num,0)
                    if i&1:
                        dwords[-1] += dword<<16
                        continue
                    dwords.append(dword)
        case "dd":
            for num in line[2:]:
                dwords.append(int(num,0))
        case _:
            raise ValueError(line)
    return dwords

def rebuild_program(program: list[str]) -> list[list]:
    line: str = None
    newprog = []
    skip = False
    slash_comment = 0
    multiline = False
    for line in program:
        in_string = False
        temp = []
        temp2 = []
        if not isinstance(line,list):
            skip = False
            line = line.strip()
            t2 = ""
            for i,char in enumerate(line):
                if multiline and char == "*" and line[i+1] == "/":
                    multiline = False
                    continue
                if multiline:
                    continue
                if in_string:
                    if char in "'\"":
                        in_string = False
                        t2+=char
                        temp.append(t2)
                        t2 = ""
                        continue
                    t2 += char
                    continue
                if char in "'\"" and not in_string:
                    t2+=char
                    in_string = True
                    continue

                if slash_comment == 1 and char == "*":
                    multiline = True
                    slash_comment = 0
                    t2 = ""
                    continue

                if char in "#;":
                    break
                if char == "/":
                    slash_comment += 1
                    if slash_comment == 2:
                        slash_comment = 0
                        break
                    continue
                slash_comment = 0

                if char in ", ":
                    if t2:
                        temp.append(t2)
                    t2 = ""
                    continue
                t2 += char
            if t2:
                temp.append(t2)
        else:
            skip = True
        ending_tag = False
        for j,t in enumerate(temp) if not skip else enumerate(line):
            t = t.strip()
            if j == 0:
                if t[0] != "\"":
                    temp2 = t.split(" ")
            elif t[0] in '[(':
                tem = smart_split(t)
                ending_tag = True
                for tp in tem:
                    temp2.append(tp)
            elif ending_tag and t[-1] in ')]':
                ending_tag = False
                temp2.append(t[:-1])
            else:
                temp2.append(t)
        temp = temp2
        if not temp or not temp[0]:
            continue
        newprog.append(temp)
    return newprog

def set_datastart(val):
    DATA_START[0] = val
    DATA_START[1] = val

if __name__ == "__main__":
    PRINT_LEN = True
    FILE_PATH = filedialog.askopenfilename(defaultextension=".cm2a")
    with open(FILE_PATH,"r", encoding="utf-8") as f:
        file = f.readlines()
    os.chdir(os.path.dirname(FILE_PATH))

    file = rebuild_program(file)
    if PRINT_LEN:
        mc.PRINT_LEN = True
        print(f"main: {len(file)} lines")
    file = mc.pre_process(file)
    file = rebuild_program(file) # ;;;;;;
    file = clean_labels(file)

    listarr = [0]*(1<<16)
    count = 0
    set_datastart(len(file)+500) # dynamic with room for program creation?
    for line in file:
        for j,l in enumerate(line[1:]):
            line[j+1] = str(labels.get(l,l))

        opcode = line[0].split(".")[0]
        if opcode in reserved_keywords:
            get_special(opcode,line)
            continue
        if opcode in data_words and DATA_START[0] != 0:
            codes = get_data(line)
            labels[line[1]] = DATA_START[1]
            if DATA_START[2] == 0:
                DATA_START[2] = None
            for v in codes:
                listarr[DATA_START[1]] = v
                DATA_START[1] += 1
                if DATA_START[2] is not None and DATA_START[1] >= DATA_START[2]:
                    raise ValueError(f"Data segment exceeded. start: {DATA_START[0]}"
                                     f"\ncurr: {DATA_START[1]}\n end: {DATA_START[2]}, {labels}")
            continue
        tf = line[0].split(".")
        flags = parse_flags(tf)
        line[0] = opcode
        code = parse_types(opcode, line)
        code += flags
        listarr[count] = code
        count += 1

    # PRINTER = False
    # PRINTER = "text"
    PRINTER = "copy"
    arr1 , arr2 = list_to_huge_string(listarr)
    if PRINTER == "text":
        print(arr1)
        print()
        print(arr2)
    elif PRINTER == "copy":
        py.copy(arr1)
        input("type a key to copy second encoded string...\n")
        py.copy(arr2)
