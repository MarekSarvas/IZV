"""
Author: Marek Sarvas
School: VUT FIT
Project: IZV
Description: Script for creating graph of car crashes in czech republic for given years and regions.
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import gzip
import pickle

B_to_MB = 1048576

to_category = ['a', 'b', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'n', 'o', 'p', 'q', 'r', 's', 't']
to_float = ['d', 'e', 'f', 'g']
to_int8 = ['p5a', 'p6', 'p7', 'p8', 'p9', 'p10', 'p11', 'p15', 'p16', 'p18', 'p19', 'p20', 'p21', 'p22', 'p23', 'p24',
           'p27', 'p28', 'p49', 'p50a', 'p50b', 'p51', 'p55a', 'p57', 'p58']


def get_dataframe(filename="accidents.pkl.gz", verbose=False):

    data = pd.read_pickle(filename, compression="gzip")

    if verbose:
        print(f'orig_size={round(data.memory_usage(index=False, deep=True).sum() / B_to_MB, 2)} MB')

    for col in to_category:
        data[col] = data[col].astype('category')
    for col in to_float:
        data[col] = data[col].astype('float64')
    for col in to_int8:
        data[col] = data[col].astype('int8')
    data.insert(0, column='date', value=data['p2a'].astype('datetime64'))
    if verbose:
        print(f'new_size={round(data.memory_usage(index=False, deep=True).sum() / B_to_MB, 2)} MB')

    return data


def plot_conseq(df, fig_location=None, show_figure=False):

    print("Creating data frames")
    p13a = df[['region', 'p13a']].groupby('region').agg(np.sum).reset_index()
    p13b = df[['region', 'p13b']].groupby('region').agg(np.sum).reset_index()
    p13c = df[['region', 'p13c']].groupby('region').agg(np.sum).reset_index()
    crashes = df['region'].value_counts().sort_values(ascending=False)
    data_list = [p13a, p13b, p13c]

    sns.set_style("darkgrid")
    fig, axs = plt.subplots(4, 1, sharex=True)
    fig.set_figwidth(8)
    fig.set_figheight(6)

    fig.tight_layout()
    fig.subplots_adjust(top=0.89)  # adjust space between figure title and first subplot

    c_pallet = sns.color_palette("mako", n_colors=14)

    sns.barplot(ax=axs[0], x="region", y="p13a", data=p13a, order=p13a['region'], palette=c_pallet)
    sns.barplot(ax=axs[1], x="region", y="p13b", data=p13b, order=p13b['region'], palette=c_pallet)
    sns.barplot(ax=axs[2], x="region", y="p13c", data=p13c, order=p13c['region'], palette=c_pallet)
    sns.barplot(ax=axs[3], x=crashes.index, y=crashes.values, palette=c_pallet)

    axs[0].title.set_text('usmrceno osob')
    axs[1].title.set_text('tezce zraneno osob')
    axs[2].title.set_text('lehce zraneno osob')
    axs[3].title.set_text('celkovy  pocet nehod')

    for i in range(4):
        axs[i].set(xlabel=None, ylabel='pocet')
        axs[i].spines['right'].set_visible(False)
        axs[i].spines['top'].set_visible(False)

    if fig_location is not None:
        plt.savefig(f'{fig_location}', bbox_inches="tight")

    if show_figure:
        plt.show()


def plot_damage(df, fig_location=None, show_figure=False):
    pass


def plot_surface(df, fig_location=None, show_figure=False):
    pass


if __name__ == '__main__':
    df = get_dataframe()
    plot_conseq(df, show_figure=True)
