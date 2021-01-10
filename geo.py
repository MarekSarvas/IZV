#!/usr/bin/python3.8
# coding=utf-8
import pandas as pd
import geopandas
import matplotlib.pyplot as plt
import contextily as ctx
import sklearn.cluster
import numpy as np
# muzeze pridat vlastni knihovny



def make_geo(df: pd.DataFrame) -> geopandas.GeoDataFrame:
    """ Konvertovani dataframe do geopandas.GeoDataFrame se spravnym kodovani"""
    # select region
    df_reg = df[df['region'] == 'JHM']

    # drop rows with unknown coordinates
    df_dropped = df_reg.dropna(how='any', subset=['d', 'e']).copy()
    
    # create geodataframe
    gdf = geopandas.GeoDataFrame(df_dropped,geometry=geopandas.points_from_xy(df_dropped["d"], df_dropped["e"]),crs="EPSG:5514")

    return gdf

def plot_geo(gdf: geopandas.GeoDataFrame, fig_location: str = None, show_figure: bool = False):
    """ Vykresleni grafu s dvemi podgrafy podle lokality nehody """
    
    # create subplots
    fig, axs = plt.subplots(1, 2, figsize=(20, 15), sharex=True, sharey=True) ###
    
    # plot accidents in city and outside city
    gdf[gdf["p5a"] == 1].plot(ax=axs[0], markersize=1, color='red')
    gdf[gdf["p5a"] == 2].plot(ax=axs[1], markersize=1, color='green')
    fig.tight_layout()

    # for each subplot
    for i in range(2):
        # set ticks
        axs[i].set(xlabel=None, ylabel=None)
        axs[i].tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
        
        # set basemap
        ctx.add_basemap(axs[i], crs=gdf.crs.to_string(), source=ctx.providers.Stamen.TonerLite)

    # set titles
    axs[0].title.set_text('Nehody v JHM: v obci')
    axs[1].title.set_text('Nehody v JHM: mimo obci')
    
    if fig_location is not None:
        plt.savefig(fig_location)
    if show_figure:
        plt.show()


def plot_cluster(gdf: geopandas.GeoDataFrame, fig_location: str = None, show_figure: bool = False):
    """ Vykresleni grafu s lokalitou vsech nehod v kraji shlukovanych do clusteru """
    # create figures
    fig = plt.figure(figsize=(20, 8))
    ax = plt.gca()
    
    gdf_c = gdf.to_crs("EPSG:5514") # spravny system
    gdf_c = gdf_c.set_geometry(gdf_c.centroid).to_crs(epsg=3857)
    
    # plot all accidents
    gdf_c.plot(ax=ax, color='grey', markersize=0.2)
    
    # get coordinates
    coords = np.dstack([gdf_c.geometry.x, gdf_c.geometry.y]).reshape(-1, 2)
    
    # create clusters
    db = sklearn.cluster.MiniBatchKMeans(n_clusters=15).fit(coords)

    gdf4 = gdf_c.copy()
    gdf4["cluster"] = db.labels_
    
    # group by clusters, number of accidents into 'cnt' column
    gdf4 = gdf4.dissolve(by="cluster", aggfunc={"p1": "count"}).rename(columns=dict(p1="cnt"))

    gdf_coords = geopandas.GeoDataFrame(geometry=geopandas.points_from_xy(db.cluster_centers_[:, 0], db.cluster_centers_[:, 1]))
    gdf5 = gdf4.merge(gdf_coords, left_on="cluster", right_index=True).set_geometry("geometry_y")

    # plot clusters and legend
    gdf5.plot(ax=ax, markersize=gdf5["cnt"]/1e1, legend=True, column="cnt", alpha=0.5, vmin=0, vmax=gdf5['cnt'].max(), legend_kwds={'label': 'Pocet nehod'})
    
    # add basemap
    ctx.add_basemap(ax, crs="epsg:3857", source=ctx.providers.Stamen.TonerLite) ###
    
    # set ticks and title
    ax.set(xlabel=None, ylabel=None)
    ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
    ax.title.set_text('Nehody v JHM kraji')
    
    
    if fig_location is not None:
        plt.savefig(fig_location)
    if show_figure:
        plt.show()


if __name__ == "__main__":
    # zde muzete delat libovolne modifikace
    gdf = make_geo(pd.read_pickle("accidents.pkl.gz"))
    #plot_geo(gdf, "geo1.png", show_figure=True)
    plot_cluster(gdf, "geo2.png", True)

