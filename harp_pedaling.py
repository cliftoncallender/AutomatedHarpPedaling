"""
Automated harp pedaling: a graph-theoretic approach to pitch spelling and
pedal settings.

This module optimizes music for the harp by finding enharmonic spellings that
minimize the number of pedal changes necessary. It implements the approach
described in:

    Clifton Callender, "Automated Harp Pedaling: A Graph-Theoretic Approach
    to Pitch Spelling and Pedal Settings," in Mathematics and Computation in
    Music (MCM 2026), LNAI 16609, Springer, pp. 603-616.
    https://doi.org/10.1007/978-3-032-27827-2_36

Overview
--------
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

Input format
------------
A sequence is a list of Python sets of integers mod 12, with B#/C=0, C#/Db=1,
..., B/Cb=11. For example, an E major triad followed by a Db major triad would
be the sequence

    [{4, 8, 11}, {1, 5, 8}].

Each set represents the distinct pitch classes in a given musical slice.

Output format
-------------
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

    [(('B#', 'C#', 'D', 'E', 'F#', 'G#'), ('B#', 'D', 'F#', 'G#', 'A#'),
      ('C#', 'E#', 'F#', 'G', 'A#', 'B'))]

(The order of the inner tuples for each slice is immaterial.)

Passages with more than one solution will have an output with multiple outer
tuples. Passages with no solutions will return an empty list, [].

get_optimal_pedaling
--------------------
    from harp_pedaling import get_optimal_pedaling

    passage = [{4, 8, 11}, {1, 5, 8}]
    for spelled_passage in get_optimal_pedaling(passage):
        # do something with the two 3-tuples in spelled_passage

By default, all equally-optimal spellings of a passage are filtered through a
readability block that penalizes less common enharmonic spellings B#, Cb, E#,
and Fb. In order to return all possible spellings as described in the paper,
call get_optimal_pedaling with the keyword argument prefer_common_spellings=False.

Dependencies: Python 3.7+ and networkx.
"""

from itertools import product
import networkx as nx
from functools import lru_cache

class Pedal_Graph:
    """Class for creating graph of pedal settings and finding the shortest path.

    Typically used indirectly as part of get_optimal_pedaling(). To use
    directly, instantiate the class, add a list of pitch-class sets to be
    optimized (add_sequence()), then process(). The resulting self.graph is a
    networkx DiGraph whose nodes consist of pedal setting / layer index pairs
    plus 'start' and 'end' nodes.
    """

    def __init__(self):
        self.all_settings = self.generate_all_settings()

    def generate_all_settings(self):
        """Return the set of all 3^7 = 2187 possible pedal settings."""
        return set([setting for setting in product([-1, 0, 1], repeat=7)])

    def add_sequence(self, sequence):
        """Store the passage (a list of pitch-class sets) to be optimized."""
        self.sequence = [chord for chord in sequence]

    def process(self):
        """Build the trellis graph: create layers, then weight all edges."""
        self.graph = nx.DiGraph()
        self._generate_layers()
        self._generate_edges()

    def _generate_layers(self):
        node = ('start', 0) # start node
        self.graph.add_node(node)
        self.layers = [set([node])]

        # pedal setting nodes
        for chord in self.sequence:
            self.layers.append(set())
            for setting in self.possible_settings(chord):
                node = (setting, len(self.layers) - 1)
                self.graph.add_node(node)
                self.layers[-1].add(node)

        node = ('end', len(self.layers)) # end node
        self.graph.add_node(node)
        self.layers.append(set([node]))

    def possible_settings(self, chord):
        settings = set()
        for setting in self.all_settings:
            if chord.issubset(self.setting_to_pcs(setting)):
                settings.add(setting)
        return settings

    def setting_to_pcs(self, setting):
        naturals = [2, 0, 11, 4, 5, 7, 9]

        return set([(s + n) % 12 for s, n in zip(setting, naturals)])

    def _generate_edges(self):
        for layer1, layer2 in zip(self.layers[:-1], self.layers[1:]):
            for node1 in layer1:
                for node2 in layer2:
                    setting1, setting2 = (node1[0], node2[0])
                    # weighting based on number of possible pedal changes
                    weight = self.pedal_weight(setting1, setting2)
                    if weight is not None:
                        self.graph.add_edge(node1, node2, weight=weight)

    @staticmethod
    @lru_cache(maxsize=None)
    def pedal_weight(setting1, setting2):
        """Cost function for moving from setting1 to setting2.

        Total cost is the sum of the cost per foot.

        Cost per foot: 0 or 1 for changing zero or one pedal;
                       3 for an adjacent multi-pedal move;
                       None for anything a single foot cannot execute.
        Edges from 'start' and to 'end' nodes cost 0.

        A None return signals the edge should be omitted from the graph.
        """
        if setting1 == 'start' or setting2 == 'end':
            return 0

        if setting1 == setting2:
            return 0

        # Split into left foot (D, C, B) and right foot (E, F, G, A)
        feet_transitions = (
            (setting1[:3], setting2[:3]), # left foot
            (setting1[3:], setting2[3:])  # right foot
        )

        weight = 0
        for foot in feet_transitions:
            state1, state2 = foot
            diff = sum(1 for x, y in zip(state1, state2) if x != y)
            if diff <=1:
                weight += diff
            elif Pedal_Graph.is_multi_pedal(state1, state2):
                weight += 3
            else:
                return None
        return weight

    @staticmethod
    def is_multi_pedal(state1, state2):
        """Test to see if the move from state1 to state2 is a multi-pedal move.

        A multi-pedal move consists of a pair of adjacent pedals controlled
        by a single foot, where the pedals begin and end in the same position.

        For example, D♮ C♮ → D♯ C♯ is an example of a multi-pedal move,
        since the D and C pedals are adjacent and begin and end in the same
        position, while D♮ C♭ → D♯ C♯ is not an example of a multi-pedal move,
        since the pedals do not begin in the same position.
        """
        # which pedals change?
        changed_pedals = [i for i, (x, y) in enumerate(zip(state1, state2))
                          if x != y]

        # must be two and only two
        if len(changed_pedals) != 2:
            return False

        i, j = changed_pedals

        # changed pedals must be adjacent
        if abs(i - j) != 1:
            return False

        # pedals must begin and end in the same position
        if (state1[i] != state1[j]) or (state2[i] != state2[j]):
            return False

        return True

def spelling_penalty(path):
    """Add a small penalty for less common spellings: Cb, B#, E#, and Fb."""

    penalty = 0

    for setting in path:
        if setting[1] == -1: # Cb
            penalty += 1
        if setting[2] == 1: # B#
            penalty += 1
        if setting[3] == 1: # E#
            penalty += 1
        if setting[4] == -1: # Fb
            penalty += 1
    return penalty

def get_optimal_pedaling(sequence, prefer_common_spellings=True):
    """
    Optimizes enharmonic spellings of a sequence of pitch-class sets to
    minimize the number of pedal changes.

    The primary optimization involves constructing a trellis graph of possible
    pedal settings as nodes and edge weights based on pedal changes between
    settings, then finding all shortest paths through the graph using
    networkx. (See paper for details.)

    Since preserving all optimal paths can yield trivially distinct but
    but difficult to read sequences of rare enharmonic spellings (e.g.
    substituting Cb/B# for B/C), there is a secondary optimization that
    penalizes the enharmonic spellings B#, Cb, E#, and Fb. When
    prefer_common_spellings is set to True (the default), these paths are
    filtered from the list. When set to False, all shortest paths are
    preserved (as discussed in the paper).
    """
    P = Pedal_Graph()
    P.add_sequence(sequence)
    P.process()

    best_paths = nx.all_shortest_paths(P.graph,
                                       source=('start', 0),
                                       target=('end', len(P.layers) - 1),
                                       weight='weight')
    paths = []
    try:
        for path in best_paths:
            cleaned_path = [node[0] for node in path[1:-1]]
            paths.append(cleaned_path)
    except nx.NetworkXNoPath:
        return []

    if prefer_common_spellings:
        scored_paths = [(spelling_penalty(path), path) for path in paths]
        minimum_penalty = min(score for score, _ in scored_paths)
        paths = [path for score, path in scored_paths
                 if score == minimum_penalty]

    unique_spelled_paths = group_paths_by_spelling(sequence, paths)
    return list(unique_spelled_paths.keys())

def group_paths_by_spelling(pcsets, paths):
    """
    pcset is a list of pitch-class sets. paths is a list of lists of
    pedal settings.

    Returns a dictionary where the keys are sequences of uniquely spelled
    pitch-class sets (tuples of tuples) and the values are the corresponding
    list of pedal settings.
    """

    unique_spellings = {}

    for path in paths:
        slices = get_spelling_options(pcsets, path)
        for option in product(*slices):
            if option not in unique_spellings:
                unique_spellings[option] = path
    return unique_spellings

def get_spelling_options(pcsets, settings):
    """
    pcsets is a list of pitch-class sets. settings is a list of harp
    pedal settings.

    Returns a list of lists of spelled pitch classes that are consistent
    with the sequence of pedal settings.
    """
    slices = []

    for pcset, setting in zip(pcsets, settings):
        slice_options = spelled_pcset(pcset, setting)
        slices.append(slice_options)

    return slices

def spelled_pcset(pcset, setting):
    """
    pcset if a set of pitches and setting is a pedal setting in the
    form of a 7-tuple; e.g. (0, 1, -1, 0, 0, 0, 0).

    Returns a list of tuples, each tuple corresponding to a valid spelling
    of pcset given setting.
    """

    letters = ('D', 'C', 'B', 'E', 'F', 'G', 'A')
    accidentals = {-1 : '-', 0 : '', 1 : '#'}
    base_vector = (2, 0, 11, 4, 5, 7, 9)
    slice_options = []

    for pc in pcset:
        pc_options = []
        for i in range(7):
            if pc == (base_vector[i] + setting[i]) % 12:
                letter = letters[i]
                accidental = accidentals[setting[i]]
                pc_options.append("{}{}".format(letter, accidental))

        if not pc_options:
            return []

        slice_options.append(pc_options)

    valid_combinations = [tuple(combo) for combo in product(*slice_options)]

    return valid_combinations
