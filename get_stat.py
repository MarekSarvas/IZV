import re
import matplotlib.pyplot as plt
import numpy as np
import sys
from download import DataDownloader


def plot_stat(data_source, fig_location=None, show_figure=False):


    # arr = data_source[1]
    data = np.vstack((data_source[1][0], data_source[1][4])).T
    regions = np.unique(data[:, 0])
    crashes = np.zeros_like(regions, dtype=int)

    max_year = int(data[np.argmax(data[:, 1])][1])
    min_year = int(data[np.argmin(data[:, 1])][1])

    fig, axs = plt.subplots(max_year - min_year+1, 1, sharex='col')
    x = np.random.randn(1000)

    for y in range(max_year - min_year + 1):
        for i, reg in enumerate(regions):
            year_data = data[data[:, 1] == str(min_year+y)]
            crashes[i] = np.sum(year_data == reg)

        axs[y].bar(regions, crashes)
        a = np.arange(0, np.max(crashes), 4000)
        print(a)
        axs[y].set_yticks(a)
        axs[y].set_ylabel(min_year+y)



    plt.show()


    pass


if __name__ == '__main__':
    data_source = DataDownloader().get_list()
    plot_stat(data_source, show_figure=True)
