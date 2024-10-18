import sys, re, math, random, argparse, os, time
from decimal import Decimal as dec

#block_objs is a dictionary of all blocks in the input file and each block is of type class macro
#block_dict is a dictionary of dictionaries of all possible [width, height] values of all blocks
global block_objs, block_dict, cuts 
block_objs = {}
block_dict = {}
cuts = ['|', '-']

class macro:
    def __init__(self, name):
        self.name = name  #name of the block e.g. sb0
        self.num_coords = 0 #number of coordinates for each block i.e 4
        self.bottom_left = [] #bottom  left corner coordinates x, y
        self.bottom_right = [] #bottom  left corner coordinates x, y
        self.top_left = [] #bottom  left corner coordinates x, y
        self.top_right = [] #bottom  left corner coordinates x, y
        self.width_height = [] # all rotated combinations of [width, height]
        self.final_layout = [] #optimal final width, height out of all possible combinations
        self.llx = 0  #optimal final lower left x coordinate
        self.lly = 0  #optimal final lower left y coordinate
        self.urx = 0  #optimal final upper right x coordinate
        self.ury = 0  #optimal final upper right y coordinate
        self.aspect_ratios = [] #aspect ratios for soft blocks
        self.width = 0 #optimal final width
        self.height = 0 #optimal final height 
        self.area = 0 #optimal final area of the block
        self.child_blocks = [] #contains names of its children
        self.child_elements = [] #links of sub trees
    def __str__(self):
        return "Name : {}\nWidth : {}\nHeight : {}".format(self.name,self.width,self.height)

    #given aspect ratios and area of soft blocks, it computes all possible width and height combos
    def width_height_calc(self, aspect_ratios, area):
        if (aspect_ratios[0]<1 and aspect_ratios[1]>1): #checks if aspect ration ratio of 1 can be considered or not
            aspect_ratios.append(1)
        aspect_ratios = list(set(aspect_ratios))
        for i in aspect_ratios:
            w = math.sqrt(area*i)
            h = w/i
            w = dec(w)
            h = dec(h)
            self.width_height.append([w,h])

#function to parse the input text file and populate the class data structure "macro" 
def block_txt_parser(file_path):
    hard_name_pattern = r'\s*(\w+)\s*hardrectilinear\s*(\d+)\s*\(([\d\.]+)\s*,\s*([\d\.]+)\)\s*\(([\d\.]+)\s*,\s*([\d\.]+)\)\s*\(([\d\.]+)\s*,\s*([\d\.]+)\)\s*\(([\d\.]+)\s*,\s*([\d\.]+)\)'
    soft_name_pattern = r'\s*(\w+)\s*softrectangular\s*(\d+)\s*([\d.]+)\s*([\d.]+)'
    with open(file_path, 'r') as block_txt_file:
        for line in block_txt_file:
            if re.match("\s*#",line): #checks for comments
                continue
            block_match_1 = re.search(hard_name_pattern, line) #match for hard macro
            block_match_2 = re.search(soft_name_pattern, line) #match for soft macro
            if block_match_1 : 
                block = str(block_match_1.group(1)) #block name
                temp = macro(block) #load into hard macro class
                block_objs[block] = temp #loading the block into class object macro
                temp.num_coords = int(block_match_1.group(2)) #number of coordinates which is 4
                temp.bottom_left += [dec(block_match_1.group(3)), dec(block_match_1.group(4))]  #bottomleft coordinate
                temp.top_left += [dec(block_match_1.group(5)), dec(block_match_1.group(6))]   #top left coordinate
                temp.top_right += [dec(block_match_1.group(7)), dec(block_match_1.group(8))]  #top right coordinate
                temp.bottom_right += [dec(block_match_1.group(9)), dec(block_match_1.group(10))] #bottom right coordinate
                #rotated version of width and height i.e 0 degrees and 90 degrees
                temp.width_height += [[temp.bottom_right[0] - temp.bottom_left[0],temp.top_left[1] - temp.bottom_left[1]], [temp.top_left[1] - temp.bottom_left[1],temp.bottom_right[0] - temp.bottom_left[0]]]
                temp.width_height = sorted(temp.width_height, key = lambda t : t[0]) #width, height pair are sorted with width in ascending order
                dict1 = {} #dictionary to store width and height combinations of its children
                for [w, h] in temp.width_height:
                    dict1[(w,h)]= [[w,h]] #its key is a tuple of its width and height 
                block_dict[block] = dict1 #store in adictionary
                temp.area = (temp.bottom_right[0] - temp.bottom_left[0])*(temp.top_left[1] - temp.bottom_left[1]) #area 
        
            if block_match_2:
                block = str(block_match_2.group(1)) #block name
                temp = macro(block) #load into soft macro class
                block_objs[block] = temp #loading the block into class object macro
                temp.area = float(block_match_2.group(2)) #area
                temp.aspect_ratios += [float(block_match_2.group(3)), float(block_match_2.group(4))] #aspect ratio values
                temp.width_height_calc(temp.aspect_ratios, temp.area) #gets all possible width, height combinations according to asect ratios
                temp.width_height = sorted(temp.width_height, key = lambda t : t[0]) #width, height pair are sorted with width in ascending order
                dict1 = {} #dictionary to store width and height combinations of its children
                for [w, h] in temp.width_height:
                    dict1[(w,h)]= [[w,h]] #its key is a tuple of its width and height
                block_dict[block] = dict1  #store in dictionary
                
