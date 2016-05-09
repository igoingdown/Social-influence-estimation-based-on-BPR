from sklearn.cluster import KMeans
import numpy as np


class UserNeighbor(object):
    def __init__(self, cluster_num, top_n):
        self.cluster_num = cluster_num
        self.top_n = top_n
        self.users_neighbors = {}
        self.organizer_set = set()
        self.organizer_count_dict = {}
        # organizer_count_dict is a dict, its key is organizer_id(str type) and its value is the count
        self.t_event_id_v_event_id_dict = {}
        # t_event_id_v_event_id_dict is is a dict, tid(key, string type) and vid(value, int type)
        self.event_location_cluster_org_dict = {}
        # event_location_cluster_org_dict is a dict, its key is t_event_id, its value is tuples composed of
        # a list including its latitude(float type) and longitude(float type), the cluster number(int)
        # the event belongs to and the organizer of the event
        self.t_event_id_set = set()
        # t_event_id_set is the set of t_event_id(str type) from event_file.txt
        self.t_user_id_set = set()
        # t_user_id_set is the set of t_user_id(str type) from user_file.txt
        self.t_user_id_v_user_id_dict = {}
        # t_user_id_v_user_id_dict is is a dict, t_user_id(key, string type) and v_user_id(value, int type)
        self.neighbor_on_con = {}
        self.neighbor_on_org = {}
        self.neighbor_on_reg = {}
        self.social_influence_list = []
        # social influence list is a list of tuples composed of t_user_id(str type), t_event_id(str type)
        # and influence score(float type)
        self.temp_t_user_id = None

    def generate_t_event_id_v_event_id_dict(self):
        with open('event_file.txt') as f:
            for line in f:
                result = line.split()
                self.t_event_id_v_event_id_dict[result[0]] = int(result[1])
                self.t_event_id_set.add(result[0])

    def generate_t_user_id_v_user_id_dict(self):
        with open('user_file.txt') as f:
            for line in f:
                result = line.split()
                self.t_user_id_set.add(result[0])
                self.t_user_id_v_user_id_dict[result[0]] = int(result[1])

    def find_regions(self):
        organizer_list = []
        latitude_longitude_list = []
        event_id_list = []
        with open('event_info.txt') as f:
            for line in f:
                result = line.split()
                event_id_list.append(result[0])
                organizer_list.append(result[4])
                self.organizer_set.add(result[4])
                if result[4] in self.organizer_count_dict:
                    self.organizer_count_dict[result[4]] += 1
                else:
                    self.organizer_count_dict[result[4]] = 0
                latitude_longitude_list.append([float(result[2]), float(result[3])])
        latitude_longitude_array = np.array(latitude_longitude_list)
        cluster_array = KMeans(n_clusters=self.cluster_num, max_iter=500).fit_predict(latitude_longitude_array)
        for i in xrange(len(latitude_longitude_list)):
            self.event_location_cluster_org_dict[event_id_list[i]] = (latitude_longitude_list[i],
                                                                      cluster_array[i], organizer_list[i])

    def find_neighbor_on_con(self):
        pass

    def find_neighbor_on_org(self):
        user_influence_on_organizers = {}
        # users_influence_on_organizers is a dict, its key is t_user_id(str type) and its value is a dict
        # the child dict shows the user's influence on each organizer
        # the key of the child dict is organizer_id(str type) and its value is user's influence on this organizer
        # the value of child dict is initialized to 0

        for user in list(self.t_user_id_set):
            user_influence_on_organizers[user] = {}
            for org in list(self.organizer_set):
                user_influence_on_organizers[user][org] = 0
        for item in self.social_influence_list:
            user_influence_on_organizers[item[0]][self.event_location_cluster_org_dict[item[0]][2]] += item[2]
        for user in list(self.t_user_id_set):
            for org in list(self.organizer_set):
                if self.organizer_count_dict[org] == 0:
                    user_influence_on_organizers[user][org] = 0
                else:
                    user_influence_on_organizers[user][org] /= self.organizer_count_dict[org]

        for user in list(self.t_user_id_set):
            self.neighbor_on_org[user] = set()
            user_similarity_dict = {}
            # user_similarity_dict is a dict, its key is compare_user'id, its value shows the similarity between
            # user and compare_user
            for compare_user in list(self.t_user_id_set):
                if compare_user == user:
                    pass
                else:
                    for org in list(self.organizer_set):
                        user_similarity_dict[compare_user] += user_influence_on_organizers[user][org] * \
                                                              user_influence_on_organizers[compare_user][org]

                    user_similarity_dict[compare_user] /= (len(self.organizer_set))**2
            sorted_similarity_list = sorted(user_similarity_dict.iteritems(), key=lambda d: d[1], reverse=True)
            for i in xrange(self.top_n):
                self.neighbor_on_org[user].add(sorted_similarity_list[i][1])

    def find_neighbor_on_reg(self):
        users_influence_on_regions = {}
        # users_influence_on_regions is a dict, its key is t_user_id(str type) and its value is a list
        # the list shows the user's influence on each region
        # the length of the list is self.cluster_num and elements of the list are initialized to 0(float type)
        users_count_on_regions = {}
        # users_count_on_regions is a dict, its key is t_user_id(str type) and its value is a list
        # the shows the num of event the user has attended in each region
        # the length of the list is self.cluster_num and elements of the list are initialized to 0(int type)
        # users_influence_on_regions divided by users_count_on_regions is the average users'influence on each
        # region, which is what we want

        for user in list(self.t_user_id_set):
            if user not in users_influence_on_regions:
                users_influence_on_regions[user] = []
                for i in xrange(self.cluster_num):
                    users_influence_on_regions[user].append(0)
            if user not in users_count_on_regions:
                users_count_on_regions[user] = []
                for i in xrange(self.cluster_num):
                    users_count_on_regions[user].append(0)

        for item in self.social_influence_list:
            cluster_item_belong = self.event_location_cluster_org_dict[item[1]][1]
            users_count_on_regions[item[0]][cluster_item_belong] += 1
            users_influence_on_regions[item[0]][cluster_item_belong] += item[2]

        for user in list(self.t_user_id_set):
            for i in xrange(self.cluster_num):
                if users_count_on_regions[user][i] == 0:
                    users_influence_on_regions[user][i] = 0
                else:
                    users_influence_on_regions[user][i] /= users_count_on_regions[user][i]

        # TODO:use user influence to calculate similarity between each pair of user and generate neighbor on reg
        for user in list(self.t_user_id_set):
            self.neighbor_on_reg[user] = set()
            user_similarity_dict = {}
            # user_similarity_dict is a dict, its key is compare_user'id, its value shows the similarity between
            # user and compare_user
            for compare_user in list(self.t_user_id_set):
                if compare_user == user:
                    pass
                else:
                    user_similarity_dict[compare_user] = np.dot(np.array(users_influence_on_regions[user]),
                                                                np.array(users_influence_on_regions[compare_user]))
                    user_similarity_dict[compare_user] /= self.cluster_num**2
            sorted_similarity_list = sorted(user_similarity_dict.iteritems(), key=lambda d: d[1], reverse=True)
            for i in xrange(self.top_n):
                self.neighbor_on_reg[user].add(sorted_similarity_list[i][1])

    def generate_social_influence_matrix(self):
        self.generate_t_event_id_v_event_id_dict()
        self.generate_t_user_id_v_user_id_dict()
        temp_list = []
        with open('social_influence.txt') as f:
            for line in f:
                result = line.split('\t')
                if len(result) == 1:
                    temp = result[0].split('::')
                    temp = temp[0].split()
                    self.temp_t_user_id = temp[0]
                else:
                    for i in range(len(result)):
                        if result[i] != '' and result[i] != '\n':
                            t_event_id, score = result[i].split(':')
                            t_event_id = t_event_id.split()
                            temp_list.append((self.temp_t_user_id, t_event_id[0], float(score)))

        for i in xrange(len(temp_list)):
            if temp_list[i][0] in self.t_user_id_set and temp_list[i][1] in self.t_event_id_set:
                self.social_influence_list.append(temp_list[i])
        print 'social influence list length:', len(self.social_influence_list)

    # TODO:combine user_neighbor_on_con, user_neighbor_on_reg and user_neighbor_on_org to find final neighbor
    def generate_users_neighbors(self):
        for user in list(self.t_user_id_set):
            self.users_neighbors[user] = (self.neighbor_on_reg[user] & self.neighbor_on_con[user]) | \
                                         (self.neighbor_on_reg[user] & self.neighbor_on_org[user]) | \
                                         (self.neighbor_on_org[user] & self.neighbor_on_con[user])

if __name__ == '__main__':
    cluster_limit_num = 20
    neighbor_top_n = 100
    neighbor_model = UserNeighbor(cluster_limit_num, neighbor_top_n)
    neighbor_model.find_regions()
    neighbor_model.generate_social_influence_matrix()