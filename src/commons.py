'''
This file contains commonly used functions 
'''

# Functions
def check_array(array, value):
    for i in array:
        if i == value:
            return True
        
    return False

def check_dict(dict, key, value):
    for x, y in dict.items():
        if x == key:
            if y == value:
                return True
            
            
    return False