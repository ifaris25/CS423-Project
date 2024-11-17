import re
import instfile
file = open('input.sic','r')
filecontent = []
bufferindex = 0
tokenval = 0
lineno = 1
progSize=0
pass1or2 = 1
lookahead = ''
startLine = True
symtable = []
inst=0
baseValue=-1
programAddress=0
Xbit3set = 0x8000               
Bbit3set = 0x4000
Pbit3set = 0x2000
Ebit3set = 0x1000
Ibit3set = 0x10000
Nbit3set = 0x20000


Xbit4set = 0x800000
Bbit4set = 0x400000
Pbit4set = 0x200000
Ebit4set = 0x100000
Ibit4set = 0x1000000
Nbit4set = 0x2000000

Nbitset = 2
Ibitset = 1

objCode= True

reLoc=[] 

locctr = [0,0,0]
block = 0


locctr_size=[0,0,0]

class Entry:
    def __init__(self,string,token,attribute,block):
        self.string=string
        self.token=token
        self.att=attribute
        self.block=block

def lookup(s):
    for i in range(0,symtable.__len__()):
        if s == symtable[i].string:
            return i
    return -1

def insert(s,t,a,b=0):
    symtable.append(Entry(s,t,a,b))
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
    # parse ---> header body  tail
    global reLoc,symtable
    header()
    body()
    if pass1or2==2:
        for list in reLoc:
            print('M{:06X} 05'.format(list)) # 2 byte and always is 05 for the changing address
 
    
    
            
    tail()
    # if pass1or2==1:
    #     for sy in symtable:
    #         print(sy.string,' ',sy.token,' ',sy.att,' ',sy.block)
        
    
  


def header():
    # header ---> id start num
    global lookahead,tokenval,locctr,startAddress,progSize,block
    block=0 
    lookahead= lexan()
    tok=tokenval
    match('ID')
    match('START')
    startAddress=symtable[tok].att=locctr[block]=tokenval
    match('NUM')
    progName=symtable[tok].string
    if pass1or2==2 and objCode:
        print('H'+symtable[tok].string+' {:06X} {:06X}'.format(startAddress,progSize))
    

def body():
    # body ---> id rest1 body | stmt body | &
    global baseValue,startLine,block
    if lookahead=='ID':
        symtable[tokenval].block=block
        match("ID")
        rest1()
        body()
    elif lookahead=='BASE':
        startLine = False
        match('BASE')
        if pass1or2==2:
            baseValue = symtable[tokenval].att
            # print(baseValue)
        match('ID')
        body()
        
    elif lookahead in ['F1','F2','F3','+','F5']:
        stmt()
        body()
    elif lookahead=='USE':
        match('USE')
        rest7()
        body()
        
    elif lookahead=='END':
        return
    else:
        error('body error')
    
        
def rest7():
    global block,locctr
    if lookahead=='CDATA':
        block=1
        
        match('CDATA')
    elif lookahead=='CBLKS':
        block=2
        
        match('CBLKS')
    elif lookahead in ['ID','BASE','USE','F1','F2','F3','+','F5','END']: # deal with epsilon
        block=0
        return
    else:
        error('Rest7 sytntax error')

def rest1():
    if lookahead in['F1','F2','F3','+']:
        stmt()
    elif lookahead in ["WORD", "BYTE", "RESW", "RESB"]:
        data()
    else:
        error('rest1 erorr')


def stmt():
    # stmt ---> F1 | F2 Reg rest4 | F3 Rest5(bool) | + F3 Rest5(bool) 
    global locctr,inst,startLine,reLoc,block
    startLine=False
    if lookahead=='F1':
        locctr[block] += 1
        if pass1or2==2:
            inst=symtable[tokenval].att

            if objCode:
                print('T{:06X} {:02X} {:02X}'.format(locctr[block]-1,1,inst))
            else:
                print('{:02X}'.format(inst))
        match('F1')
    
    
    elif lookahead=='F2':
        locctr[block]+=2
        if pass1or2==2:
            inst=symtable[tokenval].att<<8
            
        match('F2')
        if pass1or2==2:
            inst+=symtable[tokenval].att<<4
        match('REG')
        rest4()
        if pass1or2==2:
            if objCode:
                print('T{:06X} {:02X} {:04X}'.format(locctr[block]-2,2,inst))
            else:
                print('{:04X}'.format(inst))
                
                
    elif lookahead=='F3':
        locctr[block]+=3
        if pass1or2==2:
            inst=symtable[tokenval].att <<16 # to get the opcode
            
        if symtable[tokenval].string == 'RSUB':
            match('F3')
        else:
            match('F3')
            rest5(False)
        if pass1or2==2:
            if objCode:
                print('T{:06X} {:02X} {:06X}'.format(locctr[block]-3,3,inst))
            else:
                print('{:06X}'.format(inst))
        
        
    elif lookahead=='+':
        locctr[block]+=4
        match('+')
        if pass1or2==2:
            inst=symtable[tokenval].att<<24
            inst += Ebit4set
            reLoc.append(locctr[block]-3)   ### check --------------------------------
        match('F3')
        rest5(True)
        if pass1or2==2:
            if objCode:
                print('T{:06X} {:02X} {:08X}'.format(locctr[block]-4,4,inst))
            else:
                print('{:08X}'.format(inst))


    ## Quiz
    # elif lookahead=='F5':
    #     locctr[block]+=4
    #     if pass1or2==2:
    #         inst=symtable[tokenval].att<<24
    #     match('F5')
    #     if pass1or2==2:
    #         inst+=symtable[tokenval].att<<16
    #     match('REG')
    #     match(',')
    #     if pass1or2==2:
    #         inst+=symtable[tokenval].att<<8
    #     match('REG')
    #     match(',')
    #     if pass1or2==2:
    #         inst+=symtable[tokenval].att
    #     match('REG')
        
    #     if pass1or2==2:
    #         if objCode:
    #             print('T{:06X} {:02X} {:08X}'.format(locctr[block]-4,4,inst)) # Machine code
    #         else:
    #             print('{:08X}'.format(inst)) # Object Code



    


    else:
        error('stmt error')
        
def rest5(ex): # if ex= true mean F4 .... ex=false mean F3
    # Rest5 --> # Rest6 
    global inst,baseValue

    if lookahead=='#':
        if pass1or2==2:
            if ex:
                inst+=Ibit4set
            else:
                inst+=Ibit3set
        match('#')
        rest6(ex)
        
        
        
    elif lookahead=='@':
        if pass1or2==2:
            if ex:
                inst+=Nbit4set
            else:
                inst+=Nbit3set
        match('@')
        rest6(ex)
        
        
    elif lookahead=='ID':
        if pass1or2 == 2:
            if ex:
                inst+=Nbit4set
                inst+=Ibit4set
                inst+=symtable[tokenval].att # it is in format 4
            else: # Format 3
                inst+=Nbit3set
                inst+=Ibit3set
                disp = symtable[tokenval].att - locctr[block] # Calc PC
                if -2048<=disp<=2047:
                    inst+=Pbit3set
                    inst+=(disp&0xfff)
                elif baseValue != -1:
                    disp = symtable[tokenval].att - baseValue  # Calc BASE
                    if 0<=disp<=4095:
                        inst += Bbit3set
                        inst += disp
                    else:
                        error("BASE can not handle the value")
                else:
                    error("No BASE")
                    
        match('ID')
        index(ex)
        
        
    elif lookahead=='NUM':
        if pass1or2 == 2:
            if ex:
                inst+= Ibit4set
                inst += Nbit4set
                inst += tokenval
            else:
                inst += Ibit3set
                inst += Nbit3set
                disp = tokenval - locctr[block]  # Calc PC    disp = TA - PC
                if 0<tokenval<4095:
                    inst += (tokenval & 0xFFF)
                elif -2048 <= disp <= 2047:
                    inst += Pbit3set
                    inst += (disp & 0xFFF)
                elif baseValue != -1:
                    disp = tokenval - baseValue  # Calc BASE
                    if 0 <= disp <= 4095:
                        inst += Bbit3set
                        inst += (disp & 0xFFF)
                    else:
                        error('BASE can not handle the value')
                else:
                    error("No BASE")

        match('NUM')
        index(ex)
    else:
        error('rest 5 error')

def index(ex):
    global inst
    if lookahead == ',':
        match(',')
        if symtable[tokenval].att!=1:
            error('index register should be X')
        else:
            if pass1or2==2:
                if ex:
                    inst+=Xbit4set
                else:
                    inst+=Xbit3set
        match("REG")
        return True
    return False
        
        
def rest6(ex):
    global inst,baseValue
    if lookahead=='ID':
        if pass1or2 == 2:
            if ex:
                inst += symtable[tokenval].att # it is in format 4
            else:
                disp = symtable[tokenval].att - locctr[block]
                if -2048<=disp<=2047:
                    inst+=Pbit3set
                    inst += (disp & 0xFFF)
                elif baseValue!=-1:
                    disp = symtable[tokenval].att - baseValue
                    if 0<=disp<=4095:
                        inst+= (disp & 0xFFF)
                        inst+=Bbit3set
                    else:
                        error('BASE can not handle the value')
                else:
                    error("No BASE")
                
        match("ID")
    elif lookahead=='NUM':
        if pass1or2 == 2:
            if ex:
                inst += tokenval
                inst += Ibit4set
                inst += Nbit4set
            else:
                inst += Ibit3set
                inst += Nbit3set
                disp = tokenval - locctr[block]
                if 0 < tokenval < 4095:
                    inst += (tokenval & 0xFFF)
                elif -2048 <= disp <= 2047:
                    inst += Pbit3set
                    inst += (disp & 0xFFF)
                elif baseValue!=-1:
                    disp = tokenval-baseValue
                    if 0 <= disp <= 4095:
                        inst+= (disp & 0xFFF)
                        inst += Bbit3set
                else:
                    error("No BASE")
        match("NUM")
    else:
        error("rest6 error")
        


def rest4():
    global inst
    if lookahead==',':
        match(',')
        if pass1or2==2:
            inst+=symtable[tokenval].att
        match('REG')
    else:
        return


def tail():
    # end id
    global startAddress,progSize,locctr,locctr_size
    match('END')
    if pass1or2==2 and objCode:
        print('E{:06X}'.format(symtable[tokenval].att))
    match('ID')



    progSize= locctr[0]+locctr[1]+locctr[2]-startAddress
    locctr_size[0]=locctr[0]
    locctr_size[1]=locctr[0]   
    locctr_size[2]=locctr_size[1]+locctr[1]
    # defaultSize = locctr[0]
    # cdataSize = locctr[1]
    # cblckSize = locctr[2]
    for t in symtable:
        if t.block==1:
            t.att=locctr[0]+t.att
        if t.block==2:
            t.att=locctr[0]+locctr[1]+t.att

def data():
    global locctr
    if lookahead=="WORD":
        locctr[block]+=3
        match("WORD")
        if pass1or2==2:
            if objCode:
                print('T{:06X} {:02X} {:06X}'.format(locctr[block]-3,3,tokenval))
            else:
                print('T{:06X}'.format(tokenval))
        match('NUM')
    elif lookahead=='RESW':
        match('RESW')
        if pass1or2==2 and not objCode:
            for i in range(tokenval):
                print('000000')
        locctr[block]+=3*tokenval
        match("NUM")
    elif lookahead == "RESB":
        match("RESB")
        locctr[block]+=tokenval
        if pass1or2==2 and not objCode:
            for i in range(tokenval):
                print('00')
        match('NUM')
    elif lookahead == 'BYTE':
        match('BYTE')
        rest2()
    else:
        error('data erorr')
        
def rest2():
    global locctr
    size = int(len(symtable[tokenval].att)/2)
    locctr[block]+=size
    if lookahead=='STRING':
        if pass1or2==2:
            if objCode:
                print('T{:06X} {:02X}'.format(locctr[block]-size,size,hex),symtable[tokenval].att)
            else:
                print(symtable[tokenval].att)
        match('STRING')
    elif lookahead=='HEX':
        if pass1or2==2:
            if objCode:
                print('T{:06X} {:02X}'.format(locctr[block]-size,size,hex),symtable[tokenval].att)
            else:
                print(symtable[tokenval].att)
        match('HEX')
    else:
        error('rest2 erorr')




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
                    p=insert(filecontent[bufferindex].upper(),'ID',locctr[block]) # should we deal with case-sensitive?
                else:
                    p=insert(filecontent[bufferindex].upper(),'ID',-1) #forward reference
            else:
                if (symtable[p].att == -1) and (startLine == True):
                    symtable[p].att = locctr[block]
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
        locctr = locctr_size
        lineno = 1

    file.close()

main()
