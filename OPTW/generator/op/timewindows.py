import math
import numpy as np
import pandas as pd

from AI_USI_MA.OPTW.op_utils import op


class TWGenerator:

    def __init__(self):
        pass

    def __call__(self, inst_df, w=None):

        self.cities_coordinate = inst_df
        self.adjacency_matrix = self.get_adjacency_matrix()
        if w is None:
            print('no time window parameter w was given! Generating instances without time windows')
            return self.cities_coordinate[['XCOORD.', 'YCOORD.', 'TW_LOW', 'TW_HIGH']], self.adjacency_matrix

        self.second_nearest_neighbor = self.get_second_nearest_neighbor_tsp_tour()
        return self.tw_generator1(w=w)

    def tw_generator1(self, w=60):
        """
        This function is based on the following work.

        Y. Dumas, J. Desrosiers, E. Gelinas, and M. M. Solomon. An optimal algorithm for the traveling salesman problem
        with time windows. Operations Research, 43(2):367-371, 1995.

        The time windows are generated around the times to begin service at each customer of a second nearest neighbor
        TSP tour. Each side of a time is generated as a uniform random variable in the interval [0,w/2]
        where w = 60, 80 and 100.

        :return this functions returns a dataframe with n rows and 4 columns. the columns are
        x-coordinate, y-coordinate, time-window-left and the
        time-windows-right
        """

        time_windows = pd.DataFrame(columns=['XCOORD', 'YCOORD', 'TW_LOW', 'TW_HIGH'])
        # time_windows['CUSTNO.'] = self.cities_coordinate.index.values

        time_windows['XCOORD'] = self.cities_coordinate['XCOORD']
        time_windows['YCOORD'] = self.cities_coordinate['YCOORD']
        time_windows.loc[0, 'TW_LOW'] = 0
        time_windows.loc[0, 'TW_HIGH'] = math.ceil(self.second_nearest_neighbor['distance_so_far'].max() + w)
        for i in self.second_nearest_neighbor.index:
            target_city = self.second_nearest_neighbor.loc[i, 'node']
            if target_city > 0:
                time_windows.loc[target_city, 'TW_LOW'] = np.random.randint(
                    low=max(0, self.second_nearest_neighbor.loc[i, 'distance_so_far'] - (w)),
                    high=self.second_nearest_neighbor.loc[i, 'distance_so_far'])
                time_windows.loc[target_city, 'TW_HIGH'] = np.random.randint(
                    low=max(0, self.second_nearest_neighbor.loc[i, 'distance_so_far']),
                    high=self.second_nearest_neighbor.loc[i, 'distance_so_far'] + (w))

        time_windows.insert(0, 'CUSTNO', self.cities_coordinate.index.values)

        # print(time_windows)
        return time_windows, self.adjacency_matrix

    def get_second_nearest_neighbor_tsp_tour(self):
        """
        This function use the set of points in self.cities_coordination and calculate the distance matrix in the format of pandas.DataFrame
        :return: a DataFrame where the number of rows is equal to the number of cities/nodes and its columns are ['node', 'distance_so_far']. Node is
        the index of the city and distance_so_far is length of passed path.
        """
        tour = pd.DataFrame(index=np.arange(len(self.cities_coordinate.index)), columns=['node', 'distance_so_far'])
        current_node = 0
        tour.loc[0, :] = pd.Series({'node': 0, 'distance_so_far': 0})
        distance_matrix = self.adjacency_matrix.copy()
        i = 1
        tour_length = 0
        while len(distance_matrix.index) > 1:
            dists = pd.Series(distance_matrix.loc[:, current_node].copy())
            dists = dists.sort_values(ascending=True)
            remaining_nodes = len(dists.index)
            if remaining_nodes > 2:
                selected_node = dists.index[2]
            elif remaining_nodes > 1:
                selected_node = dists.index[1]
            else:
                selected_node = 0
            tour_length += distance_matrix.loc[selected_node, current_node]
            tour.loc[i, :] = pd.Series({'node': selected_node, 'distance_so_far': tour_length})
            distance_matrix.drop(current_node, axis=0, inplace=True)
            distance_matrix.drop(current_node, axis=1, inplace=True)
            i += 1
            current_node = selected_node
        tour.loc[i, :] = pd.Series(
            {'node': 0, 'distance_so_far': tour_length + self.adjacency_matrix.loc[current_node, 0]})
        return tour

    def get_adjacency_matrix(self):
        adjacency_matrix = pd.DataFrame(index=np.arange(len(self.cities_coordinate.index)),
                                        columns=np.arange(len(self.cities_coordinate.index)))
        for i in np.arange(len(self.cities_coordinate)):
            for j in np.arange(len(self.cities_coordinate)):
                x1 = (self.cities_coordinate.loc[i, 'XCOORD'], self.cities_coordinate.loc[i, 'YCOORD'])
                x2 = (self.cities_coordinate.loc[j, 'XCOORD'], self.cities_coordinate.loc[j, 'YCOORD'])

                adjacency_matrix.loc[i, j] = op.dist_l2_closest_integer(x1, x2)
        return adjacency_matrix
