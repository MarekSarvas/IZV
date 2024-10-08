"""
Author: Marek Sarvas
School: VUT FIT
Project: IZV
Description: Script for creating graph of car crashes in czech republic for given years and regions.
"""

import argparse
import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MultipleLocator

from download import DataDownloader


def plot_stat(data_source, fig_location=None, show_figure=False):
    """ Plots number of crashes in every year for every region.

    :param data_source: tuple of formatted data, index 0 is list of column header, index 1 is list od numpy arrays
    :param fig_location: path where created figure will be stored
    :param show_figure: boolean if figure should be displayed
    """
    # make matrix from regions and years with shape=(crashes, 2)
    data = np.vstack((data_source[1][0], data_source[1][4])).T

    regions = np.unique(data[:, 0])  # get all regions presented in data
    crashes = np.zeros_like(regions, dtype=int)

    # get interval boundaries for years
    max_year = int(data[np.argmax(data[:, 1])][1])
    min_year = int(data[np.argmin(data[:, 1])][1])

    # create figure and subplots
    fig, axs = plt.subplots(max_year - min_year+1, 1, sharex=True, sharey=True)
    fig.set_figwidth(8)
    fig.set_figheight(6)
    fig.suptitle('Počet nehôd v jednotlivých rokoch v českých krajoch', verticalalignment='top',
                 horizontalalignment='center')
    fig.tight_layout()
    fig.subplots_adjust(top=0.89)  # adjust space between figure title and first subplot

    # compute number of crashes for each year for each region
    for y in range(max_year - min_year + 1):
        for i, reg in enumerate(regions):
            year_data = data[data[:, 1] == str(min_year+y)]
            crashes[i] = np.sum(year_data == reg)

        # get array of indexes of number of crashes in descending order
        Ind = np.argsort(crashes)
        Ind = np.flip(Ind)

        # plot crashes for current year as bars
        bar_list = axs[y].bar(regions, crashes, color=(0.91, 0.27, 0.27, 0.8))

        # add number of crashes into every bar
        for i, v in enumerate(crashes):
            axs[y].text(i, v-(v//10), s=v, fontsize=6, verticalalignment='top', horizontalalignment='center')

        # add anotation of regions based of number of crashes in descending order<1, number of regions>
        for i, v in enumerate(Ind):
            axs[y].text(v, crashes[v], s=i+1, fontsize=6, verticalalignment='bottom', horizontalalignment='center')

        # highlight region with the most crashes in current year
        bar_list[Ind[0]].set_color((0.77, 0.07, 0.07, 0.9))

        axs[y].spines['right'].set_visible(False)
        axs[y].spines['top'].set_visible(False)

        axs[y].xaxis.set_ticks_position('none')

        axs[y].yaxis.set_major_locator(MultipleLocator(5000))
        axs[y].tick_params(axis="y", labelsize=8, rotation=20)
        axs[y].yaxis.grid(True)
        axs[y].set_ylabel('Počet nehôd', fontsize=8)

        axs[y].set_axisbelow(True)  # grid is behind bars
        axs[y].set_title(min_year+y, size=10)  # title of subplot

    # save figure as png
    if fig_location:
        path = fig_location.split('/')
        file = path[-1]
        path.pop(-1)
        path = '/'.join(path)
        if not os.path.exists(f'{path}'):
            os.makedirs(path)
        plt.savefig(f'{path}/{file}', bbox_inches="tight")

    if show_figure:
        plt.show()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--fig_location', default=None, help='Set path where figure is stored')
    parser.add_argument('--show_figure', action='store_true', help='Set to show figure')
    args = parser.parse_args()

    data_source = DataDownloader().get_list()
    plot_stat(data_source, fig_location=args.fig_location, show_figure=args.show_figure)
