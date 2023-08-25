teststr = """
        ("OBSdefine.EmCare.B11S1.DE01"=true) and ((    ("Age >= 2 months to <60 months")
             and ((    "OBSdefine.EmCare.B7.DE08" = true and "OBSdefine.EmCare.B11S2.DE02" ~ val."Skin Pinch goes back slowly (2 seconds or fewer, but not immediately)")
             or (    ("OBSdefine.EmCare.B11S2.DE06" = true or "OBSdefine.EmCare.B11S2.DE02" ~ val."Skin Pinch goes back slowly (2 seconds or fewer, but not immediately)" ) and ("OBSdefine.EmCare.B22.DE08" ~ val."Completely Unable to Drink" or "OBSdefine.EmCare.B22.DE08" ~ val."Vomits Immediately / Everything" or  "OBSdefine.EmCare.B22.DE14a"=true))
             or (    (ToInteger(Coalesce("OBSdefine.EmCare.B7.DE08" = true or  "OBSdefine.EmCare.B7.DE08a" = true,false)) + ToInteger(Coalesce("OBSdefine.EmCare.B11S2.DE01" = true,false)) +ToInteger(Coalesce("OBSdefine.EmCare.B11S2.DE02" ~ val."Skin Pinch goes back very slowly (More than 2 seconds,false))" )+ToInteger(Coalesce("OBSdefine.EmCare.B22.DE08" ~ val."Completely Unable to Drink" ,false))+ToInteger(Coalesce("OBSdefine.EmCare.B22.DE08" ~ val."Vomits Immediately / Everything",false))  + ToInteger(Coalesce("OBSdefine.EmCare.B22.DE14a"=true ,false))+ToInteger(Coalesce("OBSdefine.EmCare.B22.DE08" ~ val."Drinks Poorly",false)) )>1)))
         or (    (AgeInMonths()<2)
             and ((    (ToInteger(Coalesce("OBSdefine.EmCare.B11S2.DE01"=true,false)) +  ToInteger(Coalesce("OBSdefine.EmCare.B11S2.DE02" ~ val."Skin Pinch goes back very slowly (More than 2 seconds,false))") + ToInteger(Coalesce("OBSdefine.EmCare.B18S2.DE08" ~ val."Movement only when stimulated but then stops",false)) +ToInteger(Coalesce("OBSdefine.EmCare.B18S2.DE08" ~ val."No movement at all",false)))>1)
             or (    "OBSdefine.EmCare.B11S2.DE02" ~ val."Skin Pinch goes back very slowly (More than 2 seconds)" and ("OBSdefine.EmCare.B18S2.DE08" ~ val."Movement only when stimulated but then stops"  or "OBSdefine.EmCare.B18S2.DE08" ~ val."No movement at all" )))))

"""
import types

def get_name(i,bnd_out):
    limit = None
    hint = None
    label = None
    walki = 0
    prefix = None
    escape = 0
    l = len(i)
    # looking for hint
    if i[0] in NAME_BOUNDARY_IN:
        limit = NAME_BOUNDARY_OUT[NAME_BOUNDARY_IN.index(i[0])]
        start = 1
    elif len(i)>0 and i[0] in NAME_BOUNDARY_IN:
        limit = NAME_BOUNDARY_OUT[NAME_BOUNDARY_IN.index(i[1])]
        hint = i[0]
        start = 2
    else:
        start = 0
        out = None
    it=start
    for c in i[start:]:        
        if c not in OPERATORS and i[0] not in OPERATORS:
            if c == '\\':
                escape = it+1    
            elif c == limit and it != escape:
                break	
            elif limit is None:
                if c in WALK:
                    prefix = i[start:it]
                    [dump1, dump2, label, itt] = get_name(i[it+1:],bnd_out)
                    it+=itt+1
                    break
                elif c == bnd_out:
                    break
                elif c in BREAKS  or c in CHILDREN_BOUNDARY_IN or c in CHILDREN_BOUNDARY_OUT :
                    break
            it+=1
        elif c in OPERATORS:
            it+=1
        else:
            break
    label = i[start:it]
    print(label)      
    return hint, prefix ,label, it+ (1 if limit is not None else 0)

        
        
BREAKS = [' ']

WALK = ['.']

OPERATORS = ['=','<','>','!','~']


NAME_BOUNDARY_IN = ['"','{', "'"]

NAME_BOUNDARY_OUT = ['"','}',"'"]

CHILDREN_BOUNDARY_IN = ['(']

CHILDREN_BOUNDARY_OUT = [')']



def lexer(i):
    # remove the space
    return get_children(i,None)[0]



def get_children(i,bnd_out):
    it = 0
    l = len(i)
    first = types.SimpleNamespace()
    first.start = 0
    term=first
    # process all 
    while it < l:
        while (i[it] == ' ' or i[it] == '\n'):
            it+=1
            if it >= l: break
        if it >= l: break
        [term.hint, term.pefix, term.label, itt ] = get_name(i[it:],bnd_out)
        it+= itt
        if it >= l: break
        while (i[it] == ' ' or i[it] == '\n')  and it < l :
            it+=1
            if it >= l: break
        if it < l:
            if i[it] in CHILDREN_BOUNDARY_IN:
                term.bnd_idx = CHILDREN_BOUNDARY_IN.index(i[it])
                bnd_out_ch = CHILDREN_BOUNDARY_OUT[term.bnd_idx]
                print('group start')
                # star
                [term.children,itt] = get_children(i[it+1:],bnd_out_ch)
                it+=itt+1
                if it >= l: break
            
            if  i[it] == bnd_out:
                return first, min(l,it+1)
            
            if len(term.label.replace(' ',''))>0:
                term.next = types.SimpleNamespace()
                term = term.next
#                it+=1
    return first, min(l,it+1)

 
def print_term(term):
    op = term.operator if hasattr(term,'operator')  else ''
    prefix = term.prefix + "." if hasattr(term,'prefix')  else ''
    label = term.label if hasattr(term,'label') else ''
    group_term = print_term(term.children) if hasattr(term,'children') and term.children is not None  else ''
    group = "(" + group_term + ")" if group_term != '' else ''
    next = print_term(term.next) if hasattr(term,'next') else ''
    return ("{}{}{}{} {}".format(op,prefix,label,group,next))
   

print("LEXER")
terms = lexer(teststr)
print(print_term(terms))



    
    
    