
# coding: utf-8

# In[7]:


import math
import random

# this methode finds the indices for all occurencys of target in data 
def findAll(data: bytes, target: int) -> list:
    result = []
    last_index = 0
    while last_index != -1:
        i = data[last_index:].find(target)
        if(i < 0):
            return result
        else:
            result += [last_index+i]
            last_index = last_index+i+1
            
# this methode finds the indices for all occurencys of a word in data 
def findKeyword(data, word):
    word_array = word.encode('ascii')
    result = []
    possible_indices = findAll(data, word_array[0])
    for p in possible_indices:
        same = True
        for i in range(1, len(word)):
            if(data[p+i] != word_array[i]):
                same = False
        if(same):
            result += [p]
    return result

def distance(a, b):
    return math.sqrt(pow(a[0]-b[0],2)+pow(a[1]-b[1],2)+pow(a[2]-b[2],2))


# In[8]:


def load(name: str) -> bytes:
    binary_file = open(name, 'rb')
    data = binary_file.read()
    binary_file.close()
    return data

def save(data: bytes, name: str):
    f = open(name, 'wb+')
    f.write(data)
    f.close()  


# In[9]:


#SIZE\0c 00 00 00 \ 00 00 00 00 \ 03 00 00 00 \ 03 00 00 00 \ 03 00 00 00 \ XYZI \54 00 00 00 \ 00 00 00 00 \ 14 00 00 00'\
# id                                 size x       size y         size z      id                                 # voxel   

# |SIZE|#bytes|#children|size x|size y|size z|XYZI|#bytes|#childeren|#voxel n|[x y z c]|...|[x y z c]|
# ^start_id                                  ^xyz_id                         ^vox_id    ^[x y z c]*n ^end_id

def toBytes(a: int) -> bytes:
    return a.to_bytes(4, byteorder="little")

# takes data in for [[a_1,a_2,...],[b_1,b_2,...],...] and turns it into a byte array (a_n,b_n,... <256)
def toBytearray(data) -> bytes:
    byte = bytearray()
    for d in data:
        for i in d:
            byte += (i).to_bytes(1, byteorder="little")
    return byte

def sizeChunk(x: int, y: int, z: int) -> bytes:
    result = bytearray()
    result.extend(map(ord, "SIZE"))
    result += toBytes(12) + toBytes(0) + toBytes(x) + toBytes(y) + toBytes(z)
    
    return result

def xyziChunk(voxel) -> bytes:
    n = len(voxel)
    result = bytearray()
    result.extend(map(ord, "XYZI"))
    result += toBytes(4+n*4) + toBytes(0) + toBytes(n) + toBytearray(voxel)
    
    return result

def maxDimensions(voxel):
    result = [0,0,0]
    for v in voxel:
        for i in range(0, len(result)):
            result[i] = max(result[i], v[i])
            
    return result

def modelDataAutoSize(voxel) -> bytes:
    result = bytearray()
    dimensions = maxDimensions(voxel)
    result += sizeChunk(dimensions[0]+1,dimensions[1]+1,dimensions[2]+1)
    result += xyziChunk(voxel)
    return result

def modelData(voxel, x: int, y: int, z: int) -> bytes:
    result = bytearray()
    result += sizeChunk(x,y,z)
    result += xyziChunk(voxel)
    return result

def packChunk(number_of_models: int):
    result = bytearray()
    result.extend(map(ord, "PACK"))
    result += toBytes(4) + toBytes(0) + toBytes(number_of_models*2)
    return result

def mainHeader(byte_size: int) -> bytes:
    result = bytearray()
    result.extend(map(ord, "VOX "))
    result += toBytes(150)
    result.extend(map(ord, "MAIN"))
    result += toBytes(0) + toBytes(byte_size) 
    return result
    


# In[10]:


def split(filename: str, num_clusters: int):
    # Read the whole file at once
    data = load(filename)
    model_ids = findKeyword(data, 'SIZE') 

    header = data[:model_ids[0]]

    model_bytes = bytearray()
    end_id=0
    voxel=[]
    
    for m_id in model_ids:
        #calculate section start ids and length
        xyz_id = m_id+24
        vox_id = xyz_id+16
        n = int.from_bytes(data[xyz_id+12:vox_id], byteorder = "little")
        end_id = vox_id + n*4

        #seperate header from voxel
        voxel += [[data[vox_id+i*4], data[vox_id+1+i*4], data[vox_id+2+i*4], data[vox_id+3+i*4]] for i in range(0, n)]

    #split
    dimensions = maxDimensions(voxel)
    centers = [[random.randrange(0,dimensions[0]),random.randrange(0,dimensions[1]),random.randrange(0,dimensions[2]),7+i] for i in range(0,num_clusters)]
    cluster = [[] for i in range(0,len(centers))]
    for v in voxel:
        center_id = 0
        col = 80
        dist = 1000000;
        min_i = 0
        for i in range(0,len(centers)):
            d = distance(centers[i][0:3],v[0:3])
            if(d<dist):
                dist = d
                min_i = i
        cluster[min_i] += [v]

    #seperate header and tail, read number of voxels n
    tail = data[end_id:]

    for i in range(0,len(cluster)):

        body = modelData(cluster[i],dimensions[0]+1, dimensions[1]+1, dimensions[2]+1)

        #calculate endresult
        result = mainHeader(len(body)) + body
        save(result, filename[:len(filename)-4] + str(i) + ".vox")
    
    print("done")


# In[17]:


import sys
if(len(sys.argv)>=3):
    split(str(sys.argv[1]), int(sys.argv[2]))
else:
    print("Arguments missing, use 'py -3.6 voxspliter.px <file name> <number of clusters>'")


# In[12]:


#import tkinter as tk
#from tkinter import filedialog
#from tkinter import simpledialog

#root = tk.Tk()

#file_path = filedialog.askopenfilename()

#USER_INP = simpledialog.askstring(title="VOX Splitter",
#                                  prompt="How many pieces do you want?:")

#split(file_path,int(USER_INP))

