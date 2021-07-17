import numpy as np

a = np.array([[0, 1, 2, 3],
             [4, 5, 6, 7],
             [8, 9, 10, 11]])
b = np.array([[10, 11, 12, 13],
             [14, 15, 16, 17],
             [18, 19, 20, 21]])

print(np.concatenate([a, b], axis=0)) # 垂直方向に結合

'''
[[ 0  1  2  3]
 [ 4  5  6  7]
 [ 8  9 10 11]
 [10 11 12 13]
 [14 15 16 17]
 [18 19 20 21]]
'''

print(np.concatenate([a, b], axis=1)) # 水平方向に結合

'''
[[ 0  1  2  3 10 11 12 13]
 [ 4  5  6  7 14 15 16 17]
 [ 8  9 10 11 18 19 20 21]]
'''