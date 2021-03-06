# -*- coding: utf-8 -*-
"""
Created on Tue Sep 27 14:47:17 2016

This program realizes a batch of algorithms on time series anomaly detection. 
Debugged in Anaconda with Python 2.7. 

@author: Yunsong Zhong
"""

import numpy
from sklearn import cluster
import os
import math
import logging
import datetime
import pywt # need to install wavelet package from auto/pywavelets in anaconda
import icss # in this directory

def readfile():
	# read anomaly groundtruth
	f = open("../data/bad-feature-norm.txt", "r")
	badlist = []
	for line in f:
		line = line.strip().split()
		badlist.append(line[0])
	f.close()
	# read normal groundtruth
	f = open("../data/good-feature-norm.txt", "r")
	goodlist = []
	for line in f:
		line = line.strip().split()
		goodlist.append(line[0])
	f.close()
	# read time series
	f = open("../data/http-dip-1w-ip-ts1.txt", "r")
	ts = []
	ground = []
	for line in f:
		line = line.strip().split()
		numer = []
		for x in line[1:]:
			numer.append(int(x))
		ts.append(numer)
		if line[0] in badlist:
			ground.append([1])
		if line[0] in goodlist:
			ground.append([0])
	ts = numpy.array(ts)
	ground = numpy.array(ground)
	f.close()
	return ts, ground

def readallfile():
	f = open("../data/huangyixiang_ts_4.txt", "r")
	ts = []
	for line in f:
		line = line.strip().split()
		numer = []
		for x in line[1:]:
			numer.append(int(x))
		ts.append(numer)
	ts = numpy.array(ts)
	f.close()
	return ts

def slidingwindow(M, winsize): 
	partts = []
	for i in range(M.shape[1]):
		part = M[:, i:i + winsize]
		partts.append(part)
	return partts	

def clustering(mat):
	ap = cluster.AffinityPropagation(damping = 0.75)
	ap.fit(mat)
	lab = ap.labels_
	af = numpy.array(ap.affinity_matrix_)
	label = numpy.zeros(len(lab))
	for i in range(lab):
		if -af[i, lab[i]] > numpy.linalg.norm(mat[lab[i]]):
			label[i] = 1
	return label

def waveletdetect(mat):
	wvlt = []
	for row in mat:
		#wvlt = pywt.dwt(row,'haar')
		wdec = pywt.wavedec(row, "haar", level = int(math.log(len(row), 2)))
		wvlt.append(wdec[0][0])
	wvlt = numpy.array(wvlt)
	return wvlt

def fftdetect(mat): # fft and anomaly if more than mean
	freq = []
	for i in range(mat.shape[0]):
		f = numpy.fft.fft(mat[[i], :])
		f = abs(f[0])
		freq.append(f[0])
	freq = numpy.array(freq)
	return freq

def pauta(vec):
	vec = numpy.array(vec)
	label = numpy.zeros(len(vec))
	for i in range(len(vec)):
		if abs(vec[i] - numpy.mean(vec) / numpy.std(vec)) > 3:
			label[i] = 1
	return label

def ItCuSqSum(vec):
	vec = numpy.array(vec)
	vec = vec.tolist()
	lab = 0
	if len(vec) > 0:
		pos = icss.ICSS(vec)
		if len(pos) > 0:
			lab = 1
	label = numpy.zeros(len(vec))
	for i in range(len(vec)):
		if i in label:
			label[i] = 1
	return label

def evaluate(label, ground):
	eval = numpy.zeros((2, 2))
	for i in range(len(ground)):
		# TP
		if label[i] == 1 and ground[i] == 1:
			eval[0, 0] += 1
		# FP
		if label[i] == 1 and ground[i] == 0:
			eval[1, 0] += 1
		# FN
		if label[i] == 0 and ground[i] == 1:
			eval[0, 1] += 1
		# FN
		if label[i] == 0 and ground[i] == 0:
			eval[1, 1] += 1
	return eval

def slidingpeak(winsize):
	ts, ground = readfile()
	partts = slidingwindow(ts, winsize)
	lab = []
	dl = []
	for i in range(ts.shape[1] - winsize):
		tempdl =waveletdetect(partts[i]) 
		dl.append(tempdl)
	dl = numpy.array(dl)
	dl = dl.transpose()
	for i in range(ts.shape[0]):
		newdl = dl[i].tolist()
		newdl = ItCuSqSum(newdl)
		lab.append(newdl)
	lab = numpy.array(lab)
	label = numpy.zeros(ts.shape[0])
	lab = lab.transpose()
	for i in range(lab.shape[1]):
		temp = lab[:, [i]]
		if numpy.count_nonzero(temp) >= 1:
			label[i] = 1
	eval = evaluate(label, ground)
	return eval

def nowin():
	ts, ground = readfile()
	lab = waveletdetect(ts)
	lab = numpy.array(lab)
	eval = evaluate(lab, ground)
	return eval


def outputwindow(winsize):
	ts = readallfile()
	partts = slidingwindow(ts, winsize)
	if not os.path.exists("../result/sw/allsw" + str(winsize) + "/"):
		os.makedirs("../result/sw/allsw" + str(winsize) + "/")
	for i in range(len(partts)):
		part = partts[i]
		f = open("../result/sw/allsw" + str(winsize) + "/" + str(i) + ".csv", "w")
		for line in part:
			wline = ""
			for item in line:
				wline += str(item) + ","
			wline = wline + "\n"
			f.write(wline)
		f.close()

if __name__ == "__main__":
	# cut log size
	st = datetime.datetime.now()
	if os.path.isfile("../result/slidingpeak.log"):
		logsize = os.path.getsize("../result/slidingpeak.log")
		if logsize / 1024 / 1024 > 2:
			os.remove("../result/slidingpeak.log")
	# set logging configure
	FORMAT = "%(asctime)s %(filename)s line:%(lineno)d %(levelname)s\n %(message)s"
	FNM = "../result/slidingpeak.log"
	DATEFMT = "%Y-%m-%d %H:%M:%S";
	logging.basicConfig(level = logging.INFO, format = FORMAT,datefmt = DATEFMT,filename = FNM,filemode = "a")
	console = logging.StreamHandler()
	console.setLevel(logging.INFO)
	console.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
	logging.getLogger("").addHandler(console)
	# present algorithm
	linfo = "icss principle, haar wavelet"
	logging.info("Info: " + linfo) # comment on log
	for winsize in [4]:
		logging.info("Window size: " + str(winsize))
		eval = slidingpeak(winsize)
		logging.info("Confusion matrix: " + str(eval)) # output accuracy matrix
	et = datetime.datetime.now()
	runtime = (et - st).seconds
	logging.info("Running time: " + str(runtime))
	"""
	eval = nowin()
	logging.info(str(eval))
	outputwindow(3)
	"""