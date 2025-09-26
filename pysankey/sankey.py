# -*- coding: utf-8 -*-
"""
Produces simple Sankey Diagrams with matplotlib.
@author: Anneya Golob & marcomanz & pierre-sassoulas & jorwoods

NOTE: This code was updated from the original version found at
https://github.com/anazalea/pySankey. The original version is licensed under the
GNU General Public License v3.0, and the license is included in the rest of this package.
The main changes are to enable more formatting options, and to organize the strips and
labels differently. This code is provided to facilitate replication of figures in specific
academic papers, and is not intended to be a general-purpose library.

                      .-.
                 .--.(   ).--.
      <-.  .-.-.(.->          )_  .--.
       `-`(     )-'             `)    )
         (o  o  )                `)`-'
        (      )                ,)
        ( ()  )                 )
         `---"\    ,    ,    ,/`
               `--' `--' `--'
                |  |   |   |
                |  |   |   |
                '  |   '   |
"""

from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# Set default matplotlib parameters for LaTeX rendering


class pySankeyException(Exception):
    pass
class NullsInFrame(pySankeyException):
    pass
class LabelMismatch(pySankeyException):
    pass

def check_data_matches_labels(labels, data, side):
    if len(labels) > 0:
        if isinstance(data, list):
            data = set(data)
        if isinstance(data, pd.Series):
            data = set(data.unique().tolist())
        if isinstance(labels, list):
            labels = set(labels)
        if labels != data:
            msg = "\n"
            if len(labels) <= 20:
                msg = "Labels: " + ",".join(labels) +"\n"
            if len(data) < 20:
                msg += "Data: " + ",".join(data)
            raise LabelMismatch('{0} labels and data do not match.{1}'.format(side, msg))


def label_formatting(lab, val, pct_vals):
    if pct_vals:
        return lab + " " + "{:.1f}".format(val * 100) + r"%"
    else:
        return lab + " " + "{:.1f}".format(val)


def get_categories_by_cumulative_weight(df, category_col='category', weight_col='weight'):
    grouped = df.groupby(category_col)[weight_col].sum()
    sorted_categories = grouped.sort_values(ascending=False).index.tolist()
    return sorted_categories


def sankey(left, right, leftWeight=None, rightWeight=None, colorDict=None,
           leftLabels=None, rightLabels=None, aspect=4, gcf_size=None, rightColor=False,
           fontsize=14, flowAlpha=0.60, fontname=None, figure_name=None, closePlot=False,
           leftStackTitle=None, rightStackTitle=None, pct_vals=False):
    '''
    Make Sankey Diagram showing flow from left-->right

    Inputs:
        left = NumPy array of object labels on the left of the diagram
        right = NumPy array of corresponding labels on the right of the diagram
            len(right) == len(left)
        leftWeight = NumPy array of weights for each strip starting from the
            left of the diagram, if not specified 1 is assigned
        rightWeight = NumPy array of weights for each strip starting from the
            right of the diagram, if not specified the corresponding leftWeight
            is assigned
        colorDict = Dictionary of colors to use for each label
            {'label':'color'}
        leftLabels = order of the left labels in the diagram
        rightLabels = order of the right labels in the diagram
        aspect = vertical extent of the diagram in units of horizontal extent
        rightColor = If true, each strip in the diagram will be be colored
                    according to its left label
        pct_vals = If true, format labels as percentages
    Ouput:
        None
    '''
    if leftWeight is None:
        leftWeight = []
    if rightWeight is None:
        rightWeight = []
    if leftLabels is None:
        leftLabels = []
    else:
        leftLabels = leftLabels[::-1]
    if rightLabels is None:
        rightLabels = []
    else:
        rightLabels = rightLabels[::-1]
    # Check weights
    if len(leftWeight) == 0:
        leftWeight = np.ones(len(left))

    if len(rightWeight) == 0:
        rightWeight = leftWeight

    if fontname is None:
        fontname = plt.rcParams['font.family'][0]  # Get current default

    if gcf_size is None:
        gcf_size = {'figsize': (12, 3 * aspect)}
    
    # Create Dataframe
    if isinstance(left, pd.Series):
        left = left.reset_index(drop=True)
    if isinstance(right, pd.Series):
        right = right.reset_index(drop=True)
    df = pd.DataFrame({'left': left, 'right': right, 'leftWeight': leftWeight,
                       'rightWeight': rightWeight}, index=range(len(left)))
    
    if len(df[(df.left.isnull()) | (df.right.isnull())]):
        raise NullsInFrame('Sankey graph does not support null values.')

    # Identify all labels that appear 'left' or 'right'
    allLabels = pd.Series(np.r_[df.left.unique(), df.right.unique()]).unique()

    # Identify left labels
    if len(leftLabels) == 0:
        leftLabels = pd.Series(df.left.unique()).unique()
    else:
        check_data_matches_labels(leftLabels, df['left'], 'left')

    # Identify right labels
    if len(rightLabels) == 0:
        rightLabels = pd.Series(df.right.unique()).unique()
    else:
        check_data_matches_labels(rightLabels, df['right'], 'right')
    # If no colorDict given, make one
    if colorDict is None:
        colorDict = {}
        pal = "hls"
        cls = sns.color_palette(pal, len(allLabels))
        for i, l in enumerate(allLabels):
            colorDict[l] = cls[i]
    else:
        missing = [label for label in allLabels if label not in colorDict.keys()]
        if missing:
            raise RuntimeError('colorDict specified but missing values: '
                                '{}'.format(','.join(missing)))

    # Determine widths of individual strips
    ns_l = defaultdict()
    ns_r = defaultdict()
    for l in leftLabels:
        myD_l = {}
        myD_r = {}
        for l2 in rightLabels:
            myD_l[l2] = df[(df.left == l) & (df.right == l2)].leftWeight.sum()
            myD_r[l2] = df[(df.left == l) & (df.right == l2)].rightWeight.sum()
        ns_l[l] = myD_l
        ns_r[l] = myD_r

    # Determine positions of left label patches and total widths
    widths_left = defaultdict()
    for i, l in enumerate(leftLabels):
        myD = {}
        myD['left'] = df[df.left == l].leftWeight.sum()
        if i == 0:
            myD['bottom'] = 0
            myD['top'] = myD['left']
        else:
            myD['bottom'] = widths_left[leftLabels[i - 1]]['top'] + 0.02 * df.leftWeight.sum()
            myD['top'] = myD['bottom'] + myD['left']
            topEdge = myD['top']
        widths_left[l] = myD

    # Determine positions of right label patches and total widths
    widths_right = defaultdict()
    for i, l in enumerate(rightLabels):
        myD = {}
        myD['right'] = df[df.right == l].rightWeight.sum()
        if i == 0:
            myD['bottom'] = 0
            myD['top'] = myD['right']
        else:
            myD['bottom'] = widths_right[rightLabels[i - 1]]['top'] + 0.02 * df.rightWeight.sum()
            myD['top'] = myD['bottom'] + myD['right']
            topEdge = myD['top']
        widths_right[l] = myD

    # Total vertical extent of diagram
    xMax = topEdge / aspect

    # Draw vertical bars on left and right of each label's section & print label
    for l in leftLabels:
        plt.fill_between(
            [-0.02 * xMax, 0],
            2 * [widths_left[l]['bottom']],
            2 * [widths_left[l]['bottom'] + widths_left[l]['left']],
            color=colorDict[l], 
            alpha=0.99
        )

        lab_l = label_formatting(l, widths_left[l]['left'], pct_vals)
        plt.text(
            -0.05 * xMax,
            widths_left[l]['bottom'] + 0.5 * widths_left[l]['left'],
            lab_l,
            {'ha': 'right', 'va': 'center'},
            fontsize=fontsize+1,
            fontname=fontname
        )
    for l in rightLabels:
        plt.fill_between(
            [xMax, 1.02 * xMax], 2 * [widths_right[l]['bottom']],
            2 * [widths_right[l]['bottom'] + widths_right[l]['right']],
            color=colorDict[l],
            alpha=0.99
        )
        lab_r = label_formatting(l, widths_right[l]['right'], pct_vals)
        plt.text(
            1.05 * xMax, widths_right[l]['bottom'] + 0.5 * widths_right[l]['right'],
            lab_r,
            {'ha': 'left', 'va': 'center'},
            fontsize=fontsize+1,
            fontname=fontname
        )

    # Plot strips
    for l in leftLabels:
        for l2 in rightLabels:
            lc = l
            if rightColor:
                lc = l2
            if len(df[(df.left == l) & (df.right == l2)]) > 0:
                # Create array of y values for each strip, half at left value, half at right, convolve
                ys_d = np.array(50 * [widths_left[l]['bottom']] + 50 * [widths_right[l2]['bottom']])
                ys_d = np.convolve(ys_d, 0.05 * np.ones(20), mode='valid')
                ys_d = np.convolve(ys_d, 0.05 * np.ones(20), mode='valid')
                ys_u = np.array(50 * [widths_left[l]['bottom'] + ns_l[l][l2]] + 50 * [widths_right[l2]['bottom'] + ns_r[l][l2]])
                ys_u = np.convolve(ys_u, 0.05 * np.ones(20), mode='valid')
                ys_u = np.convolve(ys_u, 0.05 * np.ones(20), mode='valid')

                # Update bottom edges at each label so next strip starts at the right place
                widths_left[l]['bottom'] += ns_l[l][l2]
                widths_right[l2]['bottom'] += ns_r[l][l2]
                plt.fill_between(
                    np.linspace(0, xMax, len(ys_d)), ys_d, ys_u, 
                    alpha=flowAlpha,
                    color=colorDict[lc],
                    linewidth=0.5
                )
                lab_f = label_formatting("", ns_l[l][l2], pct_vals) if ns_l[l][l2] > 0.01 else ""
                plt.text(
                    0.01, 0.5 * (ys_d[0] + ys_u[0]),
                    lab_f,
                    {'ha': 'left', 'va': 'center'},
                    fontsize=fontsize,
                    fontname=fontname
                )
                plt.text(
                    xMax - 0.01, 0.5 * (ys_d[-1] + ys_u[-1]),
                    lab_f,
                    {'ha': 'right', 'va': 'center'},
                    fontsize=fontsize,
                    fontname=fontname
                )
    # Add titles to left and right stacks
    if leftStackTitle is not None:
        plt.text(
            0, 1.03 * topEdge,
            leftStackTitle,
            {'ha': 'right', 'va': 'center'},
            fontsize=fontsize + 2,
            fontname=fontname
        )
    if rightStackTitle is not None:
        plt.text(
            xMax, 1.03 * topEdge,
            rightStackTitle,
            {'ha': 'left', 'va': 'center'},
            fontsize=fontsize + 2,
            fontname=fontname
        )
                


    plt.gca().axis('off')
    plt.gcf().set_size_inches(**gcf_size)
    if figure_name!=None:
        plt.savefig("{}.png".format(figure_name), bbox_inches='tight', dpi=150)
    plt.close()
