from itertools import product
import networkx as nx
from functools import lru_cache

class Pedal_Graph:
    "Class for creating graph of pedal settings and finding the shortest path."

    def __init__(self):
        self.all_settings = self.generate_all_settings()
        self.letters = ["D", "C", "B", "E", "F", "G", "A"]
        self.accidentals = ["♭", "♮", "♯"]

    def generate_all_settings(self):
        return set([setting for setting in product([-1, 0, 1], repeat=7)])

    def add_sequence(self, sequence):
        self.sequence = [chord for chord in sequence]

    def process(self):
        self.graph = nx.DiGraph()
        self._generate_layers()
        self._generate_edges()

    def _generate_layers(self):
        # start node
        node = ('start', 0)
        self.graph.add_node(node)
        self.layers = [set([node])]

        # pedal setting nodes
        for chord in self.sequence:
            self.layers.append(set())
            for setting in self.possible_settings(chord):
                node = (setting, len(self.layers) - 1)
                self.graph.add_node(node)
                self.layers[-1].add(node)

        # end node
        node = ('end', len(self.layers))
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

    @lru_cache(maxsize=None)
    def pedal_weight(self, setting1, setting2):
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
            elif self.is_multi_pedal(state1, state2):
                weight += 3
            else:
                return None
        return weight

    def is_multi_pedal(self, state1, state2):
        # which pedal change?
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

    def setting_to_letters(self, setting):
        """Return pedal setting as letters."""
        output = ""
        for letter, position in zip(self.letters, setting):
            output += "{}{} ".format(letter, self.accidentals[position + 1])
            if letter == "B":
                output += "| "
        return output


def pcs_to_settings(pcs, settings):
    result = set()
    for setting in settings:
        pc_set = setting_to_pcs(setting)
        for pc in pcs:
            if pc not in pc_set:
                break
        else:
            result.add(setting)
    return result

def generate_pedals_dict():
    pedal = dict()
    for setting in product([-1, 0, 1], repeat=7):
        pedal[setting] = setting_to_pcs(setting)
    return pedal

def spelling_penalty(path):
    """ Add a small penalty for less common spellings:
    Cb, B#, E#, and Fb."""
    for setting in path:
        penalty = 0
        if setting[1] == -1: # Cb
            penalty += 1
        if setting[2] == 1: # B#
            penalty += 1
        if setting[3] == 1: # E#
            penalty += 1
        if setting[4] == -1: # Fb
            penalty += 1
    return penalty

def get_optimal_pedaling(sequence):
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

        scored_paths = [(spelling_penalty(path), path) for path in paths]
        minimum_penalty = min(score for score, _ in scored_paths)
        final_paths = [path for score, path in scored_paths
                       if score == minimum_penalty]
        return final_paths
    except nx.NetworkXNoPath:
        return [[]]

if __name__ == "__main__":
    test0 = [set([0, 2, 4, 5, 7, 9, 11]),
             set([0, 2, 4, 6, 9, 11])]

    answer0 = [[(0, 0, 0, 0, 0, 0, 0),
                (0, 0, 0, 0, 0, -1, 0)],
               [(0, 0, 0, 0, 0, 0, 0),
                (0, 0, 0, 0, 1, 0, 0)]]
    
    test1 = [set([0, 2, 4, 5, 7, 9, 11]),
             set([2, 4, 6, 7, 9, 11]),
             set([1, 2, 4, 6, 7, 9, 11])]

    answer1 = [[(0, 0, 0, 0, 0, 0, 0),
                (0, 0, 0, 0, 1, 0, 0),
                (0, 1, 0, 0, 1, 0, 0)],
               [(0, 0, 0, 0, 0, 0, 0),
                (0, 1, 0, 0, 1, 0, 0),
                (0, 1, 0, 0, 1, 0, 0)]]

    test2 = [set([0, 4, 7]),
             set([9, 1, 4]),
             set([6, 10, 1]),
             set([3, 7, 10]),
             set([11, 3, 6, 9])]

    answer2 = [[(-1, 0, -1, 0, 1, 0, 0),
                (-1, 0, -1, 0, 1, 0, 0),
                (-1, 0, -1, 0, 1, 0, 0),
                (1, 0, -1, 0, 1, 0, 0),
                (1, 0, 0, 0, 1, 0, 0)],
               [(-1, 0, -1, 0, 1, 0, 0),
                (-1, 0, -1, 0, 1, 0, 0),
                (-1, 0, -1, 0, 1, 0, 0),
                (-1, 0, -1, -1, 1, 0, 0),
                (-1, 0, 0, -1, 1, 0, 0)],
               [(-1, 0, -1, 0, 1, 0, 0),
                (-1, 0, -1, 0, 1, 0, 0),
                (-1, 0, -1, -1, 1, 0, 0),
                (-1, 0, -1, -1, 1, 0, 0),
                (-1, 0, 0, -1, 1, 0, 0)],
               [(-1, 0, -1, -1, -1, 0, 0),
                (-1, 0, -1, -1, -1, 0, 0),
                (-1, 0, -1, -1, 1, 0, 0),
                (-1, 0, -1, -1, 1, 0, 0),
                (-1, 0, 0, -1, 1, 0, 0)],
               [(1, 1, 1, 0, 1, 0, 0),
                (1, 1, 1, 0, 1, 0, 0),
                (1, 1, -1, 0, 1, 0, 0),
                (1, 1, -1, 0, 1, 0, 0),
                (1, 1, 0, 0, 1, 0, 0)],
               [(1, 1, 1, 0, 1, 0, 0),
                (1, 1, -1, 0, 1, 0, 0),
                (1, 1, -1, 0, 1, 0, 0),
                (1, 1, -1, 0, 1, 0, 0),
                (1, 1, 0, 0, 1, 0, 0)],
               [(1, 0, -1, 0, 1, 0, 0),
                (1, 1, -1, 0, 1, 0, 0),
                (1, 1, -1, 0, 1, 0, 0),
                (1, 1, -1, 0, 1, 0, 0),
                (1, 1, 0, 0, 1, 0, 0)]]

    test3 = [set([11, 0, 1, 3, 4, 7, 9]),
             set([11, 0, 1, 3, 4, 6, 8])]

    answer3 = [[(-1, 0, 0, -1, -1, 0, 0),
                (-1, 0, 0, -1, -1, -1, -1)]]

    test4 = [set([9, 2, 4, 5]),
             set([8, 2, 4, 5]),
             set([7, 1, 2, 5]),
             set([6, 10, 1, 2, 5]),
             set([4, 10, 0, 3, 5]),
             set([3, 11, 2, 5]),
             set([1, 9, 2, 4, 5]),
             set([0, 8, 2, 4, 5]),
             set([11, 7, 1, 2, 5]),
             set([10, 6, 9, 1, 2, 5]),
             set([8, 4, 10, 0, 5]),
             set([7, 8, 9])]

    answer4 = [[]]

    test5 = [set([4, 8, 11]),
             set([1, 5, 8]),
             set([10, 2, 5]),
             set([7, 11, 2]),
             set([3, 7, 10, 1])]

    answer5 = [[(0, 1, 0, 0, 0, 1, 1),
                (0, 1, 0, 0, 0, 1, 1),
                (0, 1, 0, 0, 0, 1, 1),
                (0, 1, 0, 0, 0, 0, 1),
                (1, 1, 0, 0, 0, 0, 1)],
               [(0, 1, 0, 0, 0, 0, -1),
                (0, 1, 0, 0, 0, 0, -1),
                (0, 1, 0, 0, 0, 0, 1),
                (0, 1, 0, 0, 0, 0, 1),
                (1, 1, 0, 0, 0, 0, 1)],
               [(0, 1, 0, 0, 0, 1, 1),
                (0, 1, 0, 0, 0, 1, 1),
                (0, 1, 0, 0, 0, 0, 1),
                (0, 1, 0, 0, 0, 0, 1),
                (1, 1, 0, 0, 0, 0, 1)],
               [(0, 1, 0, 0, 0, 1, 1),
                (0, 1, 0, 0, 0, 1, 1),
                (0, 1, 0, 0, 0, 1, 1),
                (0, 1, 0, 0, 0, 0, 1),
                (0, 1, 0, -1, 0, 0, 1)],
               [(0, 1, 0, 0, 0, 0, -1),
                (0, 1, 0, 0, 0, 0, -1),
                (0, 1, 0, 0, 0, 0, 1),
                (0, 1, 0, 0, 0, 0, 1),
                (0, 1, 0, -1, 0, 0, 1)],
               [(0, 1, 0, 0, 0, 1, 1),
                (0, 1, 0, 0, 0, 1, 1),
                (0, 1, 0, 0, 0, 0, 1),
                (0, 1, 0, 0, 0, 0, 1),
                (0, 1, 0, -1, 0, 0, 1)],
               [(0, 1, 0, 0, 0, 0, -1),
                (0, 1, 0, 0, 0, 0, -1),
                (0, 1, 0, 0, 0, 0, 1),
                (0, 1, 0, -1, 0, 0, 1),
                (0, 1, 0, -1, 0, 0, 1)],
               [(0, 1, 0, 0, 0, 1, 1),
                (0, 1, 0, 0, 0, 1, 1),
                (0, 1, 0, 0, 0, 0, 1),
                (0, 1, 0, -1, 0, 0, 1),
                (0, 1, 0, -1, 0, 0, 1)],
               [(0, 1, 0, 0, 0, 1, 1),
                (0, 1, 0, 0, 0, 1, 1),
                (0, 1, 0, -1, 0, 1, 1),
                (0, 1, 0, -1, 0, 0, 1),
                (0, 1, 0, -1, 0, 0, 1)],
               [(0, 1, 0, 0, 0, 1, 1),
                (0, 1, 0, -1, 0, 1, 1),
                (0, 1, 0, -1, 0, 1, 1),
                (0, 1, 0, -1, 0, 0, 1),
                (0, 1, 0, -1, 0, 0, 1)],
               [(0, 1, 0, -1, -1, 1, 1),
                (0, 1, 0, -1, 0, 1, 1),
                (0, 1, 0, -1, 0, 1, 1),
                (0, 1, 0, -1, 0, 0, 1),
                (0, 1, 0, -1, 0, 0, 1)],
               [(0, 1, 0, 0, 0, 0, -1),
                (0, 1, 0, -1, 0, 0, -1),
                (0, 1, 0, -1, 0, 0, 1),
                (0, 1, 0, -1, 0, 0, 1),
                (0, 1, 0, -1, 0, 0, 1)],
               [(0, 1, 0, -1, -1, 0, -1),
                (0, 1, 0, -1, 0, 0, -1),
                (0, 1, 0, -1, 0, 0, 1),
                (0, 1, 0, -1, 0, 0, 1),
                (0, 1, 0, -1, 0, 0, 1)],
               [(0, 1, 0, 0, 0, 1, 1),
                (0, 1, 0, -1, 0, 1, 1),
                (0, 1, 0, -1, 0, 0, 1),
                (0, 1, 0, -1, 0, 0, 1),
                (0, 1, 0, -1, 0, 0, 1)],
               [(0, 1, 0, -1, -1, 1, 1),
                (0, 1, 0, -1, 0, 1, 1),
                (0, 1, 0, -1, 0, 0, 1),
                (0, 1, 0, -1, 0, 0, 1),
                (0, 1, 0, -1, 0, 0, 1)]]

    test6 = [set([2, 8, 0, 4, 6, 1]),
             set([8, 2, 6, 10, 0]),
             set([7, 1, 5, 11, 6, 10])]

    answer6 = [[(0, 1, 1, 0, 1, 1, 1),
                (0, 1, 1, 1, 1, 1, 1),
                (0, 1, 0, 1, 1, 0, 1)]]

    # test7
    pcs = [2, 9, 6, 9, 2, 10, 7, 10, 9, 8, 3, 8, 7]
    test7 = [set([pc]) for pc in pcs]

    answer7 = [[(0, 0, -1, -1, 1, 0, 0),
                (0, 0, -1, -1, 1, 0, 0),
                (0, 0, -1, -1, 1, 0, 0),
                (0, 0, -1, -1, 1, 0, 0),
                (0, 0, -1, -1, 1, 0, 0),
                (0, 0, -1, -1, 1, 0, 0),
                (0, 0, -1, -1, 1, 0, 0),
                (0, 0, -1, -1, 1, 0, 0),
                (0, 0, -1, -1, 1, 0, 0),
                (0, 0, -1, -1, 1, 0, -1),
                (0, 0, -1, -1, 1, 0, -1),
                (0, 0, -1, -1, 1, 0, -1),
                (0, 0, -1, -1, 1, 0, -1)],
               [(0, 1, -1, -1, 1, 0, 0),
                (0, 1, -1, -1, 1, 0, 0),
                (0, 1, -1, -1, 1, 0, 0),
                (0, 1, -1, -1, 1, 0, 0),
                (0, 1, -1, -1, 1, 0, 0),
                (0, 1, -1, -1, 1, 0, 0),
                (0, 1, -1, -1, 1, 0, 0),
                (0, 1, -1, -1, 1, 0, 0),
                (0, 1, -1, -1, 1, 0, 0),
                (0, 1, -1, -1, 1, 0, -1),
                (0, 1, -1, -1, 1, 0, -1),
                (0, 1, -1, -1, 1, 0, -1),
                (0, 1, -1, -1, 1, 0, -1)]]

    tests = [test0, test1, test2, test3, test4, test5, test6]
    answers = [answer0, answer1, answer2, answer3, answer4, answer5, answer6]

    run_test_7 = True
    if run_test_7:
        tests.append(test7)
        answers.append(answer7)

    complete_success = True
    for i, (test, answer) in enumerate(zip(tests, answers)):
        print("Running test {} ...".format(i))
        paths = get_optimal_pedaling(test)
        if paths != answer:
            print("Test {} failed".format(i))
            print("get_optimal_pedaling returned \n{}.".format(paths))
            print("Answer is \n{}.".format(answer))
            complete_success = False
    if complete_success:
        print("All tests passed!")

