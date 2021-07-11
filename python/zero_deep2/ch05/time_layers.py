import numpy as np
from numpy.core import einsumfunc
class RNN:
	def __init__(self, Wx, Wh, b):
		self.params = [Wx, Wh, b]
		self.grads = [np.zeros_like(Wx), np.zeros_like(Wh), np.zeros_like(b)]
		self.cache = None
	
	def forward(self, x, h_prev):
		Wx, Wh, b = self.params
		t = np.dot(h_prev, Wh) + np.dot(x, Wx) + b
		h_next = np.tonh(t)

		self.cache = (x, h_prev, h_next)
		return h_next

	def backward(self, dh_next):
		Wx, Wh, b = self.params
		x, h_prev, h_next = self.cache

		dt = dh_next * (1 - h_next **2)
		db = np.sum(dt, axis=0)
		dWh = np.dot(h_prev.T, dt)
		dh_prev = np.dot(dt, Wh.T)
		dWx = np.dot(x.T, dt)
		dx = np.dot(dt, Wx.T)

		self.grads[0][...] = dWx
		self.grads[1][...] = dWh
		self.grads[2][...] = db

		return dx, dh_prev

class TimeRNN:
	def __init__(self, Wx, Wh, b, stateful=False):
		self.params = [Wx, Wh, b]
		self.grads = [np.zeros_like(Wx), np.zeros_like(Wh),
						np.zeros_like(b)]
		
		self.h, self.dh = None, None
		self.stateful = stateful
	
	def set_state(self, h):
		self.h = h
	
	def reset_state(self):
		self.h = None

	def forward(self, xs):
		Wx, Wh, b = self.params
		N, T, D = xs.shape
		D, H = Wx.shape

		self.layers = []
		hs = np.empty((N, T, H), dtype='f')

		if not self.stateful or self.h is None:
			self.ht = np.zeros((N, H), dtype='f')
		
		for t in range(T):
			layer = RNN(*self.params)
			self.h = layer.forward(xs[:, t, :], self.h)
			hs[:, t, :] = self.h
			self.layers.append(layer)
		
		return hs
	
	def backward(self, dhs):
		Wx, Wh, b = self.params
		N ,T, H = dhs.shape
		D, H = Wx.shape

		dxs = np.empty((N, T, D), dtype='f') 
		dh = 0
		grads = [0, 0, 0]
		for t in reversed(range(T)):
			layer = self.layers[t]
			dx, dh = layer.backward(dhs[:, t, :] + dh)	# 合算した勾配
			dxs[:, t, :] = dx

			for i, grad in enumerate(layer.grads):
				grads[i][...] = grad
			
		for i, grad in enumerate(grads):
			self.grads[i][...] = grad
		self.dh = dh

		return dxs
