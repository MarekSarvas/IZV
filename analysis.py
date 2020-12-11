"""
Author: Marek Sarvas
School: VUT FIT
Project: IZV
Description: Script for creating graph of car crashes in czech republic for given years and regions.
"""

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import gzip
import pickle

B_to_MB = 1048576

to_category = ['a', 'b', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'n', 'o', 'p', 'q', 'r', 's', 't']
to_float = ['d', 'e', 'f', 'g']
to_int8 = ['p5a', 'p6', 'p7', 'p8', 'p9', 'p10', 'p11', 'p15', 'p16', 'p18', 'p19', 'p20', 'p21', 'p22', 'p23', 'p24',
           'p27', 'p28', 'p49', 'p50a', 'p50b', 'p51', 'p55a', 'p57', 'p58']


def get_dataframe(filename="accidents.pkl.gz", verbose=False):
    with gzip.open(f'{filename}', 'rb') as f:
        data = pickle.load(f)
        data = pd.DataFrame(data)

    if verbose:
        print(f'orig_size={round(data.memory_usage(index=False, deep=True).sum() / B_to_MB, 2)} MB')

    data.insert(0, column='date', value=data['p2a'].astype('datetime64'))

    for col in to_category:
        data[col] = data[col].astype('category')
    for col in to_float:
        data[col] = data[col].astype('float64')
    for col in to_int8:
        data[col] = data[col].astype('int8')

    if verbose:
        print(f'new_size={round(data.memory_usage(index=False, deep=True).sum() / B_to_MB, 2)} MB')

    return data


def plot_conseq(df, fig_location=None, show_figure=False):
    pass


def plot_damage(df, fig_location=None, show_figure=False):
    pass


def plot_surface(df, fig_location=None, show_figure=False):
    pass


if __name__ == '__main__':
    df = get_dataframe(verbose=True)
    plot_conseq(df, show_figure=True)
