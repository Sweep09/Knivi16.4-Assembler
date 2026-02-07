OPCODES = {
    "halt": [0],
    "and": [1],
    "or": [2],
    "xor": [3],
    "nor": [4],
    "add": [5],
    "sub": [6],
    "adc": [7],
    "sbb": [8],
    "shl": [9],
    "shr": [10],
    "rol": [11],
    "ror": [12],
    "extb": [13],
    "rng8": [14],

    "cmp": [15],
    "scmp": [16],
    "mov": [17],
    "j": [18],
    "ld": [19],
    "st": [20],
    "in": [21],
    "out": [22],
    "swap": [23],
    "cores": [24],
    "start": [25],
    "resume": [26],
    "stop": [27],
    "ctx": [28],
}

CONDITIONS = {
    "true": 0,
    "gt": 1,
    "ge": 2,
    "eq": 3,
    "le": 4,
    "lt": 5,
    "ne": 6,
    "gz": 7,
    "gez": 8,
    "ez": 9,
    "lez": 10,
    "lz": 11,
    "nz": 12,
    "c": 13,
    "ov": 14,
    "false": 15
}

FLAG_CATS = {
    "DATA": {"set":0x400000},
    "MEM": {"set":0x400000,"pc":0x100, "st":0x200,"h":0x400, "l":0},
    "THREAD": {None:0},
    "J": {None: 0},
    "M": {"set":0x400000},
    "SET": {None: 0},
    "NULL": {None: 0},
    "CORES": {"set":0x400000},
}

REGS = {
    "r0",
    "r1",
    "r2",
    "r3",
    "r4",
    "r5",
    "r6",
    "r7",
    "r8",
    "r9",
    "r10",
    "r11",
    "r12",
    "r13",
    "r14",
    "r15"
}

CODE_TYPES = [
    "DATA",
    "MEM",
    "THREAD",
    "J",
    "M",
    "SET",
    "NULL",
    "CORES",
]

CODE_ASSO = {
    "and": CODE_TYPES[0],
    "or": CODE_TYPES[0],
    "xor": CODE_TYPES[0],
    "nor": CODE_TYPES[0],
    "add": CODE_TYPES[0],
    "sub": CODE_TYPES[0],
    "adc": CODE_TYPES[0],
    "sbb": CODE_TYPES[0],
    "shl": CODE_TYPES[0],
    "shr": CODE_TYPES[0],
    "rol": CODE_TYPES[0],
    "ror": CODE_TYPES[0],
    "extb": CODE_TYPES[0],
    "rng8": CODE_TYPES[0],

    "ld": CODE_TYPES[1],
    "st": CODE_TYPES[1],
    "in": CODE_TYPES[1],
    "out": CODE_TYPES[1],
    "swap": CODE_TYPES[1],

    "ctx": CODE_TYPES[3],

    "j": CODE_TYPES[3], # check for first letter

    "mov": CODE_TYPES[4],

    "cmp": CODE_TYPES[5],
    "scmp": CODE_TYPES[5],

    "cores": CODE_TYPES[6],
    "halt": CODE_TYPES[6],

    "start": CODE_TYPES[7],
    "resume": CODE_TYPES[7],
    "stop": CODE_TYPES[7],
}
