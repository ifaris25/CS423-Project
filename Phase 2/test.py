import re
import instfile
from instfile import token


class Entry:
    def __init__(self, string, token, attribute):
        self.string = string
        self.token = token
        self.att = attribute


symtable = []

# print(symtable[12].string + ' ' + str(symtable[12].token) + ' ' + str(symtable[12].att))

def lookup(s):
    for i in range(0,symtable.__len__()):
        if s == symtable[i].string:
            return i
    return -1

def insert(s, t, a):
    symtable.append(Entry(s,t,a))
    return symtable.__len__()-1

def init():
    for i in range(0,instfile.inst.__len__()):
        insert(instfile.inst[i], instfile.token[i], instfile.opcode[i])
    for i in range(0,instfile.directives.__len__()):
        insert(instfile.directives[i], instfile.dirtoken[i], instfile.dircode[i])

file = open('input.sic', 'r')
filecontent = []
bufferindex = 0
tokenval = 0
lineno = 1
pass1or2 = 1
locctr = 0
lookahead = ''
startLine = True
inst = 0
objCode = True
objBuffer = ''
maxBuffer = 10
addressBuffer = 0
objLength = 0
baseValue = -1

Xbit4set = 0x800000
Bbit4set = 0x400000
Pbit4set = 0x200000
Ebit4set = 0x100000
Ibit4set = 0x1000000
Nbit4set = 0x2000000

Nbitset = 2
Ibitset = 1

Xbit3set = 0x8000
Bbit3set = 0x4000
Pbit3set = 0x2000
Ebit3set = 0x1000
Ibit3set = 0x10000
Nbit3set = 0x20000


def is_hex(s):
    if s[0:2].upper() == '0X':
        try:
            int(s[2:], 16)
            return True
        except ValueError:
            return False
    else:
        return False

def lexan():
    global filecontent, tokenval, lineno, bufferindex, locctr, startLine

    while True:
        # if filecontent == []:
        if len(filecontent) == bufferindex:
            return 'EOF'
        elif filecontent[bufferindex] == '\n':
            startLine = True
            # del filecontent[bufferindex]
            bufferindex = bufferindex + 1
            lineno += 1
        else:
            break
    if filecontent[bufferindex].isdigit():
        tokenval = int(filecontent[bufferindex])  # all number are considered as decimals
        # del filecontent[bufferindex]
        bufferindex = bufferindex + 1
        return ('NUM')
    elif is_hex(filecontent[bufferindex]):
        tokenval = int(filecontent[bufferindex][2:], 16)  # all number starting with 0x are considered as hex
        # del filecontent[bufferindex]
        bufferindex = bufferindex + 1
        return ('NUM')
    elif filecontent[bufferindex] in ['+', '#', ',','@']:
        c = filecontent[bufferindex]
        # del filecontent[bufferindex]
        bufferindex = bufferindex + 1
        return (c)
    else:
        # check if there is a string or hex starting with C'string' or X'hex'
        if (filecontent[bufferindex].upper() == 'C') and (filecontent[bufferindex+1] == '\''):
            bytestring = ''
            bufferindex += 2
            while filecontent[bufferindex] != '\'':  # should we take into account the missing ' error?
                bytestring += filecontent[bufferindex]
                bufferindex += 1
                if filecontent[bufferindex] != '\'':
                    bytestring += ' '
            bufferindex += 1
            bytestringvalue = "".join("%02X" % ord(c) for c in bytestring)
            bytestring = '1_' + bytestring
            p = lookup(bytestring)
            if p == -1:
                p = insert(bytestring, 'STRING', bytestringvalue)  # should we deal with literals?
            tokenval = p
        elif (filecontent[bufferindex] == '\''): # a string can start with C' or only with '
            bytestring = ''
            bufferindex += 1
            while filecontent[bufferindex] != '\'':  # should we take into account the missing ' error?
                bytestring += filecontent[bufferindex]
                bufferindex += 1
                if filecontent[bufferindex] != '\'':
                    bytestring += ' '
            bufferindex += 1
            bytestringvalue = "".join("%02X" % ord(c) for c in bytestring)
            bytestring = '1_' + bytestring
            p = lookup(bytestring)
            if p == -1:
                p = insert(bytestring, 'STRING', bytestringvalue)  # should we deal with literals?
            tokenval = p
        elif (filecontent[bufferindex].upper() == 'X') and (filecontent[bufferindex+1] == '\''):
            bufferindex += 2
            bytestring = filecontent[bufferindex]
            bufferindex += 2
            # if filecontent[bufferindex] != '\'':# should we take into account the missing ' error?

            bytestringvalue = bytestring
            if len(bytestringvalue)%2 == 1:
                bytestringvalue = '0'+ bytestringvalue
            bytestring = '2_' + bytestring
            p = lookup(bytestring)
            if p == -1:
                p = insert(bytestring, 'HEX', bytestringvalue)  # should we deal with literals?
            tokenval = p
        else:
            p=lookup(filecontent[bufferindex].upper())
            if p == -1:
                if startLine == True:
                    p=insert(filecontent[bufferindex].upper(),'ID',locctr) # should we deal with case-sensitive?
                else:
                    p=insert(filecontent[bufferindex].upper(),'ID',-1) #forward reference
            else:
                if (symtable[p].att == -1) and (startLine == True):
                    symtable[p].att = locctr
            tokenval = p
            # del filecontent[bufferindex]
            bufferindex = bufferindex + 1
        return (symtable[p].token)


def error(s):
    global lineno
    print('line ' + str(lineno) + ': '+s)


def match(token):
    global lookahead
    if lookahead == token:
        lookahead = lexan()
    else:
        error('Syntax error Match function')


def index(extend):
    global inst
    global bufferindex, symtable, tokenval
    if lookahead == ',':
        match(',')
        if symtable[tokenval].att != 1:
            error('index regsiter should be X')
        else:
            if extend:
                inst += Xbit4set
            else:
                inst += Xbit3set

        match('REG')
        return True
    return False

def addToBuffer(loc,length,inst):
    global maxBuffer, objBuffer,addressBuffer,objLength


    objLeng = int(len(objBuffer)/2)
    if(objLength + length <= maxBuffer and objLeng != 0):
        objBuffer += ","+inst
        objLength += length
    else:
        if objLeng != 0:
            objBuffer = 'T{:06X}|{:02X}|'.format(addressBuffer,objLength) + objBuffer
            print(objBuffer)
        objLength = length
        objBuffer = inst
        addressBuffer = loc


def header():
    # HEADER → ID START NUM
    global lookahead,locctr, startAddress, progSize
    tok = tokenval
    match("ID")
    match("START")
    startAddress = symtable[tok].att = locctr = tokenval
    match("NUM")
    if pass1or2 == 2 and objCode:
        print('H'+symtable[tok].string+' {:06X} {:06X}'.format(startAddress,progSize))

def body():
    # BODY → ID REST1 BODY | STMT BODY | ε
    global baseValue,startLine
    if lookahead == "ID":
        match("ID")
        rest1()
        body()
    elif lookahead in ["F1","F2","F3","+"]:
        stmt()
        body()
    elif lookahead == "BASE":
        startLine = False
        match("BASE")
        if pass1or2 == 2:
            baseValue = symtable[tokenval].att
        match("ID")
        body()
    elif lookahead == "END": # if there is ε you have to put the after this statment which is tail = end
        return
    else:
        error("Syntax Error Body")


    pass
def tail():
    # TAIL → END ID
    global startAdress, progSize,objBuffer,addressBuffer,objLength
    match("END")
    if pass1or2 == 2 and objCode:
        objBuffer = 'T{:06X}|{:02X}|'.format(addressBuffer, objLength) + objBuffer
        #print(objBuffer)

        print('E{:06X}'.format(symtable[tokenval].att))
    match("ID")
    progSize = locctr - startAddress
    # if pass1or2 == 1:
    #     for i in symtable:
    #         if i.token == 'ID':
    #             print(i.string+ ' '+ str(hex(i.att)))



def rest1():
    # REST1 → STMT | DATA
    if lookahead in ["F1","F2","F3","+"]:
        stmt()
    elif lookahead in ["WORD","RESW","RESB","BYTE"]:
        data()
    else:
        error("Syntax Error rest1")

def stmt():
    # STMT → F3 rest3

    # STMT -> F1 | F2 REG rest4 | F3 rest5| + F3 rest5

    global startLine, locctr, inst,objBuffer,maxBuffer,baseValue
    startLine = False
    # if pass1or2 == 2:
    #     inst = symtable[tokenval].att << 16
    # locctr += 3

    if lookahead == "F1":
        locctr += 1
        if pass1or2 == 2:
            inst = symtable[tokenval].att
            if objCode:
                print('T{:06X} {:02X} {:02X}'.format(locctr - 1, 1, inst))
            else:
                print('{:02X}'.format(inst))

        match("F1")

    elif lookahead == "F2":
        locctr += 2
        if pass1or2 == 2:
            inst = symtable[tokenval].att << 8
        match("F2")
        if pass1or2 == 2:
            inst += symtable[tokenval].att << 4
        match("REG")
        rest4()

        if pass1or2 == 2:
            if objCode:
                print('T{:06X} {:02X} {:04X}'.format(locctr - 2, 2, inst))
            else:
                print('{:04X}'.format(inst))
    elif lookahead == "F3":
        locctr += 3
        if pass1or2 == 2:
            inst = symtable[tokenval].att << 16 # OPCOOOOODE
        match("F3")

        rest5(False)


        if pass1or2 == 2:
            if objCode:
                print('T{:06X} {:02X} {:06X}'.format(locctr - 3, 3, inst))
            else:
                print('{:06X}'.format(inst))

    elif lookahead == "+":
        locctr += 4
        match("+")
        if pass1or2 == 2:
            inst = symtable[tokenval].att << 24
        match("F3")
        rest5(True)

        if pass1or2 == 2:
            if objCode:
                print('T{:06X} {:02X} {:08X}'.format(locctr - 4, 4, inst))
            else:
                print('{:08X}'.format(inst))
    else:
        error("Syntax error STMT")


    # if pass1or2 == 2:
    #     if objCode:
    #         addToBuffer(locctr - 3,3,'{:06X}'.format(inst))
    #     else:
    #         print('{:06X}'.format(inst))

def rest4():
    global inst
    if lookahead == ",":
        match(",")
        if pass1or2 == 2:
            inst += symtable[tokenval].att
        match("REG")
    else:
        return


def rest5(extended):

    # Xbit4set = 0x800000
    # Bbit4set = 0x400000
    # Pbit4set = 0x200000
    # Ebit4set = 0x100000
    #
    # Nbitset = 2
    # Ibitset = 1

    # Ibit3set = 0x10000
    # Nbit3set = 0x20000

    # Ibit4set = 0x1000000
    # Nbit4set = 0x2000000
    #
    # Xbit3set = 0x8000
    # Bbit3set = 0x4000
    # Pbit3set = 0x2000
    # Ebit3set = 0x1000
    if pass1or2 == 2:
        pass

    global inst,baseValue
    if extended:
        inst += Ebit4set
        # P and b are zeros so don't change it

    if lookahead == "#":
        print("i am here")
        if extended:
            inst += Ibit4set
        else:
            inst += Ibit3set

        match("#")
        rest6(extended)
    elif lookahead == "@":
        if extended:
            inst += Nbit4set
        else:
            inst += Nbit3set

        match("@")
        rest6(extended)
    elif lookahead == "ID":
        if extended:
            inst += Nbit4set
            inst += Ibit4set
        else:
            inst += Nbit3set
            inst += Ibit3set
        rest6(extended)
        index(extended)

    elif lookahead == "NUM":
        if extended:
            inst += Nbit4set
            inst += Ibit4set
        else:
            inst += Nbit3set #edit here
            inst += Ibit3set


        rest6(extended)
        index(extended)
    else:
        error("Syntax error REST5")

def rest6(extended):
    global inst,baseValue
    if lookahead == "ID":
        if extended:
            inst += symtable[tokenval].att

        if pass1or2 == 2 and not extended:
            disp = symtable[tokenval].att - locctr
            if -2047 <= disp <= 2048:
                inst += (disp & 0xFFF)
                inst += Pbit3set
            elif baseValue < 0:
                error("No Base Value")
            else:
                disp = symtable[tokenval].att - baseValue
                if -2047 <= disp <= 2048:
                    inst+= (disp & 0xFFF)
                    inst += Bbit3set
                else:
                    error("you can't handle the Value")
        match("ID")
    elif lookahead == "NUM":
        if extended:
            inst += tokenval


        if pass1or2 == 2 and not extended:
            disp = tokenval - locctr
            if -2047 <= tokenval <= 2048:    #edit here same down
                inst += (tokenval & 0xFFF)
            elif -2047 <= disp <= 2048:
                inst += (disp & 0xFFF)
                inst += Pbit3set
            elif baseValue < 0:
                error("No Base Value")
            else:
                disp = tokenval - baseValue #from 0 to 4000 edit here
                if -2047 <= disp <= 2048:
                    inst+= (disp & 0xFFF)
                    inst += Bbit3set
                else:
                    error("you can't handle the Value")

        match("NUM")
    else:
        error("Syntax error REST6")
# def rest3():
#     # Rest3 → ID INDEX | ε
#     global inst
#     if lookahead == "ID":
#         inst += symtable[tokenval].att
#         match("ID")
#         index()

def data():
    # DATA → WORD NUM | RESW NUM | RESB NUM | BYTE REST2
    global locctr,objBuffer,maxBuffer
    if lookahead == "WORD":
        locctr+=3
        match("WORD")
        if pass1or2 == 2:
            if objCode:
                #addToBuffer(locctr - 3, 3, '{:06X}'.format(tokenval))
                print('T{:06X} {:02X} {:06X}'.format(locctr-3,3,tokenval))
            else:
                print('{:06X}'.format(tokenval))
        match("NUM")
    elif lookahead == "RESW":
        match("RESW")
        locctr += 3*tokenval
        if pass1or2 == 2:
            if objCode:
                pass
            else:
                for i in range(tokenval):
                    print('000000')
        match("NUM")
    elif lookahead == "RESB":
        match("RESB")
        locctr += tokenval
        if pass1or2 == 2:
            if objCode:
                pass
            else:
                for i in range(tokenval):
                    print('00')
        match("NUM")
    elif lookahead == "BYTE":
        match("BYTE")
        rest2()
    else:
        error("Syntax Error data")

def rest2():
    #REST2 → STRING | HEX
    global locctr,objBuffer,maxBuffer
    size = int(len(symtable[tokenval].att)/2) #So here we divide by 2 because 2 hex is 1 byte ==> and 1 character is 1 byte
    locctr+=size
    if lookahead == "STRING":
        if pass1or2 == 2:
            if objCode:
                print('T{:06X} {:02X} '.format(locctr-size,size) + symtable[tokenval].att)
                # addToBuffer(locctr-size, size, symtable[tokenval].att)
            else:
                print(symtable[tokenval].att)
        match("STRING")
    elif lookahead == "HEX":
        if pass1or2 == 2:
            if objCode:
                # addToBuffer(12 + (size*2), 'T{:06X} {:02X} '.format(locctr - size, size) + symtable[tokenval].att)
                # addToBuffer(locctr - size, size, symtable[tokenval].att)
                print('T{:06X} {:02X} '.format(locctr - size, size) + symtable[tokenval].att)
            else:
                print(symtable[tokenval].att)
        match("HEX")
    else:
        error("Syntax Error rest2")

def parse():
    global lookahead

    lookahead = lexan()

    # write the parser here
    header()
    body()
    tail()

    # PARSER → HEAD BODY TAIL
    # HEAD → ID START NUM
    # TAIL → END ID
    # BODY → ID REST1 BODY | STMT BODY | ε
    # REST1 → STMT | DATA
    # STMT → F3 rest3
    # Rest3 → ID INDEX | ε
    # INDEX → , REG | ε
    # DATA → WORD NUM | RESW NUM | RESB NUM | BYTE REST2
    # REST2 → STRING | HEX

    pass


def main():
    global file, filecontent, locctr, pass1or2, bufferindex, lineno

    init()
    w = file.read()
    filecontent = re.split(r'([\W])', w)
    i=0
    while True:
        while (filecontent[i] == ' ') or (filecontent[i] == '') or (filecontent[i] == '\t'):
            del filecontent[i]
            if len(filecontent) == i:
                break
        i += 1
        if len(filecontent) <= i:
            break
    if filecontent[len(filecontent)-1] != '\n': #to be sure that the content ends with new line
        filecontent.append('\n')
    for pass1or2 in range(1,3):
        parse()
        bufferindex = 0
        locctr = 0
        lineno = 1

    file.close()


main()