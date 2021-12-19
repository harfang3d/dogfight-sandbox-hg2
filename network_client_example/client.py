from aero_model import derivatives
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

alpha = 5
beta = 0
deltaE = 0
deltaA = 0
deltaR = 0

cx, cxQ, cy, cyP, cyR, cz, czQ, cl, clP, clR, clDeltaA, clDeltaR, cm, cmQ, cn, cnP, cnR, cnDeltaA, cnDeltaR = derivatives(alpha, beta, deltaE, deltaA, deltaR)


alpha_range = np.linspace(-10, 45, 275)
cx_range = [derivatives(alpha, beta, deltaE, deltaA, deltaR)[12] for alpha in alpha_range]

sns.lineplot(x=alpha_range, y=cx_range)
plt.show()