import sys
import cv2
import numpy as np
import math
import exifread


img_fn = []
for i in range(35,66,1):
	img_fn.append("img_" +str(i).zfill(3)+ ".jpg")

B = [];

# Open image file for reading (binary mode)
for i in img_fn:
	f = open(sys.argv[1] + i, 'rb')
	tags = exifread.process_file(f, stop_tag='ExposureTime')
	strrr = tags['EXIF ExposureTime'].__str__()
	strrr = strrr.split('/')
	if(len(strrr) == 1):
		num = float(strrr[0])
	else:
		num =  float(strrr[0])/float(strrr[1]) 
	B.append(math.log( num ))
B = np.array(B,dtype=np.float32)
print('B done')


img_total = [cv2.imread(fn,cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH) for fn in img_fn]


Z = np.zeros((3,len(img_total),100))

iDis = len(img_total[0]) / 10
jDis = len(img_total[0][0]) / 10


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

E = np.zeros( (len(img_total[0]),len(img_total[0][0]),3) ,dtype=np.float32)


for i in range(0,len(img_total[0]) ):
	for j in range(0, len(img_total[0][0]) ):
		for bgr in range(0,3):
			temp1 = 0.0
			temp2 = 0.0
			for p in range(0,len(img_total) ):
				temp1 += w[img_total[p][i][j][bgr]] * (g[bgr][img_total[p][i][j][bgr]] - B[p])
				temp2 += w[img_total[p][i][j][bgr]]
			E[i][j][bgr] = math.exp(temp1/temp2)
	print(i)


maxxx = np.amax(E)
for i in E:
	i *= 1/maxxx


cv2.cvtColor(E,cv2.COLOR_BGR2Luv)
cv2.imwrite(sys.argv[2],E);
