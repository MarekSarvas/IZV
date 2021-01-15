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
    clean_df = df[['region', 'p10', 'p12', 'p13a', 'p13b', 'p13c', 'p16', 'p18', 'p19', 'p5a']].dropna().copy()
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
def severity_wrt_cause(df, accidents, region='CZ', save_fig=None, show_fig=False):
    """Severity of injuries in car accidents w.r.t. accident cause.
    
    Show number of injured people for each severity level of injuries in car accidents with respect to cause of accident.
    Injuries could be: light injuries, severe injuries, death. Plot as barplot for each accident cause with hue representing level
    of injuries.
    """
    df = select_region(df, region)
    
    sev_df = pd.DataFrame({ 'cause': df['p12'], 'mrtvy': df['p13a'], 'tazko_zraneny': df['p13b'], 'lahko_zraneny': df['p13c']})
    cause_labels = {'1':'nezavineny_vodicom', '2': 'neprimerana_rychlost', '3': 'nespravne_predbiehanie', '4': 'nedanie_prednosti_v_jazde', 
                    '5': 'nespravny_sposob_jazdy', '6': 'technicka_zavada'}
    

    # adjust values of accident cause to index cause labels
    sev_df['cause'] = sev_df['cause'].apply(lambda x: cause_labels[str(x//100)])

    # melt to get severity into one column
    cause_df = pd.melt(sev_df, id_vars=['cause'], var_name='severity')

    cause_df = cause_df.groupby(['cause', 'severity']).agg(people=('value','sum'), accidents=('value', 'count')).reset_index()
    
    # total number of injured people for every accident cause
    total_injured = cause_df.groupby(['cause']).people.agg('sum').reset_index()
    total_injured = pd.concat([total_injured]*3, ignore_index=True).sort_values(by='cause').reset_index()

    
    # percent of people injured per accident
    cause_df['sev_acc_percent'] = (cause_df.people/cause_df.accidents)*100

    # percent of severity per injured person
    cause_df['sev_inj_percent'] = cause_df['people'].div(total_injured.people, axis=0)*100
    
    

    # print info
    p_injured = cause_df[cause_df['cause'] != 'nezavineny_vodicom'].people.sum()
    print('Počet zranených ľudí pri nehode spôsobenej vodičom {}(pri {:2.4}% nehod)'.format(p_injured, (p_injured/accidents)*100))
    print('Počet usmrtených ľudí pri nehode spôsobenej vodičom {}'.format(cause_df[(cause_df['cause'] != 'nezavineny_vodicom') & (cause_df['severity'] == 'mrtvy')].people.sum()))
    print_table(cause_df) 
    
    # setup plot
    fig, ax = plt.subplots(1, 1)
    fig.set_figwidth(10)
    fig.set_figheight(6)
    fig.suptitle(f'Následky nehôd v {region} spôsobených rôznymi príčinami')

    # create pallete
    c_pallet = sns.color_palette("mako", n_colors=3)
    
    # add 1 because of log scale(later subtracted)
    cause_df['people'] = cause_df['people']+1
    sns.barplot(ax=ax, x="cause", y="people", hue="severity", data=cause_df, palette=c_pallet, log=True)
    
    # annotate bars in plot
    for p in ax.patches:
        ax.annotate(int(p.get_height()-1), xy=(p.xy[0]+p.get_width()/2, p.get_y()+p.get_height()), fontsize=6, ha='center')
    
    # create legend
    labels = ['usmrtení', 'tažko zranení', 'ľahko zranení']
    h, l = ax.get_legend_handles_labels()
    legend = ax.legend(h, labels, title="Závažnosť zranení",loc='upper right', fontsize=10, frameon=False)
    plt.setp(legend.get_title(),fontsize=10)
   

    # set titles, labels and adjust sizes
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)

    ax.set_ylabel('Počet zranených ľudí', fontsize=10)
    ax.set_xlabel('', fontsize=0)
    ax.tick_params(axis="x", labelsize=10)
    ax.tick_params(axis="y", labelsize=10)
   
    ax.minorticks_off()
    plt.setp(ax.get_xticklabels(), rotation=25)

    fig.subplots_adjust(bottom=0.2)

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
    caused_by_labels = {'1':'vodičom motor. vozdila', '2': 'vodičom nemotor. vozdila', '3': 'chodcom', '4': 'zverou', '5': 'iným účastníkom provozu', 
                        '6': 'závadou komunikácie', '7': 'závadou vozidla', '0': 'iné'}
    
    # sort by number of accidents
    caused_by_df = caused_by_df.sort_values(['accidents'], ascending=False).reset_index(drop=True)
    # create column with percent participation in all accidents
    caused_by_df['percent'] = (caused_by_df.accidents/caused_by_df.accidents.sum())*100

    # print values used in report
    print(f'Celkovy pocet nehod v {region}: {caused_by_df.accidents.sum()}')
    print('Počet nehôd zavinených šoférom motor. vozdila: {:2.4}%({})'.format(caused_by_df[caused_by_df.caused_by == 1].percent.tolist()[0], int(caused_by_df[caused_by_df.caused_by == 1].accidents.tolist()[0])))
    print('Počet nehôd zavinených šoférom nemotor. vozdila: {:2.4}%({})'.format(caused_by_df[caused_by_df.caused_by == 2].percent.tolist()[0], int(caused_by_df[caused_by_df.caused_by == 2].accidents.tolist()[0])))
    print('Počet nehôd zavinených zverou: {:2.4}%({})'.format(caused_by_df[caused_by_df.caused_by == 3].percent.tolist()[0], int(caused_by_df[caused_by_df.caused_by == 3].accidents.tolist()[0])))
    
    # change values to labels
    caused_by_df['caused_by'] = caused_by_df['caused_by'].apply(lambda x: caused_by_labels[str(x)])
    
    # if you want to plot
    if save_fig is not None or show_fig == True:
        # plot graph
        fig, ax = plt.subplots(1, 1, figsize=(12, 7))
        fig.subplots_adjust(left=0.17)  # adjust space between figure title and first subplot
        fig.suptitle('Počet nehôd vzhľadom na vinníka')
        
        # seaborn style
        
        c_pallet = sns.color_palette("mako", n_colors=len(caused_by_labels))
        # plot number of accidents w.r.t. who caused them
        sns.barplot(ax=ax, y="caused_by", x="accidents", data=caused_by_df, palette=c_pallet, log=True)
        # annotate each bar with number of accidents
        for p in ax.patches:
            ax.annotate(int(p.get_width()), xy=(p.get_width()+p.get_width()/5, p.xy[1]+p.get_height()/2), fontsize=7, ha='center')

        #ax.title.set_text(titles[i])
        ax.set(ylabel='Zavinenie', xlabel='Počet nehôd')
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        plt.setp(ax.get_yticklabels(), rotation=30, fontsize=7)
        plt.minorticks_off()

        if save_fig is not None:
            plt.savefig(save_fig)
        if show_fig:
            plt.show()
    
    return caused_by_df.accidents.sum() # number of

if __name__ == '__main__':
    df = pd.read_pickle("accidents.pkl.gz")
    df = clean_data(df)
    accidents = accidents_cause(df, region='JHM')
    severity_wrt_cause(df, accidents, save_fig='figures/fig.png', show_fig=True, region='JHM')
