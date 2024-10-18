import argparse, re, time
from pathlib import Path

global gate_types
global inputs, outputs, node_dict, node_wid_only_ip
inputs = []    #list of primary inputs
outputs = []    #list of primary outputs
node_dict = {}    #circuit dictionary
node_wid_only_ip = []    #list of nodes which has inputs that are primary inputs
gate_types = ['NAND', 'NOR', 'AND', 'OR', 'XOR', 'NOT', 'BUFF']
global cell_objs
cell_objs = []
#Class for storing information about std cells
class node:
    def __init__(self,name):
        self.name = name    #Unique name for all instances
        self.cell_name = ""    #cell Name
        self.type = "gate"
        self.num_fanout = 0    #Number of Fanouts
        self.num_fanin = 0    #Number of Fanins
        self.inputs = []    #Links to Inputs nodes
        self.ip_str = []    #Str of input nodes
        self.outputs = []    #Links to output nodes
        self.Tau_in = []
        self.delay_values = []    #list for delay values for all inputs connected to a node
        self.slew_values = []
        self.in_arrival = []
        self.req_arrival = []
        self.min_req_arrival = 0.0     #Required arrival time
        self.slack = 0.0            #slack value
        self.max_out_arrival = 0.0     #Actual arrival time
        self.Tau_out = 0.0             #slew
        self.load_cap = 0.0             #load capacitance
    
    #Method to add the links of input nodes of a node
    def add_inputs(self,in_nodes):
        flag = 1
        for n in in_nodes:
            if n in inputs:
                self.inputs.append(n)
                self.ip_str.append(n)
            elif n in node_dict.keys():
                self.inputs.append(node_dict[n])
                self.ip_str.append(n)
                node_dict[n].outputs.append(self)
                node_dict[n].num_fanout = len(node_dict[n].outputs)
                flag = 0
            else:
                temp2 = node('NaN')    #Create a dummy node and add as parent when the input to a particular gate is not yet defined
                node_dict[n] = temp2
                self.inputs.append(node_dict[n])
                self.ip_str.append(n)
                node_dict[n].outputs.append(self)
                node_dict[n].num_fanout = len(node_dict[n].outputs)
                flag = 0
        self.num_fanin = len(self.inputs)
        if flag == 1:
            node_wid_only_ip.append(self.name.split('-')[1]) #list of nodes which has inputs that are primary inputs

#Main Netlist parser function which read the bench file and puts the data into a linked list format
def netlist_parser(fname):
    with open(fname,'r') as fp:
        for l in fp:
            if re.match("\s*#",l):
                continue
            elif (re.match("\s*INPUT\((\w+)\)",l)):
                i = re.match("\s*INPUT\((\w+)\)",l)
                inputs.append(i.group(1))    #Store input node names in a list
            elif (re.match("\s*OUTPUT\((\w+)\)",l)):
                i = re.match("\s*OUTPUT\((\w+)\)",l)    #Store output node names in a list
                outputs.append(i.group(1))
            else:
                i = re.match("\s*(\w+)\s*=\s*(\w+)\(\s*(.*)\s*\)",l)		
                if (i):
                    out_node = i.group(1)
                    gate = i.group(2)
                    in_nodes = re.split('[,\s]+', i.group(3))
                    name = gate+'-'+out_node
                    if out_node not in node_dict.keys():
                        temp = node(name)    #Create a new class object for a node if not already there
                    else:
                        temp = node_dict[out_node]    #Use exsisting class object if present
                        temp.name = name
                    temp.cell_name = gate
                    temp.add_inputs(in_nodes)
                    if out_node in outputs:
                        temp.outputs.append(out_node)
                        temp.num_fanout = len(temp.outputs)
                    node_dict[out_node] = temp

#For each standard cell in the library file, create a data structure which has the name, capacitance, delay and slew index1 and index2 along with lookup tables for slew and delay
class std_cell:
    def __init__(self,name):
        self.name = name                     #name of the standard cell
        self.cap = 0                         #capacitance of standard cell
        
        #index 1 and 2 of delay
        self.delay_idx1 = [] 
        self.delay_idx2 = []
        
        #index 1 and 2 of slew
        self.slew_idx1 = [] 
        self.slew_idx2 = []
        self.delay_lut = []             #delay array
        self.slew_lut = []              #slew array

#function for parsing the library file 'sample_NLDM.lib' into data structure std_cell for each standard cell in the file
def lib_parser(fname):                             #fname is file name
                             
    cell_pattern = r'cell \((\w+)\) {' #pattern for searching cell ({gatename}_X1) 
    #cell_objs = []                       #this contains list of all standard cells which are stored as class std_cell and it can be accessed by all
    cell_flag = 0                             #flag for encountering a cell
    cell_delay_flag = 0                         #flag for encoutering cell_delay inside cell
    delay_lut_flag_1 = 0                         #flag for encounter values inside cell_delay
    cell_slew_flag = 0                             #flag for encoutering output_slew inside cell
    slew_lut_flag = 0                             #flag for encountering values inside output_slew
    
    with open(fname, 'r') as library_file:
        for line in library_file :
            cell_match = re.search(cell_pattern, line) 
            if cell_match:
                cell = str(cell_match.group(1))             #getting the standard cell name
                temp = std_cell(cell)                         #initiating a temporary class for the encountered standard cell by removing last three i.e _X1
                cell_objs.append(temp) 
                cell_flag = 1 
            elif cell_flag == 1:                                 #going inside that standard cell to its attributes
                if(re.match("\s*capacitance",line)):
                    temp.cap = float(re.search("\s*capacitance\s*:\s*(\d+\.\d+);",line).group(1)) 
                elif(re.match("\s*cell_delay",line)):                 #going into cell_delay
                    cell_delay_flag =1
                elif(cell_delay_flag == 1):
                    if (re.search("\s*index_1\s*\(\"(.*)\"\);",line)):             #searching for cell_delay index1
                        indx = re.search("\s*index_1\s*\(\"(.*)\"\);",line)
                        temp.delay_idx1 = [float(x) for x in indx.group(1).split(',')]
                    elif (re.search("\s*index_2\s*\(\"(.*)\"\);",line)):             #searching for cell_delay index2
                        indx = re.search("\s*index_2\s*\(\"(.*)\"\);",line)
                        temp.delay_idx2 = [float(x) for x in indx.group(1).split(',')]
                    elif(re.search("\s*values\s*\(\"(.*)\"\,\s*", line)):              #searching for cell_delay values
                        indx = re.search("\s*values\s*\(\"(.*)\"\,\s*", line)
                        delay_lut_flag_1 =1
                        temp.delay_lut.append([float(x) for x in indx.group(1).split(',')])
                    elif(delay_lut_flag_1 ==1):                                         #going into cell_delay values array
                            if (re.search("\s*\"(.*)\"\);", line)):                     # searching for last line in cell_delay values
                                indx = re.search("\s*\"(.*)\"\);", line)
                                temp.delay_lut.append([float(x) for x in indx.group(1).split(',')])
                                delay_lut_flag_1 = 0
                                cell_delay_flag = 0
                            elif(re.search("\s*\"(.*)\"\,\s*", line)): 
                                indx = re.search("\s*\"(.*)\"\,\s*", line)
                                temp.delay_lut.append([float(x) for x in indx.group(1).split(',')])
                elif(re.match("\s*output_slew",line)):                                 #going into output_slew
                    cell_slew_flag = 1
                elif(cell_slew_flag == 1):
                    if (re.search("\s*index_1\s*\(\"(.*)\"\);",line)):                 #searching slew index1
                        indx = re.search("\s*index_1\s*\(\"(.*)\"\);",line)
                        temp.slew_idx1 = [float(x) for x in indx.group(1).split(',')] 
                    elif (re.search("\s*index_2\s*\(\"(.*)\"\);",line)):                 #searching slew index2
                        indx = re.search("\s*index_2\s*\(\"(.*)\"\);",line)
                        temp.slew_idx2 = [float(x) for x in indx.group(1).split(',')]
                    elif(re.search("\s*values\s*\(\"(.*)\"\,\s*", line)):                 #searching slew values
                        indx = re.search("\s*values\s*\(\"(.*)\"\,\s*", line)
                        slew_lut_flag =1
                        temp.slew_lut.append([float(x) for x in indx.group(1).split(',')])
                    elif(slew_lut_flag ==1):                                                 #going into slew values array
                            if (re.search("\s*\"(.*)\"\);", line)):                             #searching for last line in cell_delay values
                                indx = re.search("\s*\"(.*)\"\);", line)
                                temp.slew_lut.append([float(x) for x in indx.group(1).split(',')])
                                slew_lut_flag = 0
                                cell_slew_flag = 0
                                cell_flag = 0
                            elif(re.search("\s*\"(.*)\"\,\s*", line)):
                                indx = re.search("\s*\"(.*)\"\,\s*", line)
                                temp.slew_lut.append([float(x) for x in indx.group(1).split(',')])

#Function to print the netlist data in reqired format
def write_netlist_data(file_path):
    fp= open(file_path, 'w')
    fp.write(str(len(inputs))+ " Primary inputs"+'\n')
    fp.write(str(len(outputs))+" Primary outputs"+'\n')
    gate_count = {}
    for k,v in node_dict.items():
        if v.cell_name not in gate_count.keys():
            gate_count[v.cell_name] = 1
        else:
            gate_count[v.cell_name] += 1
    for k,v in gate_count.items():
        fp.write(str(v)+" "+str(k)+" gates"+'\n')
    fp.write('\n')
    fp.write("Fanout..."+'\n')
    for k,v in node_dict.items():
        fo = v.outputs
        fo_lst = ["OUTPUT-" + str(i) if i in outputs else i.name for i in fo]
        fp.write(str(v.name)+': '+ ', '.join(fo_lst)+"\n")
    fp.write('\n')
    fp.write("Fanin..."+'\n')
    for k,v in node_dict.items():
        fi = v.inputs
        fi_lst = ["INPUT-" + str(i) if i in inputs else i.name for i in fi]
        fp.write(str(v.name)+': '+', '.join(fi_lst)+'\n')

#Create LUT text files for slew and delay
def write_lib_data(type):
    if type == 'delay':
        with open(type+'_LUT.txt','w') as fp:
            for c in cell_objs:
                fp.write('\nCell: '+c.name+'\n')
                fp.write('Input Slews(ns): '+','.join([str(x) for x in c.delay_idx1])+'\n')
                fp.write('Load Caps(fF): '+','.join([str(x) for x in c.delay_idx2])+'\n\n')
                fp.write('Delays(ns) :\n')
                for t in c.delay_lut:
                    fp.write(','.join([str(x) for x in t])+';\n')
    elif type == 'slew':
        with open(type+'_LUT.txt','w') as fp:
            for c in cell_objs:
                fp.write('\nCell: '+c.name+'\n')
                fp.write('Input Slews(ns): '+','.join([str(x) for x in c.slew_idx1])+'\n')
                fp.write('Load Caps(fF): '+','.join([str(x) for x in c.slew_idx2])+'\n\n')
                fp.write('Slews(ns):\n')
                for t in c.slew_lut:
                    fp.write(','.join([str(x) for x in t])+';\n')
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
        file_path = Path(args.read_ckt)
        if not file_path.exists():
            print(f"Given Bench file {file_path} doesn't exist")
            exit()
        else:
            netlist_parser(file_path)
            write_netlist_data(f'ckt_details_{file_path.name[:-5]}txt')
    if read_nldm_flag:
        file_path = Path(args.read_nldm)
        if not file_path.exists():
            print(f"Given NLDM file {file_path} doesn't exist")
            exit()
        else:
            lib_parser(file_path)
            if args.delays and args.slews:
                write_lib_data('delay')
                write_lib_data('slew')
            elif args.delays:
                write_lib_data('delay')
            elif args.slews:
                write_lib_data('slew')
            else:
                write_lib_data('delay')
                write_lib_data('slew')
if __name__ == "__main__":
    main()
