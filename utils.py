import numpy as np
from numpy.linalg import inv
import cv2
from cv2 import cv as cv

__author__ = 'hunter'


ply_header = '''ply
format ascii 1.0
element vertex %(vert_num)d
property float x
property float y
property float z
property uchar red
property uchar green
property uchar blue
end_header
'''

def write_ply(fn, verts, colors):
    verts = verts.reshape(-1, 3)
    colors = colors.reshape(-1, 3)
    verts = np.hstack([verts, colors])
    with open(fn, 'w') as f:
        f.write(ply_header % dict(vert_num=len(verts)))
        np.savetxt(f, verts, '%f %f %f %d %d %d')


def get_rot_trans_matrix_img2_wrt_img1(dataset_calibration_info, n_img_left, n_img_right):
    r1 = np.array(dataset_calibration_info[n_img_left - 1][0:9]).reshape(3, 3)
    r2 = np.array(dataset_calibration_info[n_img_right - 1][0:9]).reshape(3, 3)

    # rotation of second image from first one
    r = np.dot(r2, inv(r1))

    t1 = np.array(dataset_calibration_info[n_img_left - 1][9:12]).reshape(3, 1)
    t2 = np.array(dataset_calibration_info[n_img_right - 1][9:12]).reshape(3, 1)

    # translation of second image from the first one
    t = t1 - np.dot(inv(r), t2)

    return r, t


def get_disparity(imgLeft, imgRight, method="BM"):
    gray_left = cv2.cvtColor(imgLeft, cv.CV_BGR2GRAY)
    gray_right = cv2.cvtColor(imgRight, cv.CV_BGR2GRAY)
    print gray_left.shape
    c, r = gray_left.shape
    if method == "BM":
        sbm = cv.CreateStereoBMState()
        disparity = cv.CreateMat(c, r, cv.CV_32F)
        sbm.SADWindowSize = 5
        sbm.preFilterType = 1
        sbm.preFilterSize = 5
        sbm.preFilterCap = 30
        sbm.minDisparity = 0
        sbm.numberOfDisparities = 16
        sbm.textureThreshold = 0
        sbm.uniquenessRatio = 0
        sbm.speckleRange = 2
        sbm.speckleWindowSize = 50

        gray_left = cv.fromarray(gray_left)
        gray_right = cv.fromarray(gray_right)

        cv.FindStereoCorrespondenceBM(gray_left, gray_right, disparity, sbm)
        disparity_visual = cv.CreateMat(c, r, cv.CV_8U)
        cv.Normalize(disparity, disparity_visual, 0, 255, cv.CV_MINMAX)
        disparity_visual = np.array(disparity_visual)

    elif method == "SGBM":
        sbm = cv2.StereoSGBM()
        sbm.SADWindowSize = 5  # Matched block size. It must be an odd number >=1 . Normally, it should be somewhere in the 3..11 range.
        sbm.numberOfDisparities = 112  # con valori piu alti tipo 112 viene il contorno nero
        sbm.preFilterCap = 60
        sbm.minDisparity = 1  # con altri valori smongola
        sbm.uniquenessRatio = 11
        sbm.speckleWindowSize = 0
        sbm.speckleRange = 0
        sbm.disp12MaxDiff = 1
        sbm.fullDP = False  # a True runna il full-scale two-pass dynamic programming algorithm

        disparity = sbm.compute(gray_left, gray_right)
        disparity_visual = cv2.normalize(disparity, alpha=0, beta=255, norm_type=cv2.cv.CV_MINMAX, dtype=cv2.cv.CV_8U)

    return disparity_visual


def rotate_img(img, angle):
    rows, cols, _ = img.shape
    M = cv2.getRotationMatrix2D((cols/2, rows/2), angle, 1)
    return cv2.warpAffine(img, M, (cols, rows))
