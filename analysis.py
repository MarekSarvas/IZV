#!/usr/bin/env python3.8
# coding=utf-8

"""
Author: Marek Sarvas
School: VUT FIT
Project: IZV
Description: Script for creating graph of car crashes in czech republic for given years and regions.
"""
from textwrap import wrap

from matplotlib import pyplot as plt
import pandas as pd
import seaborn as sns
import numpy as np
import os
# muzete pridat libovolnou zakladni knihovnu ci knihovnu predstavenou na prednaskach
# dalsi knihovny pak na dotaz

B_to_MB = 1048576

to_category = ['a', 'b', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'n', 'o', 'p', 'q', 'r', 's', 't']
to_float = ['d', 'e', 'f', 'g']
to_int8 = ['p5a', 'p6', 'p7', 'p8', 'p9', 'p10', 'p11', 'p15', 'p16', 'p18', 'p19', 'p20', 'p21', 'p22', 'p23', 'p24',
           'p27', 'p28', 'p49', 'p50a', 'p50b', 'p51', 'p55a', 'p57', 'p58']

# Ukol 1: nacteni dat
def get_dataframe(filename: str, verbose: bool = False) -> pd.DataFrame:
    """ Loads zipped dataframe and lower its size by changing to better data types.

        :param filename: path to stored dataframe
        :param verbose: if true print size of dataframe
        :return: pandas DataFrame with changed types of columns
        """
    data = pd.read_pickle(filename, compression="gzip")

    if verbose:
        print(f'orig_size={round(data.memory_usage(index=False, deep=True).sum() / B_to_MB, 2)} MB')

    # change types for specific columns
    for col in to_category:
        data[col] = data[col].astype('category')
    for col in to_float:
        data[col] = data[col].astype('float64')
    for col in to_int8:
        data[col] = data[col].astype('int8')

    # create datetime column from string
    data.insert(0, column='date', value=data['p2a'].astype('datetime64'))

    if verbose:
        print(f'new_size={round(data.memory_usage(index=False, deep=True).sum() / B_to_MB, 2)} MB')

    return data

# Ukol 2: následky nehod v jednotlivých regionech
def plot_conseq(df: pd.DataFrame, fig_location: str = None,
                show_figure: bool = False):
    """ Plots crash consequences for every region based on theirseverity.

        :param df: pandas DataFrame
        :param fig_location: location where the figure will be saved, if None figure is not saved
        :param show_figure: if true show figure
        """
    # create data frames for each subplot
    p13a = df[['region', 'p13a']].groupby('region').agg(np.sum).reset_index()
    p13b = df[['region', 'p13b']].groupby('region').agg(np.sum).reset_index()
    p13c = df[['region', 'p13c']].groupby('region').agg(np.sum).reset_index()
    crashes = df['region'].value_counts().sort_values(ascending=False)

    titles = list(['Usmrtených osôb', 'Ťažko zranených osôb', 'Ľahko zranených osôb', 'Celkový  počet nehôd'])
    # main figure settings
    sns.set_style("darkgrid")
    fig, axs = plt.subplots(4, 1)

    fig.set_figwidth(8)
    fig.set_figheight(10)
    fig.tight_layout()
    fig.subplots_adjust(top=0.89)  # adjust space between figure title and first subplot
    fig.suptitle('Následky nehôd v jednotlivých regiónoch')

    c_pallet = sns.color_palette("mako", n_colors=14)

    # plot each data frame as bar into corresponding subplots
    sns.barplot(ax=axs[0], x="region", y="p13a", data=p13a, order=crashes.index, palette=c_pallet)
    sns.barplot(ax=axs[1], x="region", y="p13b", data=p13b, order=crashes.index, palette=c_pallet)
    sns.barplot(ax=axs[2], x="region", y="p13c", data=p13c, order=crashes.index, palette=c_pallet)
    sns.barplot(ax=axs[3], x=crashes.index, y=crashes.values, palette=c_pallet)

    # set titles, adjust labels and borders
    for i in range(4):
        axs[i].title.set_text(titles[i])
        axs[i].set(xlabel=None, ylabel='pocet')
        axs[i].spines['right'].set_visible(False)
        axs[i].spines['top'].set_visible(False)

    fig.tight_layout(pad=2.0)

    if fig_location is not None:
        plt.savefig(f'{fig_location}', bbox_inches="tight")

    if show_figure:
        plt.show()

# Ukol3: příčina nehody a škoda
def plot_damage(df: pd.DataFrame, fig_location: str = None,
                show_figure: bool = False):
    """ Plots damage cost of accidents in 4 regions w.r.t. cause of accident.

        :param df: pandas DataFrame
        :param fig_location: location where the figure will be saved, if None figure is not saved
        :param show_figure: if true show figure
        """
    my_regions = ['ULK', 'JHM', 'HKK', 'VYS']  # regions to plot

    data_tmp = df[['region', 'p12', 'p53']]  # get only needed columns

    # accident cause labels
    labels = ['nezavinená vodičom', 'neprimeraná rýchlosť jazdy', 'nesprávne predbiehanie',
              'nedanie prednosti v jazde',
              'nesprávny spôsob jazdy', 'technická závada vozidla']

    # copy the data frame, otherwise loc causes a warning
    data = data_tmp.copy()
    data['p53'] = data['p53'].div(10)
    # create category data for accident cause and change p12 column to it
    data.loc[:, 'p12'] = pd.cut(data_tmp['p12'], [99, 200, 300, 400, 500, 600, float('inf')], labels=labels)

    # segment data into bins based on damage costs
    p53 = pd.cut(data['p53'], [-float('inf'), 50, 200, 500, 1000, float('inf')],
                 labels=['< 50', '50 - 200', '200 - 500',
                         '500 - 1000', '1000 >'])

    # insert segmented damage costs into "dmg_cost" column
    data.insert(0, column='dmg_cost', value=p53)

    sns.set_style("darkgrid")

    # count number of  accidents w.r.t. region, damage costs, cause of accident and add it as column "count"
    data = data.groupby(['region', 'dmg_cost', 'p12'])['p53'].count().reset_index(name='count')
    fig, axs = plt.subplots(2, 2)

    fig.set_figwidth(10)
    fig.set_figheight(6)
    fig.suptitle('Príčiny nehôd v krajoch')
    fig.tight_layout(pad=3.0)

    c_pallet = sns.color_palette("mako", n_colors=len(labels))

    # plot each region of my regions into corresponding subplot
    for i, ax in enumerate(axs.flatten()):
        region_data = data[data['region'] == my_regions[i]]  # get region

        sns.barplot(ax=ax, x="dmg_cost", y="count", hue="p12", data=region_data, log=True, palette=c_pallet)
        ax.legend().set_visible(False)  # hide legends inside plots

        # set titles, labels and adjust sizes
        ax.title.set_text(my_regions[i])
        ax.set_xlabel('Škoda [tisíc Kč]', fontsize=8)
        ax.set_ylabel('Počet', fontsize=8)

        ax.tick_params(axis="x", labelsize=6)
        ax.tick_params(axis="y", labelsize=6)

    # move subplots to make space for legend, add legend
    fig.subplots_adjust(right=0.8)
    handles, labels = axs[0, 0].get_legend_handles_labels()  # params for legend
    fig.legend(handles, labels, loc='center left', bbox_to_anchor=(0.80, 0.5), ncol=1, title='Príčiny nehôd',
               fontsize=8,
               fancybox=False, shadow=False, borderpad=None, frameon=False)

    if fig_location is not None:
        plt.savefig(f'{fig_location}', bbox_inches="tight")

    if show_figure:
        plt.show()

# Ukol 4: povrch vozovky
def plot_surface(df: pd.DataFrame, fig_location: str = None,
                 show_figure: bool = False):
    """  Visualize number of accidents w.r.t. road surface in 4 regions for every month in years.

        :param df: pandas DataFrame
        :param fig_location: location where the figure will be saved, if None figure is not saved
        :param show_figure: if true show figure
        """
    my_regions = ['ULK', 'JHM', 'HKK', 'VYS']  # regions to plot

    # labels for numeric values of road surface
    p16_to_string = {1: 'suchý neznečistený', 2: 'suchý znečistený', 3: 'mokrý',
                     4: 'blato', 5: 'poľadovice, najazdený sneh - posypané',
                     6: 'poľadovice, najazdený sneh - neposypané',
                     7: 'rozliaty olej, nafta apod.', 8: 'súvislý sneh',
                     9: 'náhla zmena stavu', 0: 'iný stav'}

    data = df[['region', 'date', 'p16']]  # get needed columns

    # copy the data frame, otherwise loc causes a warning
    data_copy = data.copy()
    data_copy.loc[:, 'date'] = pd.to_datetime(data["date"].dt.strftime('%Y-%m'))  # remove days

    # crosstab indexes are region and date,  columns are road surface
    ctab_data = pd.crosstab([data_copy.region, data_copy.date], data_copy.p16).rename(columns=p16_to_string)

    # stack data w.r.t. road surface(p16) -> values are in column "count"
    stacked = ctab_data.stack()
    stacked.name = 'count'
    stacked = stacked.reset_index()

    # main figure settings
    sns.set_style("darkgrid")
    fig, axs = plt.subplots(2, 2, sharex=True, sharey=True)

    fig.set_figwidth(11)
    fig.set_figheight(6)
    fig.suptitle('Stav vozovky v krajoch v jednotlivých mesiacoch')

    # plot lines w.r.t. time, number of crashes and road surface into subplots for each region
    for i, ax in enumerate(axs.flatten()):
        region_data = stacked[stacked['region'] == my_regions[i]]  # get region

        sns.lineplot(ax=ax, x="date", y="count", hue='p16', data=region_data)
        ax.legend().set_visible(False)  # hide legends inside plots

        # set titles, labels and adjust sizes
        ax.title.set_text(my_regions[i])
        ax.set(xlabel='Dátum vzniku nehody', ylabel='Počet nehôd')

    # move subplots to make space for legend, add legend
    fig.subplots_adjust(right=0.80)
    handles, labels = axs[0, 0].get_legend_handles_labels()
    # wraps long legend labels
    labels = ['\n'.join(wrap(l, 30)) for l in labels]
    fig.legend(handles, labels, loc='center left', bbox_to_anchor=(0.8, 0.5), ncol=1, title='Stav vozovky', fontsize=8,
               fancybox=False, shadow=False, borderpad=None, frameon=False)

    if fig_location is not None:
        plt.savefig(f'{fig_location}')

    if show_figure:
        plt.show()


if __name__ == "__main__":
    pass
    # zde je ukazka pouziti, tuto cast muzete modifikovat podle libosti
    # skript nebude pri testovani pousten primo, ale budou volany konkreni ¨
    # funkce.
    df = get_dataframe("accidents.pkl.gz")
    plot_conseq(df, fig_location="01_nasledky.png", show_figure=True)
    plot_damage(df, "02_priciny.png", True)
    plot_surface(df, "03_stav.png", True)
