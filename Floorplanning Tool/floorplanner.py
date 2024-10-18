import sys, re, math, random, argparse, os
from collections import deque
from pathlib import Path
from decimal import Decimal as dec
from utils import *
from parser import *
from simulated_annealing import *

def main():
    parser = argparse.ArgumentParser(description='Script to parse blocks text')
    #checks for argument input and output files in the command line
    parser.add_argument('-input', help='Path to the input block text file') 
    parser.add_argument('-output', help='Path to the output block text file')
    args = parser.parse_args()
    
    #checks for error in input file options
    if not args.input:
        print("Error: Need input file")
        exit()

    #checks for error in output file options
    if not args.output:
        print("Error: Need output file")
        exit()
    input_file_path = Path(args.input) #get path to input file
    output_file_path = Path(args.output) #get path to output file

    if not input_file_path.exists():
        print("Given input file ",input_file_path," doesn't exist")
        exit()
    block_txt_parser(input_file_path) #parse the input text file and store into data structures
    
    initial_sol = get_initial_sol()    #Get an initial soln for the given bench file
    final_sol = SA_engine(initial_sol[:],len(block_objs.keys()))    #Run SA on chosen bench file
    ta = tree_to_fp(final_sol)   #Converting final slicing tree into coordinates 
    tba = 0 
    for b in block_objs.values():
        tba = tba+b.area
    black_area = ta-tba     #Calculating the total black area

    filename = os.path.abspath(output_file_path)
    if not os.path.exists(os.path.dirname(filename)):
        print("VG WARN: Given out dir doesnt exist")
        filename = os.path.basename(output_file_path)
    print_output(final_sol,filename,ta,black_area)    #Writing into the output file

if __name__ == main():
    main()
