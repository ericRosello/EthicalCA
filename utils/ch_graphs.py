import matplotlib.pyplot as plt

# script to make convex hull graphs

points = [(0.18777, 0.09777),
          (0.18906, 0.09515),
          (0.23628, -0.0913),]

labels = ['Ethical-optimal', 'Second-best', 'Unethical']
labels_rel = [(0.001, 0.001), (0.001, -0.002), (-0.009, -0.008)]

x_vals=[]
y_vals=[]
for i, (x, y) in enumerate(points):
    x_vals.append(x)
    y_vals.append(y)
    plt.text(x+labels_rel[i][0], y+labels_rel[i][1], labels[i])

plt.xlabel(r'Individual value $V_{0}(S_{0})$', fontsize=12)
plt.ylabel(r'Ethical value $(V_{N}(S_{0})+V_{E}(S_{0}))$', fontsize=12)

plt.grid()
plt.plot(x_vals, y_vals, 'ko', linestyle="--")
plt.tight_layout()
plt.show()

plt.clf()

w_range = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
col = ['go', 'y^', 'rv']
for i, (x, y) in enumerate(points[:]):
    x_vals = []
    y_vals = []
    for w in w_range:
        v = x + w * y
        x_vals.append(w)
        y_vals.append(v)
    z = 10 if i == 0 else 5
    plt.plot(x_vals, y_vals, col[i], linestyle='--', label=labels[i], zorder=z)
plt.axvspan(0.492, 0.9, color='green', alpha=0.3)
plt.axvspan(0.253, 0.492, color='yellow', alpha=0.3)
plt.axvspan(-0.1, 0.253, color='red', alpha=0.3)
plt.xlim([-0.05, 0.85])
plt.xlabel(r'Ethical weight $w_{e}$', fontsize=12)
plt.ylabel(r'Scalarized Value function $V(S_{0})$', fontsize=12)
plt.legend()

plt.grid()
plt.show()
