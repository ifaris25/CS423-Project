import re
import instfile
file = open('input.sic','r')
print()
filecontent = []
bufferindex = 0
tokenval = 0
lineno = 1
pass1or2 = 1
locctr = 0
lookahead = ''
startLine = True
symtable = []
class Entry:
    def __init__(self,string,token,attribute):
        self.string=string
        self.token=token
        self.att=attribute

def lookup(s):
    for i in range(0,symtable.__len__()):
        if s == symtable[i].string:
            return i
    return -1

def insert(s,t,a):
    symtable.append(Entry(s,t,a))
    return symtable.__len__()-1

def init():
    for i in range(0,instfile.inst.__len__()):
        insert(instfile.inst[i], instfile.token[i], instfile.opcode[i])
    for i in range(0,instfile.directives.__len__()):
        insert(instfile.directives[i], instfile.dirtoken[i], instfile.dircode[i])


def error(s):
    global lineno
    print('line '+str(lineno)+': '+s)


def match(token):
    global lookahead
    if lookahead == token:
        lookahead=lexan()
    else:
        error("match error")



def parse():
    global lookahead
    lookahead = lexan()
    header()
    body()
    tail()


def header():
    match('ID')
    match('START')
    match('NUM')




def body():
    global lookahead
    if lookahead=='ID':
        match('ID')
        rest1()
        body()
    elif lookahead == 'F3':
        stmt()
        body()
    elif lookahead=='END':
        return
    else:
        error('body error')
def rest1():
    if lookahead == 'F3':
        stmt()
    elif lookahead in ["WORD", "BYTE", "RESW", "RESB"]:
        data()
    else:
        error('rest1 erorr')



def stmt():
    match('F3')
    rest3()

def data():
    if lookahead in ["WORD","RESW", "RESB"]:
        match(lookahead)
        match('NUM')
    elif lookahead == 'BYTE':
        match('BYTE')
        rest2()
    else:
        error('data erorr')

def rest3():
    if lookahead == 'ID':
        match('ID')
        index()
    elif lookahead=='END':
        return
    else:
        error('rest3 error')

def rest2():
    if lookahead=='STRING':
        match('STRING')
    elif lookahead=='HEX':
        match('HEX')
    else:
        error('rest2 erorr')


def index():
    global bufferindex, symtable, tokenval
    if lookahead == ',':
        match(',')
        if symtable[tokenval].att!=1:
            error('index register should be X')
        match("REG")
        return True
    return False


def tail():
    match('END')
    match('ID')


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
    elif filecontent[bufferindex] in ['+', '#', ',']:
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
            bytestring = '_' + bytestring
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
            bytestring = '_' + bytestring
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
            bytestring = '_' + bytestring
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


def is_hex(s):
    if s[0:2].upper() == '0X':
        try:
            int(s[2:], 16)
            return True
        except ValueError:
            return False
    else:
        return False

def main():
    global file, filecontent, locctr, pass1or2, bufferindex, lineno
    init()
    w = file.read()
    filecontent=re.split("([\W])", w)
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

print('1')
main()



