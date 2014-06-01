import cvxopt as co
import numpy as np
import pylab as pl
import matplotlib.pyplot as plt
import scipy.io as io
import sklearn.metrics as metric
import csv

from kernel import Kernel
from ocsvm import OCSVM

from ssvm import SSVM
from latentsvdd import LatentSVDD
from structured_ocsvm import StructuredOCSVM
from structured_pca import StructuredPCA
from toydata import ToyData

from so_hmm import SOHMM



def remove_mean(X, dims):
	cnt = 0
	tst_mean = co.matrix(0.0, (1, dims))
	for i in range(len(X)):
		lens = len(X[i][0,:])
		cnt += lens
		tst_mean += co.matrix(1.0, (1, lens))*X[i].trans()
	tst_mean /= float(cnt)
	print tst_mean
	for i in range(len(X)):
		for d in range(dims):
			X[i][d,:] = X[i][d,:]-tst_mean[d]
	cnt = 0
	tst_mean = co.matrix(0.0, (1, dims))
	for i in range(len(X)):
		lens = len(X[i][0,:])
		cnt += lens
		tst_mean += co.matrix(1.0, (1, lens))*X[i].trans()
	print tst_mean/float(cnt)
	return X


def load_data(num_exms, path, fname, inds, label):
	LEN = 800
	DIMS = 5
	# training data
	trainX = []
	trainY = []
	start_symbs = []
	stop_symbs = []
	phi_list = []
	marker = []
	for i in xrange(num_exms):

		# load file 
		phi_i = co.matrix(0.0, (1, DIMS))
		lbl = co.matrix(0, (1,LEN))
		exm = co.matrix(0.0, (DIMS, LEN))
		with open('{0}{1}{2:03d}.csv'.format(path, fname, inds[i]+1)) as f:
			reader = csv.reader(f)
			idx = 0
			for row in reader:
				if idx==1:
					for t in xrange(len(row)-1):
						lbl[t] = int(row[t+1])-1
				if idx>=3:
					for t in xrange(len(row)-1):
						exm[idx-3, t] = float(row[t+1])
						phi_i[idx-3] += float(row[t+1])

				idx += 1
		norm = np.linalg.norm(phi_i,2)
		#print norm
		phi_i /= norm

		marker.append(label)
		phi_list.append(phi_i)
		trainX.append(exm)
		trainY.append(lbl)

	return (trainX, trainY, phi_list, marker)


if __name__ == '__main__':
	# load data file
	directory = '/home/nicococo/Code/wind/'
	#directory = '/home/nico/mnt_tucluster/Data/wind/'
	DIMS = 5
	EXMS_ANOM = 200
	EXMS_NON = 200

	NUM_TRAIN_ANOM = 20
	NUM_TRAIN_NON = 100
	
	NUM_TEST_ANOM = 20
	NUM_TEST_NON = 100

	NUM_COMB_ANOM = NUM_TRAIN_ANOM+NUM_TEST_ANOM
	NUM_COMB_NON = NUM_TRAIN_NON+NUM_TEST_NON

	anom_prob = float(NUM_COMB_ANOM) / float(NUM_COMB_ANOM+NUM_COMB_NON)
	print('Anomaly probability is {0}.'.format(anom_prob))
	REPS = 1
	showPlots = True

	auc = []
	base_auc = []
	res = []
	base_res = []
	for r in xrange(REPS):
		# shuffle genes and intergenics
		anom_inds = np.random.permutation(EXMS_ANOM)
		non_inds = np.random.permutation(EXMS_NON)

		# load genes and intergenic examples
		(combX, combY, phi_list, marker) = load_data(NUM_COMB_ANOM, directory, 'winddata_A15_only_', anom_inds, 1)
		(X, Y, phis, lbls) = load_data(NUM_COMB_NON, directory, 'winddata_C10_only_', non_inds, 0)
		combX.extend(X)
		combY.extend(Y)
		phi_list.extend(phis)
		marker.extend(lbls)
		combX = remove_mean(combX, DIMS)

		trainX = combX[0:NUM_TRAIN_ANOM]
		trainX.extend(X[0:NUM_TRAIN_NON])
		trainY = combY[0:NUM_TRAIN_ANOM]
		trainY.extend(Y[0:NUM_TRAIN_NON])

		testX = combX[NUM_TRAIN_ANOM:NUM_COMB_ANOM]
		testX.extend(X[NUM_TRAIN_NON:NUM_COMB_NON])
		testY = combY[NUM_TRAIN_ANOM:NUM_COMB_ANOM]
		testY.extend(Y[NUM_TRAIN_NON:NUM_COMB_NON])

		train = SOHMM(trainX, trainY, num_states=2)
		test = SOHMM(testX, testY, num_states=2)
		comb = SOHMM(combX, combY, num_states=2)

		# SSVM annotation
		#ssvm = SSVM(train, C=10.0)
		#(lsol,slacks) = ssvm.train()
		#(vals, svmlats) = ssvm.apply(test)
		#(err_svm, err_exm) = test.evaluate(svmlats)
		#base_res.append((err_svm['fscore'], err_svm['precision'], err_svm['sensitivity'], err_svm['specificity']))
		base_res.append((0.0,0.0,0.0,0.0))

		# SAD annotation
		lsvm = StructuredOCSVM(comb, C=1.0/(comb.samples*anom_prob))
		(lsol, latsComb, thres) = lsvm.train_dc(max_iter=100)
		(lval, lats) = lsvm.apply(test)
		(err, err_exm) = test.evaluate(lats)
		res.append((err['fscore'], err['precision'], err['sensitivity'], err['specificity']))
		print err
		#print err_svm
		
		if (showPlots==True):
			for i in range(comb.samples):
				if (i>=10 and marker[i]==1):
					LENS = 800
					plt.plot(range(LENS),comb.X[i][0,:].trans() - 2+(i-10)*10,'-m')

					plt.plot(range(LENS),latsComb[i].trans() +(i-10)*10,'-r')
					plt.plot(range(LENS),comb.y[i].trans() + 2 +(i-10)*10,'-b')
					#plt.plot(range(LENS),svmlats[i-10].trans() + 4 +(i-10)*10,'-k')
			
					(anom_score, scores) = comb.get_scores(lsol, i, latsComb[i])
					plt.plot(range(LENS),scores.trans() + 6 + (i-10)*10,'-g')
					break
			plt.show()

		# SAD anomaly scores
		(scores, foo) = lsvm.apply(comb)
		(fpr, tpr, thres) = metric.roc_curve(marker, scores)
		bauc = metric.auc(fpr, tpr)
		if (bauc<0.5):
			bauc = 1.0-bauc
		auc.append(bauc)
		print auc

		# train one-class svm
		phi = co.matrix(phi_list).trans()
		print phi.size
		kern = Kernel.get_kernel(phi, phi)
		ocsvm = OCSVM(kern, C=1.0/(comb.samples*anom_prob))
		ocsvm.train_dual()
		(oc_as, foo) = ocsvm.apply_dual(kern[:,ocsvm.get_support_dual()])
		(fpr, tpr, thres) = metric.roc_curve(marker, oc_as)
		bauc = metric.auc(fpr, tpr)
		if (bauc<0.5):
			bauc = 1.0-bauc
		base_auc.append(bauc)
		print base_auc

	
	print '##############################################'
	print auc
	print base_auc
	print '##############################################'
	print res
	print base_res
	print '##############################################'

	# store result as a file
	data = {}
	data['auc'] = auc
	data['base_auc'] = base_auc
	data['res'] = res
	data['base_res'] = base_res

	io.savemat('14_nips_wind_01.mat',data)

	print('finished')