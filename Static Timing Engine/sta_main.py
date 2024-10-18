from sta_parser import *
import argparse, re, time 
from pathlib import Path

def find_index_val(arr_list, val):        #given a value, this function returns the indices of two elements in the given array where the value is between them
    for i in range(len(arr_list) - 1):
        if arr_list[i] <= val <= arr_list[i + 1]:
            return i, i + 1

def interpolation_2D(cap, slew, num_fanin, gate_type):            #interpolation function of slew and cap
    
    n = gate_types.index(gate_type)                #getting the index from pre-defined list of satndard cells to access cell_objs's dictionary

    #case for both cap and slew are exactly matching to one of values in the delay_idx2 and delay_idx1 array
    if cap in cell_objs[n].delay_idx2 and slew in cell_objs[n].delay_idx1: 
        C_indx = cell_objs[n].delay_idx2.index(cap)
        tau_indx = cell_objs[n].delay_idx1.index(slew)
        delay_value = cell_objs[n].delay_lut[tau_indx][C_indx]
        slew_value = cell_objs[n].slew_lut[tau_indx][C_indx]
    else:
        if cap >= max(cell_objs[n].delay_idx2):            #case for cap is greater than maximum in cap array
            C1_indx = len(cell_objs[n].delay_idx2) - 2
            C2_indx = len(cell_objs[n].delay_idx2) - 1
        elif cap <= min(cell_objs[n].delay_idx2):        #case for cap is less than minimum in cap array
            C1_indx = 0
            C2_indx = 1
        else:                                            #case for cap within the cap array 
             C1_indx, C2_indx = find_index_val(cell_objs[n].delay_idx2, cap)
            
        if slew >= max(cell_objs[n].delay_idx1):        #case for slew is greater than maximum in slew array
            tau1_indx = len(cell_objs[n].delay_idx1) - 2
            tau2_indx = len(cell_objs[n].delay_idx1) - 1
        elif slew <= min(cell_objs[n].delay_idx1):        #case for slew is less than minimum in slew array
            tau1_indx = 0
            tau2_indx = 1
        else:                                            #case for slew within the slew array 
             tau1_indx, tau2_indx = find_index_val(cell_objs[n].delay_idx1, slew)

        #all values required for interpolation
        C1 = cell_objs[n].delay_idx2[C1_indx]
        C2 = cell_objs[n].delay_idx2[C2_indx]
        tau1 = cell_objs[n].delay_idx1[tau1_indx]
        tau2 = cell_objs[n].delay_idx1[tau2_indx]
        
        #interpolation formula for delay and slew
        delay_value = (cell_objs[n].delay_lut[tau1_indx][C1_indx] * (C2 - cap) * (tau2 - slew) + cell_objs[n].delay_lut[tau1_indx][C2_indx] * (cap - C1) * (tau2 - slew) + cell_objs[n].delay_lut[tau2_indx][C1_indx] * (C2 - cap) * (slew - tau1) + cell_objs[n].delay_lut[tau2_indx][C2_indx] * (cap - C1) * (slew - tau1)) / ((C2- C1) * (tau2 - tau1))
        slew_value =  (cell_objs[n].slew_lut[tau1_indx][C1_indx] * (C2 - cap) * (tau2 - slew) + cell_objs[n].slew_lut[tau1_indx][C2_indx] * (cap - C1) * (tau2 - slew) + cell_objs[n].slew_lut[tau2_indx][C1_indx] * (C2 - cap) * (slew - tau1) + cell_objs[n].slew_lut[tau2_indx][C2_indx] * (cap - C1) * (slew - tau1)) / ((C2- C1) * (tau2 - tau1))

    #Making delay non-negative and slew is greater than 2ps
    if (delay_value < 0):
        delay_value = 0
    if (slew_value < 0.002):
        slew_value = 0.002
    if (num_fanin > 2):
        delay_value = (num_fanin/2)*delay_value
        slew_value = (num_fanin/2)*slew_value
        
    return delay_value, slew_value

#function for getting argmax(ai+di) tau_di and maximum arrival time
def out_values(delay_values, slew_values, in_arrival) : 
    sum_array = [x + y for x, y in zip(delay_values, in_arrival)]                 #array which is ai+di
    a_out, max_index = max((value, index) for index, value in enumerate(sum_array))         #getting maximum value and its index in sum_array to getting max tau_out in the next line
    tau_out = slew_values[max_index]
    return a_out, tau_out

def sort_slack_inputs(max_key):                            #given a node, this function outputs the input which has minimum slack
    slack_list = {}
    for p in max_key.inputs:                    #checking whether the input of that node is a primary inputs as primary inputs slacks are stored in alist called min_req_list_inputs
        if isinstance(p, str):
            slack_list[p] = min_req_list_inputs[p]
        else:                                    #if the input of the given node is a node itself, just output its slack attribute
            slack_list[p]= p.slack
    min_key = min(slack_list, key=slack_list.get)     #sort the slack list
    return min_key

def sta(node_dict, circuit_fname):                       #function where both forward and backward travesal is done
    global precision
    precision = 5
    
    for n in node_dict.keys():        #for each node in the circuit, get output capacitance and input slew
        gate_type = node_dict[n].cell_name            #getting its standard_cell type
        node_dict[n].load_cap = 0.0    #initializing its laod cap to 0.0 first and change later 
        
        for m in node_dict[n].outputs :        #next, go to that gate's outputs
            if isinstance(m, str) :                 #if that output is a primary output
                node_dict[n].load_cap = node_dict[n].load_cap + 4 * cell_objs[5].cap         #The load capacitance (which are simply connected to the primary outputs) is equal to four times the capacitance of an inverter from the liberty file.
            elif isinstance(m,node) :                        #if that output is another gate
                num = gate_types.index(m.cell_name)                #get the type of that gate
                node_dict[n].load_cap = node_dict[n].load_cap + cell_objs[num].cap          #then add load_cap as per its type from the liberty file
        i = 0
        for p in node_dict[n].inputs :          #go to the inputs of the current gate
            if isinstance(p, str) :             #checking if its a primary input
                node_dict[n].Tau_in.append(0.002)                 #the input slew for primary input is 2 ps
                node_dict[n].in_arrival.append(0)                 #input arrival time for primary inputs is 0 s           
            elif isinstance(p, node):                            #if the inputs is a another gate
                node_dict[n].Tau_in.append(p.Tau_out)              #then, take the tau_out of that another gate as input slew of current gate
                node_dict[n].in_arrival.append(p.max_out_arrival)   #same here, take maximum arrival time of that another gate and append it to list of in_arrival

            # for each path of inputs to outputs of the current gate, do the interpolation to get slew and delay values
            delay_value, slew_value = interpolation_2D(node_dict[n].load_cap, node_dict[n].Tau_in[i], node_dict[n].num_fanin, gate_type)
            node_dict[n].delay_values.append(delay_value)
            node_dict[n].slew_values.append(slew_value)
            i = i+1  
            
        node_dict[n].max_out_arrival,node_dict[n].Tau_out = out_values(node_dict[n].delay_values, node_dict[n].slew_values, node_dict[n].in_arrival)   #get max_out_arrival and tau_out for the current gate as per out_values function.

   
    global aout_list_outputs, min_req_list_inputs             #list of arrival times of primary outputs and list of minimum required arrival times of primary inputs 
    aout_list_outputs = {}               
    min_req_list_inputs = {}

    #for all primary outputs, get the actual arrival times
    for b in outputs :
        if b not in node_dict.keys():                #case where primary output is directly connected to primary input
            aout_list_outputs[b] = 0
        else:
            aout_list_outputs[b]= node_dict[b].max_out_arrival
    max_key = max(aout_list_outputs, key=aout_list_outputs.get)
    delay_circuit = aout_list_outputs[max_key]                #The maximum among the arrival times at all the primary outputs is the circuit delay.

    #The required arrival time is 1.1 times the total circuit delay, and is the same at each primary output of the circuit.

    #back-ward traversal
    for n in list(node_dict.keys())[::-1]:            #traversing the circuit backward
        gate_type = node_dict[n].cell_name
        if n in outputs:                                            #if the node encountered is connected to primary output in its fan_out, then append 1.1*delay_circuit which is required arrival time for primary outputs
            node_dict[n].req_arrival.append(1.1*delay_circuit)  
            
        if (len(node_dict[n].req_arrival) != 0):          #once you know all the required arrivals of fan_out of that node, take minimum of that list i.e the minimum required arrival of that node             
            node_dict[n].min_req_arrival = min(node_dict[n].req_arrival)
        else:                                        #case where output of a node is floating i.e not connected to any primary output
            node_dict[n].req_arrival.append(1.1*delay_circuit)
            
        for k in node_dict[n].inputs:                   #now, go the inputs of the current gate
            if isinstance(k, node):                     #if it's an another gate, required arrival time of it is minimum required arrival time of the curent gate minus delay of the path from it to output of the current gate
                k.req_arrival.append(node_dict[n].min_req_arrival - node_dict[n].delay_values[node_dict[n].inputs.index(k)])
            else:                                        #if it's a primary input
                if k in min_req_list_inputs.keys():     #if the encoundetered inputs is already there, then take minimum of curent gate minus delay of the path from it to output of the current gate and itself
                    min_req_list_inputs[k] = min(node_dict[n].min_req_arrival - node_dict[n].delay_values[node_dict[n].inputs.index(k)],min_req_list_inputs[k]) 
                else:                                
                    min_req_list_inputs[k] = node_dict[n].min_req_arrival - node_dict[n].delay_values[node_dict[n].inputs.index(k)]

        node_dict[n].slack = node_dict[n].min_req_arrival - node_dict[n].max_out_arrival            #
        
    for ix in inputs:             #case for where primary inputs are directly connected to primary outputs or left floating
        if ix not in min_req_list_inputs.keys():
            if ix not in outputs:           
                min_req_list_inputs[ix] = 0
            else:         
                min_req_list_inputs[ix] = 1.1*delay_circuit 
            
    cr_path = []            #list to store gate names in the critical path
    cr_path.append("OUTPUT-" + str(max_key))   #start from that primary output whcih has maximum delay 
    if max_key in node_dict.keys():          #next, go that particular gate that connected to the above primary output 
        max_key = node_dict[max_key]
    while type(max_key) != str:        # update the gate i.e. max_key until you reach the primary input
        cr_path.append(str(max_key.name))
        max_key = sort_slack_inputs(max_key)
    cr_path.append("INPUT-" + str(max_key))   
    str_towrite_cr_path = ""
    for m in cr_path[::-1]:        
        str_towrite_cr_path = str_towrite_cr_path + str(m) + ","
        
    #writing the ckt_traversal_{gatename}.txt
    fp = open(str('ckt_traversal_'+ str(circuit_fname)+ 'txt'),'w') 
    fp.write("Circuit delay: "+str(round(delay_circuit*1000, precision)) + " ps" + '\n'+'\n')
    fp.write("Gate slacks:" + "\n")
    for k,v in list(min_req_list_inputs.items()):
        fp.write('INPUT-'+ str(k)+': '+str(round(v*1000, precision))+" ps"+'\n')
    for k,v in aout_list_outputs.items():
        fp.write('OUTPUT-'+ str(k)+': '+str(round((1.1*delay_circuit - v)*1000, precision))+" ps"+'\n')
    for n in node_dict.keys() :
        fp.write(node_dict[n].name + ": " +str(round(node_dict[n].slack * 1000, precision))+" ps"+'\n')
    fp.write("\n"+"Critical path: " + "\n")
    fp.write(str_towrite_cr_path[:-1])


def dict_ordering(node_dict):
    queue = []
    ordered_node_dict = {}
    queue = node_wid_only_ip
    while (len(queue) != 0):
        element = queue[0]
        queue = queue[1:]
        if element not in ordered_node_dict.keys():
            ordered_node_dict[element] = node_dict[element]
        for c in node_dict[element].outputs:
            if isinstance(c,str):
                continue
            flag = 1
            for i in c.ip_str:
                if i not in inputs and i not in ordered_node_dict.keys():
                    flag = 0
            if flag == 1:
                if isinstance(c,node):
                    if c.name.split('-')[1] not in ordered_node_dict.keys():
                        queue.append(c.name.split('-')[1])
    return ordered_node_dict

#Main Code
def main():
    st = time.time()
    parser = argparse.ArgumentParser(description='Script to parse bench and NLDM files')
    parser.add_argument('--read_ckt', help='Path to the circuit file')
    parser.add_argument('--read_nldm', help='Path to the NLDM file')
    parser.add_argument('--delays', help='To output delay data', action='store_true')
    parser.add_argument('--slews', help='To output slew data', action='store_true')
    args = parser.parse_args()

    read_ckt_flag = args.read_ckt is not None
    read_nldm_flag = args.read_nldm is not None

    if not read_ckt_flag and not read_nldm_flag:
        print("Error: Need at least one input, ckt file, or lib file")
        exit()

    if read_ckt_flag:
        ckt_file_path = Path(args.read_ckt)
        if not ckt_file_path.exists():
            print(f"Given Bench file {ckt_file_path} doesn't exist")
            exit()
        else:
            netlist_parser(ckt_file_path)
    if read_nldm_flag:
        nldm_file_path = Path(args.read_nldm)
        if not nldm_file_path.exists():
            print(f"Given NLDM file {nldm_file_path} doesn't exist")
            exit()
        else:
            lib_parser(nldm_file_path)
            
    print('Time after read netlist: ',time.time()-st)
    node_dict_ordered = dict_ordering(node_dict)                                #order the circuit
    sta(node_dict_ordered, ckt_file_path.name[:-5])                                                   #do topological traversal
    print('Run time :',time.time()-st)

if __name__ == "__main__":
    main()
