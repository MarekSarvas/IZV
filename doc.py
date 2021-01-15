#!/usr/bin/python3.8
# coding=utf-8
"""
Author: Marek Sarvas
School: VUT FIT
Project: IZV
Description: Script for car crash data represantation.
"""

import numpy as np
import pandas as pd
import seaborn as sns
import scipy.stats as st
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker


def clean_data(df):
    """Select only columns with data necessary for this task, drop rows with None value.
    Selected columns are:   p10 - accident caused by
                            p12 - main cause of accident
                            p13 - consequences
                            p16 - surface condition
                            p18 - weather conditions
                            p19 - visibility
                            region
    """
    clean_df = df[['region', 'p10', 'p12', 'p13a', 'p13b', 'p13c', 'p16', 'p18', 'p19']].dropna().copy()
    return clean_df


def select_region(df, region='CZ'):
    """Select chosen region, if region is not given return same dataframe"""
    if region == 'CZ':
        return df
    reg_df = df[df.region == region].copy()
    return reg_df

def print_table(df):
    print(df.to_latex(index=False))
    

# severity by accident cause
def severity_wrt_cause(df, region='CZ', save_fig=None, show_fig=False):
    """Severity of injuries in car accidents w.r.t. accident cause.
    
    Show number of injured people for each severity level of injuries in car accidents with respect to cause of accident.
    Injuries could be: light injuries, severe injuries, death. Plot as barplot for each accident cause with hue representing level
    of injuries.
    """
    df = select_region(df, region)
    
    sev_df = pd.DataFrame({ 'cause': df['p12'], 'dead': df['p13a'], 'severely_injured': df['p13b'], 'lightly_injured': df['p13c']})
    cause_labels = {'1':'nezavineny vodicom', '2': 'neprimerana rychlost', '3': 'nespravne predbiehanie', '4': 'nedanie prednosti v jazde', 
                    '5': 'nespravny sposob jazdy', '6': 'technicka zavada'}
    

    # adjust values of accident cause to index cause labels
    sev_df['cause'] = sev_df['cause'].apply(lambda x: cause_labels[str(x//100)])
    print(sev_df)
    # melt to get severity into one column
    cause_df = pd.melt(sev_df, id_vars=['cause'], var_name='severity')
   
    #cause_df = cause_df[cause_df['value'] != 0]
    print()
    tmp = cause_df.groupby(['cause', 'severity']).agg(people=('value','sum'), accidents=('value', 'count')).reset_index()
    tmp['percent'] = (tmp.people/tmp.accidents)*100
    print_table(tmp)
    cause_df = cause_df.groupby(['cause', 'severity']).value.agg('sum').reset_index(name='people')
    #tmp = cause_df.groupby(['cause', 'severity']).agg(accidents=('value','sum'), people=('value', 'count')).reset_index()
    print(cause_df)
   
    # setup plot
    fig, ax = plt.subplots(1, 1)
    fig.set_figwidth(10)
    fig.set_figheight(6)
    fig.suptitle(f'Nasledky nehod v {region} sposobenych roznymi pricinami')
    fig.tight_layout(pad=3.0)

    # create pallete
    c_pallet = sns.color_palette("mako", n_colors=3)
    
    # add 1 because of log scale(later subtracted)
    cause_df['people'] = cause_df['people']+1
    sns.barplot(ax=ax, x="cause", y="people", hue="severity", data=tmp, palette=c_pallet, log=True)
    
    # annotate bars in plot
    for p in ax.patches:
        ax.annotate(int(p.get_height()-1), xy=(p.xy[0]+p.get_width()/2, p.get_y()+p.get_height()), fontsize=6, ha='center')
    
    # create legend
    labels = ['usmrteny', 'tazko zraneny', 'lahko zraneny']
    h, l = ax.get_legend_handles_labels()
    legend = ax.legend(h, labels, title="Zavaznost zraneni",loc='upper right', fontsize=6, frameon=False)
    plt.setp(legend.get_title(),fontsize=8)
   

    # set titles, labels and adjust sizes
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.set_xlabel('pricina nehody', fontsize=8)
    ax.set_ylabel('pocet zranenych ludi', fontsize=8)
    ax.tick_params(axis="x", labelsize=6)
    ax.tick_params(axis="y", labelsize=6)
    ax.minorticks_off()

    if save_fig is not None:
        plt.savefig(save_fig)
    if show_fig:
        plt.show()


def accidents_cause(df, region='CZ', save_fig=None, show_fig=False):
    df = select_region(df, region)

    # create  needed dataframe with values grouped by cause of accident
    acc_df = pd.DataFrame({'caused_by': df['p10'], 'cause': df['p12'], 'dead': df['p13a'], 'heavily_injured': df['p13b'], 'lightly_injured': df['p13c']})
    caused_by_df = acc_df.groupby('caused_by').cause.agg('count').to_frame('accidents').reset_index()

    # change "cause_by" column lables to text description
    caused_by_labels = {'1':'vodicom motor. vozdila', '2': 'vodicom nemotor. vozdila', '3': 'chodcom', '4': 'zverou', '5': 'inym ucastnikom provozu', 
                        '6': 'zavadou komunikacie', '7': 'zavadou vozidla', '0': 'ine'}
    
    caused_by_df['caused_by'] = caused_by_df['caused_by'].apply(lambda x: caused_by_labels[str(x)])
    
    print(caused_by_df)

    fig, ax = plt.subplots(1, 1, figsize=(12, 7))
    fig.subplots_adjust(left=0.17)  # adjust space between figure title and first subplot
    fig.suptitle('Následky nehôd v jednotlivých regiónoch')
    
    # seaborn style
    sns.set_style("darkgrid")
    c_pallet = sns.color_palette("mako", n_colors=len(caused_by_labels))

    caused_by_df = caused_by_df.sort_values(['accidents'], ascending=False).reset_index(drop=True)

    # plot number of accidents w.r.t. who caused them
    sns.barplot(ax=ax, y="caused_by", x="accidents", data=caused_by_df, palette=c_pallet, log=True)

    # annotate each bar with number of accidents
    for p in ax.patches:
        ax.annotate(int(p.get_width()), xy=(p.get_width()+p.get_width()/5, p.xy[1]+p.get_height()/2), fontsize=7, ha='center')
   
    #ax.title.set_text(titles[i])
    ax.set(ylabel='Zavinenie', xlabel='Pocet nehod')
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    plt.setp(ax.get_yticklabels(), rotation=30, fontsize=7)
    plt.minorticks_off()

    if save_fig is not None:
        plt.savefig(save_fig)
    if show_fig:
        plt.show()


# number of accident w.r.t. weather, visibility, surface conditions
def weather_accidents(df, region='CZ', save_fig=None, show_fig=False):
    df = select_region(df, region)
    print(df)
    w_df = pd.DataFrame({'caused_by': df['p10'], 'cause': df['p12'], 'visibility': df['p19'], 'weather': df['p18'], 'dead': df['p13a'], 'heavily_injured': df['p13b'], 'lightly_injured': df['p13c']})
    print(w_df.weather.min())







    if save_fig is not None:
        plt.savefig(save_fig)
    if show_fig:
        plt.show()


if __name__ == '__main__':
    df = pd.read_pickle("accidents.pkl.gz")
    df = clean_data(df)
    severity_wrt_cause(df, save_fig='figures/fig.png', show_fig=True)
    #accidents_cause(df, show_fig=True, save_fig='figures/priciny_nehod.png')
    #accidents_wrt_weather(df)
    #accidents_wrt_weather(df, save_fig='figures/pocasie.png', show_fig=True)