import sys, re, math, random, argparse, os, time
from collections import deque
from pathlib import Path
from decimal import Decimal as dec
from utils import *
from parser import *

#function for getting initial solution
def get_initial_sol():
    block_list = list(block_dict.keys()) #list of all blocks names
    temp = [] #output list along with added vertical and hortizontal cuts to block_list
    i = 0
    j = 0
    l = len(block_list) #number of blocks in the layout
    #gets a polish expression representation which contains horizonatal and vertical cuts alternatively in each lveel of tree
    while(i<l): 
        temp.append(block_list[i])
        i = i + 1
        if i != l:
            temp.append(block_list[i])
            i = i + 1
            temp.append('-')
            j = j + 1
            if len(temp) > 3:
                temp.append('|')
    if temp[-1] != '|': #makes it valid polish expression
        temp.append('|')
    return temp

boltz_const = 1.3806E-16 
boltz_list = [] #list for plotting boltzmann probabilities
boltz_list_temp = []

#function for accepting moves with bolzmann probability
def isAccept(cost, T): #given change in cost and temperature
    if cost < 0:  #always accept if change in cost is reduced
        return True
    else:         #accept with higher probabilities at higher temperatures 
        temp = -1*cost/(T)
        boltz = math.exp(temp)
        boltz_list.append(boltz)
        boltz_list_temp.append(T)
        r = random.random()
        if r < boltz:
            return True
        else:
            return False

#this function implements simulated algorithm with starting intial solutions and N is number of blocks 
#N is number of blocks which is used to parammeterize number of moves per step
def SA_engine(initial_sol, N):
    iter = 0
    temp_list = []
    cost_list = [] #areas of all gotten layouts 
    del_cost_list = [] 
    accepted_list = []
    curSol = initial_sol #current solution is intial solution
    cost_cur_sol = get_area(initial_sol[:]) #area of inital layout
    cost_list.append(cost_cur_sol) 
    total_w = 0
    max_h = 0
    best_area = 0
    j=0
    #this computes best areas where there is no black area i.e. it just sum of areas of all blocks in the layout
    for i in block_objs.values():
        total_w = total_w+i.width_height[0][0]
        max_h = max(max_h,i.width_height[0][1])
        best_area = best_area+(i.width_height[0][0]*i.width_height[0][1]) #best area is sum 
        j = j+1       
    worst_area = total_w*max_h #worst is maximum of heights and sum of all widths of all blocks in layout
    worst_del_cost = worst_area-best_area #this for finding intial temperature with worst cost
    
    T0 = worst_del_cost/dec(math.log(0.999))*-1
    T0 = 10000 #we fixed initial temperature to 10000 according to our experiments
    tf = 0.1 #final temperature
    slope = dec(0.99) #slope of temperature decrease is 0.99
    T = T0  #temperature is first intialised intial temperature
    mov_per_step = int(5*(math.log(N))+40) #moves per step is a logartithmic function of number of blocks in the layout
    
    while(T>tf): #when Temprature is less than final temperature, we update costs with perturbatons to the layout
        k = 0
        for i in range(mov_per_step): #we run for number of moves per each tempearture step
            next_sol = perturb(curSol[:]) #perturb the current solution i.e current slicing tree to get another slicing tree
            cost_next_sol = get_area(next_sol[:]) #calculate cost for it
            del_cost = cost_next_sol - cost_cur_sol #change in cost for the perturbation
            del_cost_list.append(del_cost) 
            if isAccept(del_cost,T): #use isaccept function for accepting the perturbation or not
                curSol = next_sol    #upadte current solution to nect slution if the perurbation is accepted
                cost_cur_sol = cost_next_sol #likewise upadte cost of curent current solutions
                k = k + 1
        cost_list.append(cost_cur_sol)  
        T = slope*T #change temperature step 
        temp_list.append(T) #stores all temperature steps
        accepted_list.append(k) #stores all accepted moves list
        iter = iter+1
    
    return curSol #return the final solution of simulated aanealing

#this function does swapping any random two different operands in the slicing tree 
def move1(slice_tree):
    idx1 = random.randint(0,len(slice_tree)-1)
    while (slice_tree[idx1] in cuts):
        idx1 = random.randint(0,len(slice_tree)-1)
    idx2 = random.randint(0,len(slice_tree)-1)
    while (slice_tree[idx2] in cuts or abs(idx1-idx2)<=1):
        idx2 = random.randint(0,len(slice_tree)-1)
    slice_tree[idx1],slice_tree[idx2] = slice_tree[idx2],slice_tree[idx1]
    return slice_tree

#this function does OP2 in wong-liu's i.e reversing type of all the cuts betwen two random different operands
def move2(slice_tree):
    idx1 = random.randint(0,len(slice_tree)-1)
    while (slice_tree[idx1] in cuts):
        idx1 = random.randint(0,len(slice_tree)-1)
    idx2 = random.randint(0,len(slice_tree)-1)
    while (slice_tree[idx2] in cuts or idx2==idx1):
        idx2 = random.randint(0,len(slice_tree)-1)
    for i in range(idx1,idx2):
        if (slice_tree[i] == '|'):
            slice_tree[i] = '-'
        elif (slice_tree[i] == '-'):
            slice_tree[i] = '|'
    return slice_tree

#this function does swap one operator and operand as per OP3 in wong-liu 's algorithm
def move3(slice_tree):
    flag = 1
    while(flag):
        idx1 = random.randint(3,len(slice_tree)-1)
        if (slice_tree[idx1] in cuts):
            continue
        if (slice_tree[idx1-1] in cuts and slice_tree[idx1-1]!=slice_tree[idx1+1]):
            slice_tree[idx1],slice_tree[idx1-1] = slice_tree[idx1-1],slice_tree[idx1]
            flag = 0
        elif (slice_tree[idx1+1] in cuts and slice_tree[idx1-1]!=slice_tree[idx1+1]):
            slice_tree[idx1],slice_tree[idx1+1] = slice_tree[idx1+1],slice_tree[idx1]
            flag = 0
    return slice_tree

#this function randomaly choose one of three move functions defined above to perurb the slicing tree
def perturb(slice_tree):
    choose_move = random.randint(0,2)
    switch_moves = {0: move1, 1: move2, 2: move3}
    return switch_moves.get(choose_move)(slice_tree[:])
