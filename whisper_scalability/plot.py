import matplotlib.pyplot as plt
import numpy as np
from labellines import labelLines

# # Trying to get interpolation to work but getting error:
# # ValueError: The number of derivatives at boundaries does not match: expected 1, got 0+0
# from scipy.interpolate import make_interp_spline, BSpline
# n_users = np.array([100, 10000, 1000000])
# bw_case8 = np.array([1, 1.5, 98.1])
# # 300 represents number of points to make between T.min and T.max
# n_users_new = np.linspace(n_users.min(), n_users.max(), 300)
# spl8 = make_interp_spline(n_users, bw_case8, k=3)  # type: BSpline
# bw_case8_smooth = spl8(n_users_new)
# plt.plot(n_users_new, bw_case8_smooth, label='case 8', linewidth=2)

n_users = [100, 10000, 1000000]

bw_case1 = [1, 1, 1]
bw_case2 = [97.7, 9.5*1000, 935.7*1000]
bw_case3 = [49.3, 4.*10008, 476.8*1000]
bw_case4 = [1, 1.5, 98.1]
bw_case5 = [10.7, 978, 95.5*1000]
bw_case6 = [21.5, 1.9*1000, 190.9*1000]
bw_case7 = [3.9, 284.8, 27.8*1000]
bw_case8 = [1, 1.5, 98.1]

plt.xlim(100, 10**6)
plt.ylim(1, 10**6)

plt.plot(n_users, bw_case1, label='case 1', linewidth=4, linestyle='dashed')
plt.plot(n_users, bw_case2, label='case 2', linewidth=4, linestyle='dashed')
plt.plot(n_users, bw_case3, label='case 3', linewidth=4, linestyle='dashed')
plt.plot(n_users, bw_case4, label='case 4', linewidth=4, linestyle='dashed')
plt.plot(n_users, bw_case5, label='case 5', linewidth=4)
plt.plot(n_users, bw_case6, label='case 6', linewidth=4)
plt.plot(n_users, bw_case7, label='case 7', linewidth=4)
plt.plot(n_users, bw_case8, label='case 8', linewidth=4)

#labelLines(plt.gca().get_lines(),zorder=0)

case1 = "Case 1. Only receiving messages meant for you [naive case]"
case2 = "Case 2. Receiving messages for everyone [naive case]"
case3 = "Case 3. All private messages go over one discovery topic [naive case]"
case4 = "Case 4. All private messages partitioned into shards [naive case]"
case5 = "Case 5. Case 4 + All messages passed through bloom filter"
case6 = "Case 6. Case 5 + Benign duplicate receives"
case7 = "Case 7. Case 6 + Mailserver case under good conditions with small bloom fp and mostly offline"
case8 = "Case 8. Waku - No metadata protection with bloom filter and one node connected; static shard"


plt.xlabel('number of users (log)')
plt.ylabel('mb/day (log)')
plt.legend([case1, case2, case3, case4, case5, case6, case7, case8], loc='upper left')
plt.xscale('log')
plt.yscale('log')


plt.axhspan(0, 10, facecolor='0.2', alpha=0.2, color='blue')
plt.axhspan(10, 30, facecolor='0.2', alpha=0.2, color='green')
plt.axhspan(30, 100, facecolor='0.2', alpha=0.2, color='orange')
plt.axhspan(100, 10**6, facecolor='0.2', alpha=0.2, color='red')

#plt.axvspan(0, 10**2+3, facecolor='0.2', alpha=0.5)
#plt.axvspan(10**4, 10**4+10**2, facecolor='0.2', alpha=0.5)
#plt.axvspan(10**6, 10**6+10**4, facecolor='0.2', alpha=0.5)

#for i in range(0, 5):
#    plt.axhspan(i, i+.2, facecolor='0.2', alpha=0.5)

plt.show()
