RISC_CODES = {
    # handle lui/auipc separately
    # handle jumps/branches separately
    "add" : "add",
    "sub" : "sub",

    "slt" : "slt",      # macro
    "slti" : "slt",
    "sltu" : "sltu",
    "sltiu" : "sltu",   #

    "sll" : "shl",
    "slli" : "shl",
    "srl" : "shr",
    "srli" : "shr",
    "sra" : "arithmetic_shift_error",
    "srai" : "arithmetic_shift_error",

    "xor" : "xor",
    "xori" : "xori",
    "or" : "or",
    "ori" : "or",
    "and" : "and",
    "andi" : "and",

    "lb" : "ld",
    "lh" : "ld",
    "lbu" : "ld",
    "lhu" : "ld",
    "lw" : "ld",
    "sb" : "st",
    "sh" : "st",
    "sw" : "st",
}

REGISTER_MAP = {
    "zero" : "r0",
    "t0": "r1",
    "t1": "r2",
    "t2": "r3",
    "a0" : "r4",
    "a1" : "r5",
    "a2" : "r6",
    "a3" : "r7",
    "a4" : "r8",
    "a5" : "r9",
    "s1" : "r10",
    "s0" : "r11",
    "fp" : "r11",
    "tp" : "r12",
    "gp" : "r13",
    "ra" : "r14",
    "sp" : "r15",
}

def parse_program(prog:list[str]) -> list[str]:
    new_prog = []
    file_detected = False
    count = 0
    last_value = [0,0]
    for i, line in enumerate(prog):
        line = line.strip()
        if not line:
            continue
        if not file_detected:
            # check if file header is proper format
            file_detected = True
            continue
        if line[:2] == "Di":
            continue
        line = line.split("#")[0].split(" ", 1)[-1].replace(",", " ").replace("\t", " ").strip()
        line = line.split()
        line[0] = RISC_CODES.get(line[0],line[0])
        match line[0]:
            case "lui":     # BAD: throws away upper 16 bits for now
                last_value[0] = i
                last_value[1] = int(line[2],0)&0xF
                if int(line[2],0) > 0xf:
                    line = ["mov",line[1],line[1],'0']
                else:
                    continue
            case "auipc":   # assumes jumping to label
                continue
            case "jal":
                if line[1] == "ra":
                    line = ["call", line[3]]
                elif line[1] == "zero":
                    line = ["j", line[3]]
                else:
                    raise ValueError(f"Unexpected case. {line}")
            case "jalr":
                if line[1] == "zero" and line[2] == "0(ra)":
                    line = ["ret"]
                elif line[1] == "ra":
                    line = ["call", line[3]]
                else:
                    raise ValueError(f"Unexpected case. {line}")
            case "addi":
                if last_value[0] == i-1:
                    line[3] = str(int(line[3],0)|(last_value[1]<<12))
                if int(line[3],0) < 0:
                    line[0] = "sub"
                    line[3] = str(-int(line[3],0))
                else:
                    line[0] = "add"

        if line[0][0] == "b":
            if len(line) == 4:
                line = ["call." + line[0][1:-1], line[3]]
            else:
                raise ValueError(f"Expected list of length 4. {line}")
        temp = ""
        for v,t in enumerate(line):
            if t.find("(") != -1:
                idx = t.find("(")
                temp = t[:idx]
                t = REGISTER_MAP.get(t[idx+1:-1],t[idx+1:-1])
            else:
                t = REGISTER_MAP.get(t,t)
            line[v] = t
        if temp:
            if int(temp,0) > 0:
                line.append("+")
                line.append(temp)
            else:
                line.append("-")
                line.append(temp[1:])

        if count == 0:
            new_prog.append(["mov","r0","0"])
            new_prog.append(line)
            count += 1
        else:
            new_prog.append(line)
            count += 1
    return new_prog



if __name__ == "__main__":
    with open("output.txt","r",encoding="utf-8") as file:
        f = file.readlines()
    new_file = parse_program(f)
    print(new_file)
