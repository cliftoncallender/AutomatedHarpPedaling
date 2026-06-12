# Automated harp pedaling: a graph-theoretic approach to pitch spelling and pedal settings

This tool optimizes music for the harp by finding enharmonic spellings that
minimize the number of pedal changes necessary. It implements the approach
described in:

> Clifton Callender, "Automated Harp Pedaling: A Graph-Theoretic Approach
> to Pitch Spelling and Pedal Settings," in Mathematics and Computation in
> Music (MCM 2026), LNAI 16609, Springer, pp. 603-616.
> https://doi.org/10.1007/978-3-032-27827-2_36

## Overview

Passages for harp are modeled as sequences of pitch-class sets, one for each
musical "slice". A directed trellis graph is constructed whereby 1) each layer
corresponds to a musical slice, 2) the nodes of each layer are the pedal
settings capable of producing the corresponding pitch-class set, and 3) edges
connecting nodes in adjacent layers are weighted according to a cost function
modeling pedal changes. Optimal enharmonic respellings are found through an
all-shortest-paths search through the trellis graph (via networkx). The
algorithm also detects impossible passages with no solutions that are
unplayable on the harp.

Each of the harp's seven pedals (in order D, C, B, E, F, G, A) can be in one
of three positions: flat (-1), natural (0), or sharp (1). A pedal setting is
thus a seven-tuple, s in {-1, 0, 1}^7.

The pedals are divided between those controlled by the left foot (D, C, B) and
those controlled by the right (E, F, G, A). In general, a single foot can only
change a single pedal at a time, with the exception of multi-pedal moves
involving adjacent pedals moving from and to the same positions.

## Input format

A sequence is a list of Python sets of integers mod 12, with B#/C=0, C#/Db=1,
..., B/Cb=11. For example, an E major triad followed by a Db major triad would
be the sequence

```python
[{4, 8, 11}, {1, 5, 8}]
```

Each set represents the distinct pitch classes in a given musical slice.

## Output format

The primary function to be called, get_optimal_pedaling, returns a list of
spelled passages, where each uniquely spelled sequence is a tuple of slices and
each slice is a tuple of note names. Note names are strings combining a letter
name with an optional modifier for accidentals, where '#' indicates a sharp and
'-' indicates a flat. (This is consistent with music21's format for spelled
pitch classes.)

For example, if the input corresponds to figure 2 from the paper, then the
input is [{2, 8, 0, 4, 6, 1}, {8, 2, 6, 10, 0}, {7, 1, 5, 11, 6, 10}]. There is
only one optimal spelling of this three-chord progression, i.e., the spelling
that minimizes pedal changes (other spellings are playable but require more
pedal changes). Therefore, the output is a list of a single tuple, which
contains a sequence of three tuples, one for each slice:

```python
[(('B#', 'C#', 'D', 'E', 'F#', 'G#'), ('B#', 'D', 'F#', 'G#', 'A#'),
  ('C#', 'E#', 'F#', 'G', 'A#', 'B'))]
```

(The order of the inner tuples for each slice is immaterial.)

Passages with more than one solution will have an output with multiple outer
tuples. Passages with no solutions will return an empty list, [].

## get_optimal_pedaling

```python
from harp_pedaling import get_optimal_pedaling

passage = [{4, 8, 11}, {1, 5, 8}]
for spelled_passage in get_optimal_pedaling(passage):
    # do something with the two 3-tuples in spelled_passage
```

By default, all equally-optimal spellings of a passage are filtered through a
readability block that penalizes less common enharmonic spellings B#, Cb, E#,
and Fb. In order to return all possible spellings as described in the paper,
call get_optimal_pedaling with the keyword argument prefer_common_spellings=False.

Dependencies: Python 3.7+ and networkx.
