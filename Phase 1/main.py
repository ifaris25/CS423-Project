import re
import instfile
file = open('input.sic','r')
filecontent = []
bufferindex = 0
tokenval = 0
lineno = 1
pass1or2 = 1
locctr = 0
lookahead = ''
startLine = True
symtable = []
inst=0
Xbit4set = 0x800000
Bbit4set = 0x400000
Pbit4set = 0x200000
Ebit4set = 0x100000

Nbitset = 2
Ibitset = 1

Xbit3set = 0x8000
Bbit3set = 0x4000
Pbit3set = 0x2000
Ebit3set = 0x1000
objCode= True
reLoc=[]

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
    global reLoc
    header()
    body()
    if pass1or2==2:
        for list in reLoc:
            print('M{:06X} 04'.format(list)) # 2 byte and always is 05 for the changing address)
    tail()


def header():
    global lookahead,tokenval,locctr,programAddress,programSize,progName
    lookahead = lexan()
    tok = tokenval
    match('ID')
    match('START')
    programAddress= symtable[tok].att=locctr = tokenval
    match('NUM')
    progName = symtable[tok].string
    if pass1or2==2 and objCode:
        print('H',progName,'{:06X} {:06X}'.format(programAddress,programSize))




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
    global startLine,locctr,inst,reLoc
    startLine = False
    locctr+=3
    if pass1or2==2:
        inst= symtable[tokenval].att << 16
    if pass1or2==2:
        reLoc.append(locctr-2) #----------------check
    match('F3')
    rest3()
    if pass1or2==2:
        if objCode:
            print('T{:06X} {:02X} {:06X}'.format(locctr-3,3,inst))
        else:
            print('{:06X}'.format(inst))

def data():
    global locctr,reLoc
    if lookahead=="WORD":
        locctr+=3
        match("WORD")
        if pass1or2==2:
            
            if objCode:
                print('T{:06X} {:02X} {:06X}'.format(locctr-3,3,tokenval))
            else:
                print('T{:06X}'.format(tokenval))
        match('NUM')
    elif lookahead=='RESW':
        locctr+=3*tokenval
        match('RESW')
        if pass1or2==2 and not objCode:
            for i in range(tokenval):
                print('000000')
        match("NUM")
    elif lookahead == "RESB":
        match("RESB")
        locctr+=tokenval
        if pass1or2==2 and not objCode:
            for i in range(tokenval):
                print('00')
        match('NUM')
    elif lookahead == 'BYTE':
        match('BYTE')
        rest2()
    else:
        error('data erorr')

def rest3():
    global inst
    
    if lookahead == 'ID':
        inst += symtable[tokenval].att
        match('ID')
        index()
    elif lookahead=='END':
        return
    else:
        error('rest3 error')

def rest2():
    global locctr,reLoc
    size = int(len(symtable[tokenval].att)/2)
    locctr+=size
    if lookahead=='STRING':
        if pass1or2==2:
            if objCode:
                print('T{:06X} {:02X}'.format(locctr-size,size,hex),symtable[tokenval].att)
            else:
                print(symtable[tokenval].att)
        match('STRING')
    elif lookahead=='HEX':
        if pass1or2==2:
            if objCode:
                print('T{:06X} {:02X}'.format(locctr-size,size,hex),symtable[tokenval].att)
            else:
                print(symtable[tokenval].att)
        match('HEX')
    else:
        error('rest2 erorr')


def index():
    global bufferindex, symtable, tokenval,inst
    if lookahead == ',':
        match(',')
        if symtable[tokenval].att!=1:
            error('index register should be X')
        else:
            inst+=Xbit3set
        match("REG")
        return True
    return False


def tail():
    global programAddress,programSize,locctr
    match('END')
    if pass1or2==2 and objCode:
        print('E{:06X}'.format(symtable[tokenval].att))
    match('ID')
    programSize = locctr-programAddress
    # if pass1or2==2:
    #     for i in range(symtable.__len__()):
    #         if symtable[i].token=='ID':
    #             print(symtable[i].string+' '+str(hex(symtable[i].att)))


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
            bytestring = '2_' + bytestring
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

main()



