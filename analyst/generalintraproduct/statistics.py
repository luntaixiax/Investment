import pandas as pd
from scipy import stats
import numpy as np
from statsmodels.tsa.stattools import adfuller
import statsmodels.api as sm
from hmmlearn import hmm
from matplotlib import pyplot as plt
import seaborn as sns
import itertools

def test_stationary(s, alpha = 0.05):
	adf, p_value, lag, nobs, criticals, icbest = adfuller(s)
	if not criticals.get(f"{alpha:.0%}"):
		alpha = 0.05

	return {
		"adf" : adf,
		"critical" : criticals.get(f"{alpha:.0%}"),
		"p_value" : p_value,
		"alpha": alpha,
		"stationary" : p_value < alpha,
		"lag" : lag,
		"nobs" : nobs,
	}

def markov_switching(s, k_regimes = 3):
	mod_kns = sm.tsa.MarkovRegression(s, k_regimes = k_regimes,  switching_variance = True)
	res_kns = mod_kns.fit()
	return res_kns.summary()


def hidden_markov(x, n_state = 4):
	x = np.array(x).reshape((len(x), 1))
	model = hmm.GMMHMM(n_components = n_state, covariance_type = "full", n_iter = 100)
	model.fit(x)
	z = model.predict(x)

	print(model.means_)
	print(model.covars_)
	print(model.weights_)
	print(model.monitor_.converged)


	m = model.means_[z,0,0]
	#print(m[-100:])

	# fig = plt.figure()
	# ax = fig.add_subplot(111)
	# ax.plot(x[-100:])
	# ax.plot(m[-100:], color = "green")
	# ax2 = ax.twinx()
	# ax2.plot(z[-100:], color = "red")
	# plt.show()

	df = pd.DataFrame({
		"x" : x.ravel(),
		"z" : z,
	})

	rows, cols = dimension(n_state)
	f, axes = plt.subplots(rows, cols, figsize = (7, 7))
	for state, ax in axes_iter(axes, n_state, rows, cols):
		d = df.loc[df["z"] == state, "x"]
		ax = sns.distplot(d, ax = ax, norm_hist = True, label = "real")
		vs = np.linspace(d.min(), d.max(), 50)

		mu = model.means_[state,0,0]
		sigma = model.covars_[state,0,0,0] ** 0.5
		pdf = stats.norm.pdf(vs, loc = mu, scale = sigma)
		ax.plot(vs, pdf, 'r', lw = 2, label = "estimate")
		ax.set(xlabel = f"state{state}", title=f'mu={mu:.3%}, sigma={sigma:.3%}')
	plt.legend()
	plt.show()


def dimension(n):
	# decompose into m*(m+1)
	for x in range(1, int(n ** 0.5 + 2)):
		for y in range(1, x + 1):
			if x * y >= n and x * (y-1) < n and y * (x-1) < n:
				return x,y

def axes_iter(axes, n, rows, cols):
	r = itertools.product(range(rows), range(cols))
	for i in range(n):
		row, col = next(r)
		yield i, axes[row, col]


if __name__ == '__main__':
	for i in range(10):
		print(i, dimension(i))


