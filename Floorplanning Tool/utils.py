from collections import deque
from parser import *

#This function uses the dynamic programming approach to get best possible layouts when combining two blocks
def combine_area(b1,b2,cut):
    l1 = len(b1)
    l2 = len(b2)
    i = 0
    j = 0
    out = {}
    b1_list = [list(tup) for tup in b1]  #Layouts possible for block b1
    b2_list = [list(tup) for tup in b2]  #Layouts possible for block b2
    if cut == '|':
        while(i<l1 and j<l2):
            w = b1_list[i][0] + b2_list[j][0]
            if b1_list[i][1] > b2_list[j][1]:
                h = b1_list[i][1]
                out[(w,h)] = [b1_list[i],b2_list[j]]
                i = i + 1
            else:
                h = b2_list[j][1]
                q = j
                out[(w,h)] = [b1_list[i],b2_list[j]]
                j = j + 1
    else:
        b1_list = b1_list[::-1] #Reversing the order to be in decreasing order of widths
        b2_list = b2_list[::-1]
        while(i<l1 and j<l2):
            h = b1_list[i][1] + b2_list[j][1]
            if b1_list[i][0] > b2_list[j][0]:
                w = b1_list[i][0]
                out[(w,h)] = [b1_list[i],b2_list[j]]
                i = i + 1
            else:
                w = b2_list[j][0]
                out[(w,h)] = [b1_list[i],b2_list[j]]
                j = j + 1
        out2 = {}
        rev_keys = list(out.keys())[::-1]
        for k in rev_keys:
            out2[k] = out[k]
        out = out2
    return out
#Post order traversal of the slicing tree to get best area
def get_area(slice_tree):
    stack = deque()
    for i in slice_tree:
        if i not in cuts:
            stack.append(i)
        else:
            if len(stack) < 2:
                print("VG ERROR: Invalid Polish exp")
                return None
            e1 = stack.pop()
            e2 = stack.pop()
            
            comb = e2+e1+i
            if comb not in block_dict.keys():
                tmp = combine_area(block_dict[e2],block_dict[e1],i)
                block_dict[comb] = tmp
            stack.append(comb)
    if(len(stack) > 1):
        print("VG WARN: Invalid polish exp ")
        return None
    m = stack.pop()
    final_layouts = list(block_dict[m].keys())
    min_layout = min(final_layouts, key=lambda t: t[0] * t[1])
    return min_layout[0]*min_layout[1]

#Function to choose the layout to be used among all possible layouts for each block based on final min layout 
def get_final_layouts(slice_tree):
    stack = deque()
    for i in slice_tree:
        if i not in cuts:
            stack.append(block_objs[i])
        else:
            if len(stack) < 2:
                print("VG ERROR: Invalid Polish exp")
                return None
            e1 = stack.pop()
            e2 = stack.pop()
            comb = e2.name+e1.name+i
            if comb not in block_dict.keys():
                b1 = block_dict[e1]
                b2 = block_dict[e2]
                tmp = combine_area(b2,b1,i)
                block_dict[comb] = tmp
            else:
                tmp = block_dict[comb]
            temp = macro(comb)
            temp.width_height = list(tmp.keys())
            temp.child_elements = [e2,e1]
            stack.append(temp)
    if(len(stack) > 1):
        print("VG WARN: Invalid polish exp ")
        return None
    final_element = stack.pop()
    final_layouts = final_element.width_height
    min_layout = min(final_layouts, key=lambda t: t[0] * t[1])
    tree_traversal(final_element,min_layout)
#Recursive function to update best layout based on layout table
def tree_traversal(element,layout):
    if (len(element.child_elements) == 0):
        element.final_layout = layout
    else:
        l1 = block_dict[element.name][tuple(layout)][0]
        l2 = block_dict[element.name][tuple(layout)][1]
        tree_traversal(element.child_elements[0],l1)
        tree_traversal(element.child_elements[1],l2)
#Update the actual x,y coordinates for all the blocks depending upon the final width and height
def update_coords(e2,e1,cut):
    if cut == '|':
        for b in e2.child_blocks:
            b_obj = block_objs[b]
            b_obj.llx = b_obj.llx + e1.width
            b_obj.urx = b_obj.llx + b_obj.width
    else:
        for b in e2.child_blocks:
            b_obj = block_objs[b]
            b_obj.lly = b_obj.lly + e1.height
            b_obj.ury = b_obj.lly + b_obj.height
#Main function which converts the final slicing tree into actual floorplan coordinates           
def tree_to_fp(slice_tree):
    get_final_layouts(slice_tree)
    stack = deque()
    for i in slice_tree:
        if i not in cuts:
            temp = block_objs[i]
            temp.width = temp.final_layout[0]
            temp.height = temp.final_layout[1]
            temp.area = temp.width*temp.height
            temp.urx = temp.llx + temp.width
            temp.ury = temp.lly + temp.height
            temp.child_blocks.append(temp.name)
            stack.append(temp)
        else:
            if len(stack) < 2:
                print("VG ERROR: Invalid Polish exp ")
                return None
            e1 = stack.pop()
            e2 = stack.pop()
            comb = e2.name+e1.name+i            
            update_coords(e1,e2,i)
            temp = macro(comb)
            if i == '|':
                temp.width = e1.width + e2.width
                temp.height = max(e1.height,e2.height)
                temp.area = temp.width*temp.height
            else:
                temp.height = e1.height + e2.height
                temp.width = max(e1.width,e2.width)
                temp.area = temp.width*temp.height
            temp.llx = 0
            temp.lly = 0
            temp.urx = temp.llx + temp.width
            temp.ury = temp.lly + temp.height
            temp.child_blocks.extend(e1.child_blocks)
            temp.child_blocks.extend(e2.child_blocks)
            stack.append(temp)
    if(len(stack) > 1):
        print("VG WARN: Invalid polish exp ")
        return None
    f = stack.pop()
    return f.width*f.height
#Function to write the output file
def print_output(st,out_file,tot_area,black_area):
    with open(out_file,'w') as fp:
        fp.write("Final area = "+str(round(tot_area,4))+'\n')
        fp.write("Black area = "+str(round(black_area,4))+'\n')
        for t in st:
            if t in block_objs.keys():
                b = block_objs[t]
                fp.write(b.name+' ('+str(round(b.llx,4))+','+str(round(b.lly,4))+') ('+str(round(b.urx,4))+','+str(round(b.ury,4))+')\n')
