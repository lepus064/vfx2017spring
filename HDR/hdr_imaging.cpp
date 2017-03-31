#include <opencv2/photo.hpp>
#include "opencv2/imgcodecs.hpp"
#include "opencv2/core.hpp"
#include <opencv2/highgui.hpp>
#include "opencv2/core/matx.hpp"
#include "exif.h"
#include <dirent.h>

#include <algorithm>
#include <cmath>
#include <ctime>
#include <fstream>
#include <iostream>
#include <iterator>
#include <random>
#include <stdio.h>
#include <vector>
#include <thread>

using namespace cv;
using namespace std;

void loadExposureSeq(string, vector<Mat>&, vector<double>&);
void loadExposureSeq(string, string, vector<Mat>&, vector<double>&);
double weight(int z);
int get_img_in_dir(string dir, vector<string> &files);
void get_time_stamp(string dir, vector<string> files, vector<double> &timestamp);
void get_color_E(int color,const int &n, const double &l, const vector<Point> &pts, const vector<double> &times, const vector<Mat> &images, Mat &HDR);

int main(int argc, char**argv){

    if(argc < 2){
        cout << "Usage: ./hdr_imaging <Path>" << endl;
        cout << "or" << endl;
        cout << "Usage: ./hdr_imaging <Path> list" << endl;
        return 0;
    }


    // Some parameters
    vector<Mat> images; // Example 1024*768
    vector<double> times;
    vector<string> names;
    vector<Point> pts;

    if(argc == 2){
        loadExposureSeq(argv[1], images, times);
    }
    else{
        loadExposureSeq(argv[1], argv[2], images, times);
    }

    get_img_in_dir(argv[1], names);

    if(images.size() != times.size()){
        cout << "number of images and time is not equal" << endl;
        return 0;
    }

    const int p = images.size();
    const int n = 60;
    const double l = 0.5;
    const int img_rows = images[0].rows; //768
    const int img_cols = images[0].cols; //1024

    srand(time(0));
    
    while(pts.size() < n){
        int x = (rand()%(img_cols-1))+1;
        int y = (rand()%(img_rows-1))+1;
        if(y > img_rows*0.8 && x < img_cols*0.5)
            continue;
        Point temp_pt(x,y);
        bool uni = true;
        if(pts.size() > 0){
            for(const auto &i:pts){
                if(i == temp_pt)
                    uni = false;
            }
        }
        if(uni)
            pts.push_back(temp_pt);
    }

    /* Show picked points */

    // int pick_one = images.size()/2;
    // Mat PickedPointImg;
    // images[pick_one].copyTo(PickedPointImg);
    // for(const auto &i:pts){
    //     circle(PickedPointImg,i,3,Scalar(0,0,255),-1);
    // }
    // resize(PickedPointImg, PickedPointImg, Size(), 0.4, 0.4);
    // imshow("All Picked Points",PickedPointImg);
    // waitKey(5000); 

    /* Result image */
    Mat HDR = Mat(Size(img_cols,img_rows),CV_32FC3);

    /* Three Threads for BGR */
    thread blue(get_color_E, 0, n, cref(l), cref(pts), cref(times), cref(images), ref(HDR));
    thread green(get_color_E, 1, n, cref(l), cref(pts), cref(times), cref(images), ref(HDR));
    thread red(get_color_E, 2, n, cref(l), cref(pts), cref(times), cref(images), ref(HDR));

    blue.join();
    green.join();
    red.join();
    
    cout << "Done!!" << endl;
    Mat reslut;
    imwrite("out.hdr",HDR);
    // imshow("img",HDR);
    // waitKey(5000);

    return 0;
}


void loadExposureSeq(string path, vector<Mat>& images, vector<double>& times){
    // path = path + std::string("/");
    vector<string> temp_name;
    get_img_in_dir(path,temp_name);
    get_time_stamp(path,temp_name,times);
    for(const auto &i:temp_name){
        Mat img = imread(path + "/" + i);
        images.push_back(img);
    }

}

void loadExposureSeq(string path, string list, vector<Mat>& images, vector<double>& times){
    path = path + std::string("/");
    ifstream list_file((list).c_str());
    string name;
    float val;
    while(list_file >> name >> val) {
        Mat img = imread(path + name);
        images.push_back(img);
        times.push_back(val);
    }
    list_file.close();
}

double weight(int z){
    return z > 127 ? ((256-z)*1.0/128) : ((z+1)*1.0/128);
}

int get_img_in_dir(string dir, vector<string> &files){
    DIR *dp;
    struct dirent *dirp;
    if((dp = opendir(dir.c_str())) == NULL){
        cout << "Error" << endl;
        return 1;
    }
    while((dirp = readdir(dp)) != NULL){
        string jpg = string(dirp->d_name);
        if(jpg.find(".jpg") == jpg.size()-4||jpg.find(".JPG") == jpg.size()-4)
        files.push_back(string(dirp->d_name));
    }
    closedir(dp);
    return 0;
}

void get_time_stamp(string dir, vector<string> files, vector<double> &timestamp){
    // Read the JPEG file into a buffer
    timestamp.clear();
    
    for(auto ii:files){
        string temp = dir+"/"+ii;
        const char* tp = temp.c_str();
        FILE *fp = std::fopen(tp, "rb");
        if (!fp) {
            printf("Can't open file.\n");
        }
        fseek(fp, 0, SEEK_END);
        unsigned long fsize = ftell(fp);
        rewind(fp);
        unsigned char *buf = new unsigned char[fsize];
        if (fread(buf, 1, fsize, fp) != fsize) {
            printf("Can't read file.\n");
            delete[] buf;
        }
        fclose(fp);

        // Parse EXIF
        easyexif::EXIFInfo result;
        int code = result.parseFrom(buf, fsize);
        delete[] buf;
        if (code) {
            printf("Error parsing EXIF: code %d\n", code);
        }
        timestamp.push_back(result.ExposureTime);
    }
    

}

void get_color_E(int color,const int &n, const double &l, const vector<Point> &pts, const vector<double> &times,const vector<Mat> &images, Mat &HDR){

    int k = 0;
    const int p = images.size();
    Mat A = Mat::zeros(n*p+255, 256+n, CV_32F);
    Mat b = Mat::zeros(n*p+255, 1, CV_32F);
    Mat x = Mat::zeros(256+n, 1, CV_32F);

    const int img_rows = images[0].rows; //768
    const int img_cols = images[0].cols; //1024
    
    for(int i = 0 ; i < n; i++){
        for(int j = 0 ; j < p ; j++){
            int Zij = images[j].at<Vec3b>(pts[i])[color];//B
            A.at<float>(k,Zij) = weight(Zij);
            A.at<float>(k,256+i) = -weight(Zij);
            b.at<float>(k,0) = weight(Zij)*log(times[j]);
            k++;
        }
    }

    A.at<float>(k++,128) = 1;

    for(int i = 0 ; i < 254; i++){
        A.at<float>(k,i) = l*weight(i+1);
        A.at<float>(k,i+1) = -2*l*weight(i+1);
        A.at<float>(k,i+2) = l*weight(i+1);
        k++;
    }
    
    solve(A,b,x,DECOMP_SVD);

    vector<double> g;
    vector<double> lE;

    for(int i = 0 ; i < x.rows; i++){
        if(i < 256){
            g.push_back(x.at<float>(i,0));
        }
        else{
            lE.push_back(x.at<float>(i,0));
        }
    }

    /* Using Pointer */
    auto iter = HDR.ptr<float>();
    iter += color;
    for(int j = 0 ; j < img_rows ; j++){
        for(int i = 0 ; i < img_cols; i++){
            double value = 0;
            double total_w = 0;
            for(int P = 0;P < times.size(); P++){
                int C = images[P].at<Vec3b>(j,i)[color];
                value += (weight(C)*(g[C] - log(times[P])));
                total_w += weight(C);
            }
            value /= total_w;
            iter[0] = exp(value);
            iter+=3;
        }
    }
}