# vfx2017spring
website:https://r05521501.wixsite.com/vfx2017spring
## Project1: High Dynamic Range Imaging

### 使用相機:

Panasonic G7 + Panasonic LUMIX 14-42mm F3.5-5.6 ASPH

Nikon D750 + AF-S NIKKOR 35mm f/1.8G ED


### 使用工具:
#### c++ ver:

OpenCV 3.2.0 :http://opencv.org
easyexif:https://github.com/mayanklahiri/easyexif

#### python ver:

Ubuntu 16.04
OpenCV 3.2
OpenCV package for python 
Exifread （in order to get the exposure time of each picture)
https://pypi.python.org/pypi/ExifRead

我們寫了兩個版本

分別是C++和Python

### 使用方法:

git clone https://github.com/lepus064/vfx2017spring.git

#### c++:

cd HDR && mkdir build && cd build

cmake ..

./hdr_imaging ../../images/ce_building

如果無法compile可將CMakeLists.txt中的hdr_imaging_multi_thread.cpp

改成hdr_imaging.cpp

#### python:

cd HDR_python.ver/Resource/src
python 0319.py

