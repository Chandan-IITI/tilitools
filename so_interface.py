from cvxopt import matrix,spmatrix,sparse,exp
import numpy as np
import math as math



class SOInterface:
	""" Structured Object Interface"""

	X = [] # (list of matricies) data 
	y = [] # (list of vectors) state sequences (if present)

	samples = -1 # (scalar) number of training data samples
	dims = -1 # (scalar) number of input dimensions

	def __init__(self, X, y=[]):
		self.X = X
		self.y = y

		# assume either co.matrix or list-of-objects
		if isinstance(X, matrix):
			(self.dims, self.samples) = X.size
		else: #list
			self.samples = len(X)
			(self.dims, foo) = X[0].size
		print('Create structured object with #{0} training examples, each consiting of #{1} features.'.format(self.samples,self.dims))


	def argmin(self, sol, idx):
		return self.argmax(sol, idx, opt_type='quadratic')

	def argmax(self, sol, idx, add_loss=False, opt_type='linear'): raise NotImplementedError
		
	def calc_loss(self, idx, y): raise NotImplementedError

	def get_joint_feature_map(self, idx, y=[]): raise NotImplementedError

	def get_num_samples(self):
		return self.samples

	def get_num_dims(self): raise NotImplementedError