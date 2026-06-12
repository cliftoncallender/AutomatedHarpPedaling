import unittest
from harp_pedaling import get_optimal_pedaling

class TestHarpPedaling(unittest.TestCase):

    def test_equally_optimal_pedalings(self):
        """Testing two optimal pedalings with absurd spellings of the C major
        scale filtered out. Pc 6 in the second set can be F# or Gb.
        """
        test = [{0, 2, 4, 5, 7, 9, 11}, {0, 2, 4, 6, 9, 11}]
        answer = [(('C', 'D', 'E', 'F', 'G', 'A', 'B'),
                    ('C', 'D', 'E', 'G-', 'A', 'B')),
                   (('C', 'D', 'E', 'F', 'G', 'A', 'B'),
                    ('C', 'D', 'E', 'F#', 'A', 'B'))]

        self.assertSpellingEqual(get_optimal_pedaling(test), answer)

    def test_figure_1(self):
        """Test the five-chord example from Figure 1 (g-i) in the paper.

        With the prefer_common_spellings filter set to True, returns four
        equally optimal solutions. Essentially, one can use Ab or G# in the
        first chord and D# or Eb in the last.
        """
        test = [set([4, 8, 11]),
                set([1, 5, 8]),
                set([10, 2, 5]),
                set([7, 11, 2]),
                set([3, 7, 10, 1])]

        answer = [(('G#', 'B', 'E'),
                   ('G#', 'C#', 'F'),
                   ('A#', 'D', 'F'),
                   ('D', 'B', 'G'),
                   ('C#', 'A#', 'D#', 'G')),
                  (('A-', 'B', 'E'),
                   ('A-', 'C#', 'F'),
                   ('A#', 'D', 'F'),
                   ('D', 'B', 'G'),
                   ('C#', 'A#', 'D#', 'G')),
                  (('G#', 'B', 'E'),
                   ('G#', 'C#', 'F'),
                   ('A#', 'D', 'F'),
                   ('D', 'B', 'G'),
                   ('C#', 'A#', 'E-', 'G')),
                  (('A-', 'B', 'E'),
                   ('A-', 'C#', 'F'),
                   ('A#', 'D', 'F'),
                   ('D', 'B', 'G'),
                   ('C#', 'A#', 'E-', 'G'))]

        self.assertSpellingEqual(get_optimal_pedaling(test), answer)

    def test_multi_pedal_allowed(self):
        """Simple test that multi-pedal moves, constrained as detailed in the
        paper, are allowed. The only way to move between these two slices is
        to lower G and A simultaneously to Gb and Ab.
        """
        test = [set([11, 0, 1, 3, 4, 7, 9]),
                set([11, 0, 1, 3, 4, 6, 8])]

        answer = [(('C', 'D-', 'E-', 'F-', 'G', 'A', 'B'),
                   ('C', 'D-', 'E-', 'F-', 'G-', 'A-', 'B'))]

        self.assertEqual(get_optimal_pedaling(test), answer)

    def test_sigma_high_enough(self):
        """Test of the penalty for a multi-pedal move (sigma > 2).

        The test case moves from a Hungarian minor scale to a six-note subset
        of the harmonic major scale. This move can either be accomplished by
        two different single pedal move with each foot (D/E# to D#/E or
        D/F# to D#/Fb) or a multi-pedal move with a single foot (E#/F# to Eb,
        Fb). For any value of sigma > 2, the algorithm will prefer the combined
        single-pedal moves over the multi-pedal move.
        """

        test = [set([11, 1, 2, 5, 6, 7, 10]),
                set([11, 1, 3, 4, 7, 10])]

        result = get_optimal_pedaling(test, prefer_common_spellings=False)

        second_slices = [frozenset(slices[1]) for slices in result]
        multi_pedal_solution = frozenset({'B', 'C#', 'E-', 'F-', 'G', 'A#'})

        self.assertNotIn(multi_pedal_solution, second_slices)

    def test_dear_matafele_peinam_original(self):
        """Test of a sequence that does not have a solutions. There are no
        enharmonic spellings that render this playable on the harp.
        """
        test = [set([9, 2, 4, 5]),
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

        answer = []

        self.assertEqual(get_optimal_pedaling(test), answer)


    def test_figure_1_transposed(self):
        """Test of the five-chord progression in figure 1 transposed.

        In this case, there are only three optimal solutions returned (when
        prefer_common_spellings is set to the default of True).
        """
        test = [set([0, 4, 7]),
                set([9, 1, 4]),
                set([6, 10, 1]),
                set([3, 7, 10]),
                set([11, 3, 6, 9])]

        answer = [(('C', 'E', 'G'),
                   ('A', 'E', 'D-'),
                   ('D-', 'B-', 'F#'),
                   ('B-', 'D#', 'G'),
                   ('D#', 'A', 'B', 'F#')),
                  (('C', 'E', 'G'),
                   ('A', 'E', 'D-'),
                   ('D-', 'B-', 'F#'),
                   ('B-', 'E-', 'G'),
                   ('E-', 'A', 'B', 'F#')),
                  (('C', 'E', 'G'),
                   ('A', 'E', 'C#'),
                   ('C#', 'B-', 'F#'),
                   ('B-', 'D#', 'G'),
                   ('D#', 'A', 'B', 'F#'))]

        self.assertSpellingEqual(get_optimal_pedaling(test), answer)

    def test_figure_2(self):
        "Test of figure 2 in the paper."
        test = [set([2, 8, 0, 4, 6, 1]),
                set([8, 2, 6, 10, 0]),
                set([7, 1, 5, 11, 6, 10])]

        answer = [(('B#', 'C#', 'D', 'E', 'F#', 'G#'),
                   ('B#', 'D', 'F#', 'G#', 'A#'),
                   ('C#', 'E#', 'F#', 'G', 'A#', 'B'))]

        self.assertEqual(get_optimal_pedaling(test), answer)

    @unittest.skip("Skipping test 7 manually")
    def test_7_long_sequence(self):
        """Sequence taken from the harp part in Mahler's Kindertotenlieder."""
        pcs = [2, 9, 6, 9, 2, 10, 7, 10, 9, 8, 3, 8, 7]
        test = [set([pc]) for pc in pcs]

        answer = [(('D',),
                   ('A',),
                   ('F#',),
                   ('A',),
                   ('D',),
                   ('B-',),
                   ('G',),
                   ('B-',),
                   ('A',),
                   ('A-',),
                   ('E-',),
                   ('A-',),
                   ('G',))]

        self.assertEqual(get_optimal_pedaling(test), answer)

    def test_prefer_common_spellings_flag(self):
        """Test that the readability filter discards some equally-optimal
        pedalings in the progression of figure 1 (g-i).
        """
        passage = [{4, 8, 11}, {1, 5, 8}, {10, 2, 5}, {7, 11, 2}, {3, 7, 10, 1}]

        filtered = get_optimal_pedaling(passage)  # default: True
        unfiltered = get_optimal_pedaling(passage, prefer_common_spellings=False)

        self.assertTrue(set(filtered).issubset(set(unfiltered)))
        self.assertLess(len(filtered), len(unfiltered))
        self.assertTrue(filtered)
        self.assertTrue(unfiltered)

    def test_prefer_common_spellings_no_solution(self):
        """Test that the unplayable passage from the original progression in
        Dear Matafele Peinam is flagged regardless of whether
        prefer_common_spellings is True or False.
        """
        unplayable = [{9, 2, 4, 5}, {8, 2, 4, 5}, {7, 1, 2, 5}, {6, 10, 1, 2, 5},
                      {4, 10, 0, 3, 5}, {3, 11, 2, 5}, {1, 9, 2, 4, 5},
                      {0, 8, 2, 4, 5}, {11, 7, 1, 2, 5}, {10, 6, 9, 1, 2, 5},
                      {8, 4, 10, 0, 5}, {7, 8, 9}]
        self.assertEqual(get_optimal_pedaling(unplayable), [])
        self.assertEqual(
            get_optimal_pedaling(unplayable, prefer_common_spellings=False), [])

    def assertSpellingEqual(self, actual, expected):
        self.assertEqual(strip_unnecessary_orderings(actual),
                         strip_unnecessary_orderings(expected))

def strip_unnecessary_orderings(spelling):
    modified_spelling = set()
    for passage in spelling:
        modified_passage = []
        for pcset in passage:
            modified_pcset = frozenset(pcset)
            modified_passage.append(modified_pcset)
        modified_spelling.add(tuple(modified_passage))
    return modified_spelling

if __name__ == '__main__':
    unittest.main()
