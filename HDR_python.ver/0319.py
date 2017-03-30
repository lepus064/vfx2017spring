import cv2
import numpy as np
import math

img_fn = []
for i in range(1,14,1):
	img_fn.append("img" +str(i).zfill(2)+ ".jpg")
img_total = [cv2.imread(fn,cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH) for fn in img_fn]
Z = np.zeros((3,len(img_total),36))
#Z = [[[] for j in range(0,len(img_total),1)] for i in range(0,3) ] 

iDis = len(img_total[0]) / 6
jDis = len(img_total[0][0]) / 6

for bgr in range(0,3):
	for p in range(0,len(img_total)):
		znindex = 0;
		for i in range(0,len(img_total[0])):
			for j in range(0,len(img_total[0][0])):
				if( (i % iDis == 0) and (j % jDis == 0) and (i*j != 0) ):
					Z[bgr][p][znindex] = img_total[p][i][j][bgr]
					znindex = znindex+1
				else:
					continue
print('initialize Z')

B = np.array([math.log(13),math.log(10),
	math.log(4),math.log(3),math.log(1),math.log(0.5),
	math.log(0.33),math.log(0.25),math.log(0.0167),
	math.log(0.0125),math.log(0.003125),math.log(0.0025),math.log(0.0001)], dtype=np.float32)
print('B done')

l = 1
z_min = 0
z_max = 255
z_mid = (z_min+z_max)/2
w = [0 for i in range(z_min,z_max+1,1)]
for i in range(z_min,z_max+1,1):
	if(i <= z_mid): w[i] = i - z_min
	else:w[i] = z_max - i
	w[i] +=1
print('w done')
n = 256
N = len(Z[0][0])  #i
P = len(Z[0])	  #j
A = [[[0 for j in range(0, n+len(Z[0][0]))] for i in range(0,len(Z[0][0])*len(Z[0])+n)] for bgr in range(0,3)]
b = [[0 for i in range(0, len(A[0]))] for bgr in range(0,3)]

print('start Filling A and b')
print(len(A[0]) )


for bgr in range(0,3):
	k = 0
	for i in range(0,len(Z[0][0])):
		for j in range(0,len(Z[0])):
			wij = w[Z[bgr][j][i].astype(np.int64)]
			A[bgr][k][Z[bgr][j][i].astype(np.int64)] = wij
			A[bgr][k][n+i] = -wij
			b[bgr][k] = wij * B[j]
			k = k+1

A[0][k][127] = 1
A[1][k][127] = 1
A[2][k][127] = 1
k =k+1;

print('1st stage finish')
kk = k
try:
	for bgr in range(0,3):
		k = kk
		for i in range(z_min+1,z_max):
			A[bgr][k][i] = l * w[i+1]
			A[bgr][k][i+1] = -2*l*w[i+1]
			A[bgr][k][i+2] = l * w[i+1]
			k = k+1
except IndexError:
    print "Oops!  That was no valid number.  Try again..."

print('2nd stage finish')
print('start calculating x')
x = []
for bgr in range(0,3):
	Anp = np.matrix(A[bgr])
	bnp = np.matrix(b[bgr])
	temp, _, _, _ = np.linalg.lstsq(Anp,bnp.getT())
	x.append(temp)

	

g = [[x[bgr][i] for i in range(z_min,z_max+1)] for bgr in range(0,3)]

lE = [[x[bgr][i] for i in range(z_max+1,len(x[0]))] for bgr in range(0,3)]

#E = [ [ [0 for bgr in range(0,3)] for j in range(0,len(img_total[0][0]))]for i in range(0,len(img_total[0]))] 
E = np.zeros( (len(img_total[0]),len(img_total[0][0]),3) ,dtype=np.float32)

#z[bgr][p][n]
#img_total[p][i][j][bgr]

for i in range(0,len(img_total[0]) ):
	for j in range(0, len(img_total[0][0]) ):
		for bgr in range(0,3):
			temp1 = 0.0
			temp2 = 0.0
			for p in range(0,len(img_total) ):
				temp1 = temp1 + w[img_total[p][i][j][bgr]] * (g[bgr][img_total[p][i][j][bgr]] - B[p])
				temp2 = temp2 + w[img_total[p][i][j][bgr]]
			#print(temp1)
			#print(temp2)
			E[i][j][bgr] = math.exp(temp1/temp2)
	print(i)

maxxx = np.amax(E)
for i in E:
	i *= 1/maxxx


cv2.cvtColor(E,cv2.COLOR_BGR2Luv)
cv2.imwrite("0329.hdr",E)
