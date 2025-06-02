import matplotlib.pyplot as plt
import numpy as np
import json

# block_C_x = [(b,C) for b in range(5, 39, 2) for C in range(2, 38, 2)]
# x_values = list(range(len(block_C_x)))

x_values = [b for b in range(5, 39, 2)]

num_boxes_y = [int(x.strip()) for x in open('num-boxes.nd', 'r').readlines() if x.strip()]
avg_box_prox_y = [float(x.strip()) for x in open('avg-prox.nd', 'r').readlines() if x.strip()]

fig = plt.figure()
x_title = 'Block Neighborhood and C Value'
plt.plot(x_values, avg_box_prox_y, marker='o', color='red', label='Average Closest Box Proximity')
plt.plot(x_values, num_boxes_y, marker='o', color='blue', label='Number of Boxes')
plt.xlabel(x_title)
plt.grid()
plt.legend()
fig.savefig('BlockNeighborhoodCValue-Metrics.png')
plt.show()