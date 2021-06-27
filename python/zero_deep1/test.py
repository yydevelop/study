import math

x1,y1=map(int, input().split())  #複数数値入力　「A B」みたいなスペース空いた入力のとき
x2,y2=map(int, input().split())  #複数数値入力　「A B」みたいなスペース空いた入力のとき
x3,y3=map(int, input().split())  #複数数値入力　「A B」みたいなスペース空いた入力のとき
x1_x2 = math.sqrt((x2-x1)**2 + (y2-y1)**2)
print(x1_x2)