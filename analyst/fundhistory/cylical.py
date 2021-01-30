import matplotlib.pyplot as plt
import numpy as np
import numpy.fft as fft

from dataUtils.dataApis.funds import getFundMergedHist


fund_id = "481001"
df = getFundMergedHist(fund_id).dropna()

returns = df["Return"]


# volatility of returns
vol_period = 30
vols = []
for i in range(vol_period, len(returns)):
    vols.append(returns[i - vol_period : i].std())

returns = np.array(vols)


Fs = len(returns)          # 采样频率
T = 1 / Fs            # 采样周期
L = len(returns)            # 信号长度
t = np.array([i*T for i in range(L)])


#S = 0.2+0.7*np.cos(2*np.pi*50*t+20/180*np.pi) + 0.2*np.cos(2*np.pi*100*t+70/180*np.pi)
complex_array = fft.fft(returns)
S_ifft = fft.ifft(complex_array)
freqs = fft.fftfreq(t.size, t[1] - t[0])
pows = np.abs(complex_array)


def fourierExtrapolation(x, n_predict):
    n = x.size
    n_harm = 20  # number of harmonics in model
    t = np.arange(0, n)
    p = np.polyfit(t, x, 1)  # find linear trend in x
    x_notrend = x - p[0] * t  # detrended x
    x_freqdom = fft.fft(x_notrend)  # detrended x in frequency domain
    f = fft.fftfreq(n)  # frequencies
    indexes = list(range(n))
    # sort indexes by frequency, lower -> higher
    indexes.sort(key = lambda i: np.absolute(f[i]))

    t = np.arange(0, n + n_predict)
    restored_sig = np.zeros(t.size)
    for i in indexes[:1 + n_harm * 2]:
        ampli = np.absolute(x_freqdom[i]) / n  # amplitude
        phase = np.angle(x_freqdom[i])  # phase
        restored_sig += ampli * np.cos(2 * np.pi * f[i] * t + phase)
    return restored_sig + p[0] * t

n_predict = 100
extrapolation = fourierExtrapolation(returns, n_predict)



plt.subplot(411)
plt.grid(linestyle=':')
plt.plot(Fs * t, returns, label = 'S')  # y是1000个相加后的正弦序列
plt.xlabel("t")
plt.ylabel("Returns")
plt.title("Returns")
plt.legend()

###################################
plt.subplot(412)

# S_new是ifft变换后的序列
plt.plot(Fs * t, S_ifft, label='S_ifft', color ='orangered')
plt.xlabel("t")
plt.ylabel("S_ifft(t)")
plt.title("inverse fourier")
plt.grid(linestyle=':')
plt.legend()

###################################


plt.subplot(413)
plt.title('FFT')
plt.xlabel('Frequency')
plt.ylabel('Power')
plt.tick_params(labelsize = 10)
plt.grid(linestyle = ':')
plt.plot(freqs[(freqs > 0) & (freqs < 250)], pows[(freqs > 0) & (freqs < 250)], c='orangered', label='Frequency')
plt.legend()
plt.tight_layout()

plt.subplot(414)
plt.title('FFT - predict')
plt.xlabel('t')
plt.ylabel('Returns')
plt.tick_params(labelsize = 10)
plt.grid(linestyle = ':')
plt.plot(np.arange(0, extrapolation.size), extrapolation, 'r', label = 'extrapolation')
#plt.plot(np.arange(0, returns.size), returns, label = 'x')
plt.legend()


plt.show()