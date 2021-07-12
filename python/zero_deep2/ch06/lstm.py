class LSTM:
	def __init(self, Wx, Wh, b):
		self.params = [Wx, Wh, b]
		self.grads = [np.zero_like(Wx), np.zeros_like(Wh), np.zeros_like(b)]
		self.cache = None
	
	def forward(self, x, h_prev, c_prev):
		Wx, Wh, b = self.params
		N, H = h_prev.shape

		A = np.dot(x,Wx) + np.dot(h_prev, Wh) + b

		# slice
		f = A[:, :H]
		g = A[:, H:2*H]
		i = A[:, 2*H:3*H]
		o = A[:, 3*H:]

		f = sigmoid(f)
		g = np.tanh(g)
		i = sigmoid(i)
		o = sigmoid(o)

		c_next = f * c_prev + g * i
		h_next = o * np.tanh(c_next)

		self.cache = (x, h_prev, c_prev, i, f, g, o, c_next)
		return h_next, c_next