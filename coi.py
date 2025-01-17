"""Community of interest (COI) preservation scores."""

from typing import Dict, Sequence, Any, Callable
from scipy.sparse import csr_matrix
from gerrychain import Partition
import numpy as np


def block_level_coi_preservation(
    unit_blocks: Dict[Any, set],
    coi_blocks: Dict[Any, set],
    block_pops: Dict[Any, float],
    thresholds: Sequence[float],
) -> Callable[[Partition], Dict[float, float]]:
    """
    Makes a COI preservation score function.
    We assume that dual graph units and communities of interest can both be
    represented (ideally losslessly) with a smaller common unit
    (typically Census blocks). For a given partitition :math:`P`, inclusion
    threshold :math:`t` and communities of interest :math:`C_1, \dots, C_n`,
    we compute the preservation score
        .. math:: f(P, t) = \sum_{i=1}^n (\max(f_1(C_i, P, t),f_2(C_i, P, t))
    where:
      * :math:`f_1(C_i, P, t) = 1` when :math:`100t\%%` of the population
        of community of interest :math:`C_i` is inside of one district in
        :math:`P` (0 otherwise). Intuitively, :math:`f_1` captures how much
        a community of interest is split across districts. When the typical
        COI population is much smaller than the typical district population,
        it is relatively easier to satisfy this criterion.
      * :math:`f_2(C_i, P, t)` is computed as the sum of the populations of
        the districts :math:`P_j` such that at least :math:`100t\%%` of the
        population of :math:`P_j` is inside of :math:`C_i`, divided by the
        population of :math:`C_i`. Intuitively, :math:`f_2` captures how districts
        are split across communities of interest (though this notion is less easy
        to interpret than :math:`f_1`). When the typical COI population is
        much larger than the typical district population, it is easier to
        satisfy this criterion.
    :param unit_blocks: A mapping from dual graph units to the blocks
      contained in each unit. THe key must be the same as the nodes
      in the dual graph.
    :param coi_blocks: A mapping from COIs to the blocks contained in
      each COI.
    :param block_pops: The block populations.
    :param thresholds: The threshold values to use (ranging in [0, 1]).
    :param partial_districts: If `True`, an alternative (non-integer-valued)
      formula is used to compute COI preservation scores.
    :return: An updater that computes the COI preservation score for a
      partition for each threshold in `thresholds`.
    """
    # We precompute a sparse COI-unit intersection matrix.
    node_ordering = {k: idx for idx, k in enumerate(unit_blocks.keys())}
    unit_coi_inter_pops = np.zeros((len(coi_blocks), len(unit_blocks)))
    for unit_idx, (unit, blocks_in_unit) in enumerate(unit_blocks.items()):
        for coi_idx, (coi, blocks_in_coi) in enumerate(coi_blocks.items()):
            unit_coi_inter_pops[coi_idx, unit_idx] = sum(
                block_pops[b] for b in blocks_in_coi & blocks_in_unit
            )
    unit_coi_inter_pops = csr_matrix(unit_coi_inter_pops)

    coi_pops = np.array(
        [sum(block_pops[b] for b in blocks) for blocks in coi_blocks.values()]
    )
    unit_pops = np.array(
        [sum(block_pops[b] for b in blocks) for blocks in unit_blocks.values()]
    )
    total_pop = unit_pops.sum()

    def score_fn(partition: Partition) -> Dict[float, float]:
        # Convert the assignment to a matrix encoding.
        dist_ordering = {dist: idx for idx, dist in enumerate(partition.parts.keys())}
        dist_mat = np.zeros((len(unit_blocks), len(dist_ordering)))
        for node, dist in partition.assignment.items():
            dist_mat[node_ordering[node], dist_ordering[dist]] = 1

        coi_dist_pops = unit_coi_inter_pops @ dist_mat
        max_district_pop_in_coi = np.max(coi_dist_pops, axis=1)
        score_by_threshold = {}
        ideal_dist_pop = total_pop / dist_mat.shape[1]

        # intersecting_dists = np.sum(coi_dist_pops > 0, axis=1)

        for threshold in thresholds:
            if threshold == 0.0:
                score_by_threshold[threshold] =  float(len(coi_blocks)) 

            # f_1: At least (100 * threshold)% of the population
            # of the COI is contained within one district.
            f1_scores = max_district_pop_in_coi >= threshold * coi_pops
            f1_scores = f1_scores.astype(int)

            over_threshold = (coi_dist_pops >= threshold * ideal_dist_pop)
            pop_over_threshold = np.multiply(over_threshold, coi_dist_pops).sum(axis=1)
            f2_scores = pop_over_threshold / coi_pops


            score_by_threshold[threshold] = np.maximum(f1_scores, f2_scores).sum()
        return score_by_threshold

    return score_fn
