# -*- coding: utf-8 -*-
#
# downward uses the lab package to conduct experiments with the
# Fast Downward planning system.
#
# Copyright (C) 2012  Jendrik Seipp (jendrikseipp@web.de)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
import math
import os
from collections import defaultdict

from lab import tools

from downward.reports import PlanningReport


class Plot(object):
    def __init__(self):
        self.legend = None
        self.create_canvas_and_axes()

    def create_canvas_and_axes(self):
        # Import in method to be compatible to rtfd.org
        try:
            from matplotlib.backends import backend_agg
            from matplotlib import figure
        except ImportError, err:
            logging.critical('matplotlib could not be found: %s' % err)

        # Create a figure with size 6 x 6 inches
        fig = figure.Figure(figsize=(10, 10))

        # Create a canvas and add the figure to it
        self.canvas = backend_agg.FigureCanvasAgg(fig)
        self.axes = fig.add_subplot(111)

    @staticmethod
    def change_axis_formatter(axis, missing_val):
        # We do not want the default formatting that gives zeros a special font
        formatter = axis.get_major_formatter()
        old_format_call = formatter.__call__

        def new_format_call(x, pos):
            if x == 0:
                return 0
            if x == missing_val:
                return 'Missing'  # '$\mathdefault{None^{\/}}$' no effect
            return old_format_call(x, pos)

        formatter.__call__ = new_format_call

    def create_legend(self, categories):
        # Only print a legend if there is at least one non-default category.
        if any(key is not None for key in categories.keys()):
            self.legend = self.axes.legend(scatterpoints=1, loc='center left',
                                      bbox_to_anchor=(1, 0.5))

    def print_figure(self, filename):
        # Save the generated scatter plot to a PNG file.
        # Legend is still bugged in mathplotlib, but there is a patch see:
        # http://www.mail-archive.com/matplotlib-users@lists.sourceforge.net/msg20445.html
        extra_artists = []
        if self.legend:
            extra_artists.append(self.legend.legendPatch)
        self.canvas.print_figure(filename, dpi=100, bbox_inches='tight',
                                 bbox_extra_artists=extra_artists)
        logging.info('Wrote file://%s' % filename)


class PlotReport(PlanningReport):
    """
    Abstract base class for Plot classes.
    """
    LINEAR = ['cost', 'coverage', 'plan_length', 'initial_h_value']

    def __init__(self, category_styles=None, **kwargs):
        """
        ``kwargs['attributes']`` must contain exactly one attribute.

        Subclasses may define a *get_category* function that returns a category
        name for points in the plot. These categories are separated visually
        by drawing them with different styles. You can set the styles manually
        by providing a dictionary *category_styles* that maps category names to
        tuples (marker, color) where marker and color are valid values for
        pyplot (see http://matplotlib.sourceforge.net/api/pyplot_api.html).
        For example to change the default style to blue stars use::

            ScatterPlotReport(attributes=['expansions'],
                              category_styles={None: ('*','b')})
        """
        PlanningReport.__init__(self, **kwargs)
        self.category_styles = category_styles or {}
        assert len(self.attributes) == 1, self.attributes
        self.attribute = self.attributes[0]

    def _calc_max_val(self, runs):
        # It may be the case that no values are found.
        try:
            return max(run.get(self.attribute) for run in runs)
        except ValueError:
            return None

    def _get_missing_val(self, max_value):
        """
        Separate the missing values by plotting them at (max_value * 10) rounded
        to the next power of 10.
        """
        assert max_value is not None
        return 10 ** math.ceil(math.log10(max_value * 10))

    def _get_category_styles(self, categories):
        # Pick any style for categories for which no style is defined.
        # TODO: add more possible styles.
        styles = self.category_styles.copy()
        possible_styles = [(m, c) for m in 'ox+^v<>' for c in 'rgby']
        missing_category_styles = (set(categories.keys()) - set(styles.keys()))
        for i, missing in enumerate(missing_category_styles):
            styles[missing] = possible_styles[i % len(possible_styles)]
        return styles

    def _fill_categories(self, runs, missing_val):
        raise NotImplementedError

    def _plot(self, axes, categories, missing_val):
        raise NotImplementedError

    def _write_plot(self, runs, filename):
        plot = Plot()

        max_value = self._calc_max_val(runs)
        if max_value is None or max_value <= 0:
            logging.info('Found no valid datapoints for the plot.')
            return

        missing_val = self._get_missing_val(max_value)

        # Map category names to value tuples
        categories = self._fill_categories(runs, missing_val)
        styles = self._get_category_styles(categories)

        self._plot(plot.axes, categories, styles, missing_val)

        plot.create_legend(categories)
        plot.print_figure(filename)

    def write(self):
        raise NotImplementedError


class ProblemPlotReport(PlotReport):
    """
    For each problem generate a plot for a specific attribute.
    """
    def __init__(self, get_category=None, get_x=None, **kwargs):
        """
        *get_category* can be a function that takes a **single** run (dictionary
        of properties) and returns a category name which is used to group the
        values. Grouped values are drawn with the same style, e.g. red stars.
        Runs for which this function returns None are shown in a default
        category and are not contained in the legend.
        If *get_category* is None, all runs are shown in the default category.

        *get_x* can be a function that takes a **single** run and returns a
        numeric value or string that should be used as the x-ccordinate for this
        point (the y-coordinate is predetermined by the value for the plotted
        attribute). If *get_x* is None, the config name is used as the
        x-coordinate.

        For example, to compare different ipdb and m&s configurations use::

            # Configs: 'ipdb-1000', 'ipdb-2000', 'mas-1000', 'mas-2000'
            def get_states(run):
                nick, states = run['config_nick'].split('-')
                return states
            def get_nick(run):
                nick, states = run['config_nick'].split('-')
                return nick

            PlotReport(attributes=['expansions'],
                       get_x=get_states,
                       get_category=get_nick)

        """
        PlotReport.__init__(self, **kwargs)
        # By default plot the configs on the x-axis.
        self.get_x = get_x or (lambda run: run['config'])
        # By default all values are in the same category.
        self.get_category = get_category or (lambda run: None)

    def _fill_categories(self, runs, missing_val):
        categories = defaultdict(list)
        for run in runs:
            x = self.get_x(run)
            category = self.get_category(run)
            y = run.get(self.attribute)
            if y is None:
                y = missing_val
            categories[category].append((x, y))
        return categories

    def _plot(self, axes, categories, styles, missing_val):
        # Find all x-values.
        all_x = set()
        for coordinates in categories.values():
            x, y = zip(*coordinates)
            all_x |= set(x)
        all_x = sorted(all_x)

        # Map all x-values to positions on the x-axis.
        indices = dict((val, i) for i, val in enumerate(all_x, start=1))

        # Reserve space on the x-axis for all x-values and the labels.
        axes.set_xticks(range(1, len(all_x) + 1))
        axes.set_xticklabels(all_x)

        # Plot all categories.
        for category, coordinates in categories.items():
            marker, c = styles[category]
            x, y = zip(*coordinates)
            xticks = [indices[val] for val in x]
            axes.scatter(xticks, y, marker=marker, c=c, label=category)

        axes.set_xlim(left=0, right=len(all_x) + 1)
        axes.set_ylim(bottom=0, top=missing_val * 1.25)
        if self.attribute not in self.LINEAR:
            axes.set_yscale('symlog')
        Plot.change_axis_formatter(axes.yaxis, missing_val)

        # Make a descriptive title and set axis labels.
        axes.set_title(self.attribute, fontsize=14)

    def _write_plots(self, directory):
        for (domain, problem), runs in sorted(self.problem_runs.items()):
            filename = os.path.join(directory, '-'.join([self.attribute, domain,
                                                         problem]) + '.png')
            self._write_plot(runs, filename)

    def write(self):
        if os.path.isfile(self.outfile):
            logging.critical('outfile must be a directory for this report.')
        tools.makedirs(self.outfile)
        self._write_plots(self.outfile)
