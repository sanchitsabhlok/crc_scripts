from copy import copy
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import patheffects
from mpl_toolkits.axes_grid1 import make_axes_locatable

from . import config
from .utils import plot_utils
from .utils import math_utils
from .utils import data_calc_utils as calc


class Figure(object):
    """ Wrapper for matplotlib figures to have them fit my personal tastes. """
    
    def __init__(self, plot_num, **kwargs):
        """
        Parameters
        ----------
        plot_type : str
            The type of plot you want to make. Supported formats are (basic, projection).
        plot_num : int
            Number of plots in this figure.
        """
        self.plot_num = plot_num
        self.fig, self.axes, self.dims = plot_utils.setup_figure(plot_num, **kwargs)

        # Keep track of Artists for plotted data in case you want to remove it later
        self.axis_artists = [[] for i in range(self.plot_num)]
        # Keeps track of what handles and labels are already included in legends for each axis
        self.axis_legend_handles_labels = [{} for i in range(self.plot_num)]
        self.outside_legend_handles_labels = {}


    def set_axes(self, x_props, y_props, axes_kwargs=None):
        """
        Set up all axes in figure given the properties you want you plot on the x and y axis for each. 
        Can also give more arguements for each axis such as setting log/linear and the limits.

        Parameters
        ----------
        x_props : list
            List of properties for each x axis.
        y_props : list
            List of properties for each y axis.
        axes_kwargs : list
            List of dictionaries containing arguements for plot_utils.setup_axi()
        """


        if axes_kwargs is None: 
            axes_kwargs = [{}]*self.num_plots
        if (self.plot_num>1) and (len(x_props)!=len(self.plot_num) or len(y_props)!=len(self.plot_num)):
            print("Number of axes labels needs to match number of axes for set_axes().")
            return
        for i in range(self.num_plots):
            self.set_axis(self.axes[i], x_props[i], y_props[i], **axes_kwargs[i])
    

    def set_axis(self, axis_num, x_prop, y_prop, twin_time_axis = True, **kwargs):
        """
        Set specific axis in figure given the properties you want you plot on the x and y axis 
        Can also give more arguements for axis such as setting log/linear and the limits.

        Parameters
        ----------
        axis_num : int
            Axis number. Starts at 0 and moves left to right and up to down. i.e [[0,1],[2,3]]
        x_prop : string
            Property for each x axis.
        y_prop : string
            Property for each y axis.
        axes_kwargs : dict
            Additional arguements for plot_utils.setup_axis()
        """
        
        plot_utils.setup_axis(self.axes[axis_num], x_prop, y_prop, **kwargs)
        # If we have a time/redshift axis, create a twin time/redshift axis
        if twin_time_axis and x_prop in ['redshift','time','redshift_plus_1']:
            # Only want extra labels on the top axis
            tick_labels=False
            if axis_num < self.dims[1]:
                tick_labels=True
            plot_utils.make_axis_secondary_time(self.axes[axis_num], x_prop, snapshot=None, tick_labels=tick_labels)


    def save(self, filename, **kwargs):
        self.fig.savefig(filename, bbox_inches='tight', **kwargs)


    def show(self):
        return self.fig
    
    
    def clear_axis(self,axis_num):
        if (len(self.axis_artists[axis_num]) > 0):
            for artist in self.axis_artists[axis_num]:
                artist.remove()
            self.axis_artists[axis_num]=[]

    
    def plot_line_data(self, axis_num, x_data, y_data, y_std=None, std_kwargs={}, **kwargs):
        default_kwargs = {
            'color': config.BASE_COLOR, 
            'linestyle': config.BASE_LINESTYLE, 
            'linewidth': config.BASE_LINEWIDTH, 
            'zorder': 3}
        
        # If std/errors for the y values are given then we want to plot them as shaded regions with the lines
        std_bars = True if y_std is not None else False

        for kwarg in default_kwargs:
            if kwarg not in kwargs:
                kwargs[kwarg] = default_kwargs[kwarg]

        axis = self.axes[axis_num]
        sc = axis.plot(x_data, y_data, **kwargs)
        self.axis_artists[axis_num] += sc

        if std_bars:
            default_std_kwargs = {
            'color': kwargs['color'], 
            'zorder': kwargs['zorder']-1,
            'alpha': 0.3}

            for kwarg in default_std_kwargs:
                if kwarg not in std_kwargs:
                    std_kwargs[kwarg] = default_std_kwargs[kwarg]

            self.plot_shaded_region(axis_num, x_data, np.array(y_std)[:,0], np.array(y_std)[:,1], **std_kwargs)


    def plot_errorbar_data(self, axis_num, x_data, y_data, y_err=None, x_err=None, **kwargs):
        default_kwargs = {
            'fmt': 'o', 
            'c': config.BASE_COLOR,
            'elinewidth': config.BASE_ELINEWIDTH, 
            'ms': config.BASE_MARKERSIZE**0.5, 
            'mew': config.BASE_ELINEWIDTH,
            'mfc': 'xkcd:white',
            'zorder': 3,
            'alpha': 1}
        
        for kwarg in default_kwargs:
            if kwarg not in kwargs:
                kwargs[kwarg] = default_kwargs[kwarg]
        
        axis = self.axes[axis_num]
        eb = axis.errorbar(x_data, y_data, yerr=y_err, xerr=x_err, **kwargs)
        self.axis_artists[axis_num] += [eb]
    

    def plot_shaded_region(self, axis_num, x_data, y1_data, y2_data, **kwargs):
        default_kwargs = {
            'color': config.BASE_COLOR, 
            'alpha': 0.3, 
            'zorder': 1}
        
        for kwarg in default_kwargs:
            if kwarg not in kwargs:
                kwargs[kwarg] = default_kwargs[kwarg]

        axis = self.axes[axis_num]
        fb = axis.fill_between(x_data, y1_data, y2_data, **kwargs)
        self.axis_artists[axis_num] += [fb]
    

    def plot_polygon(self, axis_num, x_data, y_data, **kwargs):
        default_kwargs = {
            'color': config.BASE_COLOR, 
            'alpha': 0.3, 
            'zorder': 1}
        
        for kwarg in default_kwargs:
            if kwarg not in kwargs:
                kwargs[kwarg] = default_kwargs[kwarg]

        axis = self.axes[axis_num]
        fill = axis.fill(x_data, y_data, **kwargs)
        self.axis_artists[axis_num] += [fill]
        return fill
    



    def plot_scatter_data(self, axis_num, x_data, y_data, **kwargs):
        default_kwargs = {
            'c': config.BASE_COLOR, 
            'marker': 'o', 
            's': config.BASE_MARKERSIZE, 
            'zorder': 3}
        
        for kwarg in default_kwargs:
            if kwarg not in kwargs:
                kwargs[kwarg] = default_kwargs[kwarg]

        axis = self.axes[axis_num]
        sc = axis.scatter(x_data, y_data, **kwargs)
        self.axis_artists[axis_num] += [sc]

    def plot_histogram(self, axis_num, z_prop, X, Y, Z, cmap='magma', z_lim=None, z_log=None, label=None):
     

        z_limits = z_lim if z_lim is not None else config.get_prop_limits(z_prop)
        z_log = z_log if z_log is not None else config.get_prop_if_log(z_prop)

        if z_log:
            norm = mpl.colors.LogNorm(vmin=z_limits[0], vmax=z_limits[1], clip=True)
        else:
            norm = mpl.colors.Normalize(vmin=z_limits[0], vmax=z_limits[1], clip=True)

        axis = self.axes[axis_num]
        img = axis.pcolormesh(X, Y, Z, cmap=cmap, norm=norm)
        axis.autoscale('tight')
        self.axis_artists[axis_num] += [img]

        if label!=None:
            axis.text(.95, .95, label, color=config.BASE_COLOR, fontsize=config.EXTRA_LARGE_FONT, ha='right', va='top', transform=axis.transAxes, zorder=4)

    def set_all_legends(self, labels_per_legend=4, max_cols=2, **kwargs):
        default_kwargs = {
            'loc': 'best',
            'fontsize': config.SMALL_FONT,
            'frameon': False}
        
        for kwarg in default_kwargs:
            if kwarg not in kwargs:
                kwargs[kwarg] = default_kwargs[kwarg]

        # Check labels and handles between each axis in turn. Any differences should be added to a new legend in the next axis
        labels_handles = {}
        for i,axis in enumerate(self.axes):
            hands, labs = axis.get_legend_handles_labels()
            new_lh = dict(zip(labs, hands))
            for key in labels_handles.keys(): new_lh.pop(key, 0);
            if len(new_lh) > 0:
                ncol = max_cols if len(new_lh) > labels_per_legend else 1
                # Remove any old legends
                if axis.get_legend() is not None: axis.get_legend().remove()
                axis.legend(new_lh.values(), new_lh.keys(), ncol=ncol,**kwargs)
                self.axis_legend_handles_labels[i] = new_lh
            labels_handles.update(new_lh)
        
    def set_axis_legend(self, axis_num, **kwargs):
        default_kwargs = {
            'loc': 'best',
            'fontsize': config.SMALL_FONT,
            'frameon': False,
            'ncol': 2}

        for kwarg in default_kwargs:
            if kwarg not in kwargs:
                kwargs[kwarg] = default_kwargs[kwarg]

        axis = self.axes[axis_num]
        # Remove existing legend
        if axis.get_legend() is not None: axis.get_legend().remove()
        hands, labs = axis.get_legend_handles_labels()
        # Dictionaries do not have duplicate keys so this effectively gets rid of duplicate legend labels
        new_lh = dict(zip(labs, hands))
        axis.legend(new_lh.values(), new_lh.keys(),**kwargs)
        self.axis_legend_handles_labels[axis_num] = new_lh

    
    def set_outside_legend(self, **kwargs):
        default_kwargs = {
            'loc': 'lower center',
            'bbox_to_anchor': (0.5, 1.07),
            'frameon': False,
            'ncol': 2,
            'borderaxespad': 0,
            'fontsize': config.LARGE_FONT,
            "bbox_transform": self.fig.transFigure}     
        
        for kwarg in default_kwargs:
            if kwarg not in kwargs:
                kwargs[kwarg] = default_kwargs[kwarg]
        # Check for old legends and remove
        legends = [c for c in self.fig.get_children() if isinstance(c, mpl.legend.Legend)]
        if len(legends)>0:
            for legend in legends: legend.remove()
        # Check labels and handles which are already included in axes legends so we only get unique handles and exclude any already in legends within the axis
        axis_labels_handles = {}
        legend_labels_handles = {}
        # Collect all plotted handles and thos included in legends already. Then only include the difference
        for i in range(len(self.axes)):
            axis = self.axes[i]
            hands, labs = axis.get_legend_handles_labels()
            # This also remove duplicate labels
            axis_labels_handles.update(dict(zip(labs, hands)))
            legend_labels_handles.update(self.axis_legend_handles_labels[i])
        for key in legend_labels_handles: axis_labels_handles.pop(key, 0)
        fig_legend = self.fig.legend(axis_labels_handles.values(), axis_labels_handles.keys(), **kwargs)
        self.outside_legend_handles_labels = axis_labels_handles

        ### THIS NO LONGER WORKS FOR SCATTERS WITH COLORMAPS IN NEW VERSION OF MATPLOTLIB 
        # Overide the legend marker colors to all be the same
        # if override_color is not None:
        #     for handle in fig_legend.legend_handles:
        #         handle.set(cmap=None,norm=None,facecolor=None)




    def add_colorbar(self, axis_num, cbar_prop=None, invert_axis=False, no_minor_ticks=False, side='right'):

        # Since we are adding a colorbar lets make sure the plots aren't too close together
        if self.plot_num>1:
            if side in ['right','left']:
                self.fig.subplots_adjust(wspace=mpl.rcParams["figure.subplot.wspace"])
            else:
                self.fig.subplots_adjust(hspace=mpl.rcParams["figure.subplot.hspace"])
        # Find the artist with a colormap, seems to have a specific attribute we can use
        for artist in self.axis_artists[axis_num]:
            if hasattr(artist, 'autoscale_None'):
                mappable = artist; break;
        axis = self.axes[axis_num]
        divider = make_axes_locatable(axis)
        cax = divider.append_axes(side, size="5%", pad=0.0)
        cbar = self.fig.colorbar(mappable,cax=cax,pad=0)
        cbar_label = config.get_prop_label(cbar_prop)
        cbar.ax.set_ylabel(cbar_label, fontsize=config.LARGE_FONT)
        if invert_axis:
            cbar.ax.invert_yaxis()
        if no_minor_ticks:
            cbar.ax.minorticks_off()

    def add_outside_colorbar(self, axis_num=0, cbar_prop=None, invert_axis=False, no_minor_ticks=False):

        # Find the artist with a colormap, seems to have a specific attribute we can use
        for artist in self.axis_artists[axis_num]:
            if hasattr(artist, 'autoscale_None'):
                mappable = artist; break;
        self.fig.subplots_adjust(right=0.9)
        cax = self.fig.add_axes([0.95, 0.1, 0.05, 0.8])
        cbar = self.fig.colorbar(mappable,cax=cax,pad=0)
        cbar_label = config.get_prop_label(cbar_prop)
        cbar.ax.set_ylabel(cbar_label, fontsize=config.LARGE_FONT)
        if invert_axis:
            cbar.ax.invert_yaxis()
        if no_minor_ticks:
            cbar.ax.minorticks_off()
 
    # This is a wrapper for the matplotlib annotate function which is more versatile than the text function
    def add_text(self, axis_num, x, y, text, **kwargs):
        default_kwargs = {
            'color': config.BASE_COLOR,
            'fontsize': config.EXTRA_LARGE_FONT,
            'ha': 'center',
            "va": 'center',
            'xycoords': 'axes fraction'} 

        # Adding outlines to text is not simple so lets make it similar to edges 
        if 'ec' in kwargs:
            if 'ew' not in kwargs:
                kwargs['ew']=0.5*config.BASE_ELINEWIDTH
            kwargs['path_effects']=[patheffects.withStroke(linewidth= kwargs['ew'],
                                                        foreground= kwargs['ec'])]
            kwargs.pop('ec',0);kwargs.pop('ew',0)

        for kwarg in default_kwargs:
            if kwarg not in kwargs:
                kwargs[kwarg] = default_kwargs[kwarg]
                 
        axis=self.axes[axis_num]
        axis.annotate(text,xy=[x,y], **kwargs)


    def add_artist(self, axis_num, artist, **kwargs):

        axis=self.axes[axis_num]
        # Deal with either single or multiple artists
        if isinstance(artist, list):
            for art in artist:
                # Just in case you reuse the same artist across axes make a copy and add that instead
                art_copy = copy(art)
                axis.add_artist(art_copy)
                self.axis_artists += [art_copy]
        else:
            art_copy = copy(artist)
            axis.add_artist(art_copy)
            self.axis_artists += [art_copy]



class Projection(Figure):

    def __init__(self, plot_num, add_sub_proj=True, add_colorbars=True, height_ratios=[5,1]):
        """
        Parameters
        ----------
        plot_num : int
            Number of plots in this figure.
        add_sub_proj : bool
            Toggle wether each projection has a sub projection along a different axis which is plotted right below it.
        add_colorbars : bool
            Toggle wether each projection has a colorbar.
        height_ratios : list
            Ratio between heights of projection, sub_projection, and colorbar. Only need to include ratio for each option selected.
        """
        self.plot_num = plot_num
        self.sub_proj = add_sub_proj
        self.has_colorbars = add_colorbars
        if self.sub_proj: self.height_ratios = height_ratios
        else: height_ratios = [1]
        # Set up subplots based on number of parameters given
        self.fig, self.axes = plot_utils.setup_proj_figure(plot_num, add_sub_proj, add_colorbars=add_colorbars,height_ratios=height_ratios)

        self.axis_artists = [[] for i in range(self.plot_num)]
        if add_colorbars:
            self.axis_colorbar = [None for i in range(self.plot_num)]
        self.axis_properties = ['' for i in range(self.plot_num)]


    def set_all_axis(self, properties, main_Ls, axes_visible=False, colorbar_kwargs=None):

        for i in range(len(self.axes)):
            if colorbar_kwargs is None:
                kwargs = {} if colorbar_kwargs is None else colorbar_kwargs[i]
            self.set_axis(i, properties[i], main_Ls[i], axes_visible=axes_visible, **kwargs)


    def set_axis(self, axis_num, property, main_L, axes_visible=False, **kwargs):
        default_colorbar_kwargs = {
            'cmap': 'magma', 
            'label': None,
            'limits': None,
            'log': None}
        
        self.axis_properties[axis_num]=property

        for kwarg in default_colorbar_kwargs:
            if kwarg not in kwargs:
                kwargs[kwarg] = default_colorbar_kwargs[kwarg]

        axes_set = self.axes[axis_num]
        if self.sub_proj: sub_L = main_L/self.height_ratios[0]*self.height_ratios[1]
        else: sub_L = None
        plot_utils.setup_proj_axis(axes_set, main_L, sub_L=sub_L, axes_visible=axes_visible)


    
    def plot_projection(self, axis_num, main_proj_data, main_extent, sub_proj_data=None, sub_extent=None, label=None, v_limits=None, v_log=False, **kwargs):
        default_imshow_kwargs = {
            'cmap': 'inferno', 
            'interpolation': 'bicubic',
            'aspect': 'equal',
            'origin': 'lower',
            'zorder': 1}        

        for kwarg in default_imshow_kwargs:
            if kwarg not in kwargs:
                kwargs[kwarg] = default_imshow_kwargs[kwarg]   

        # Change default projection limits
        if v_limits is not None:
            if v_log:
                norm = mpl.colors.LogNorm(vmin=v_limits[0], vmax=v_limits[1], clip=True)
            else:
                norm = mpl.colors.Normalize(vmin=v_limits[0], vmax=v_limits[1], clip=True)
            kwargs['norm'] = norm


        axes_set = self.axes[axis_num]
        ax1 = axes_set[0]
		# Plot top projection
        img1 = ax1.imshow(main_proj_data, extent=main_extent, **kwargs)
        if label is not None:
            ax1.annotate(label, (0.975,0.975), xycoords='axes fraction', color='xkcd:white', ha='right', va='top', fontsize=config.EXTRA_LARGE_FONT)
        # Plot sub projection if applicable
        if self.sub_proj:
            ax2 = axes_set[1]
            img2 = ax2.imshow(sub_proj_data, extent=sub_extent, **kwargs)
        if self.has_colorbars:
            cbar = plot_utils.setup_proj_colorbar(self.axis_properties[axis_num], self.fig, axes_set[-1], mappable=img1)       
            self.axis_colorbar[axis_num] = cbar

