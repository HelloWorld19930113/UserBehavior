import pandas as pd
from itertools import combinations
import os
import sys
curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(os.path.split(rootPath)[0])
import json

class clusterData(object):
    pre = "../raw_data/ECommAI_ubp_round1_"
    mid_pre = "../mid_data/"
    real_pre = "../mid_data_random/"
    res_pre = "../result_data/"

    def __init__(self, small = True, sup = 0.1):
        # 置信度
        self.support_degree = sup
        self.small = small

    def find_frequent_cate(self):
        # 平均每位用户点的小类——42
        # 平均 item_id ———— 157
        # 平均 brand_id 84
        self.item_cate_df = self.load_item_feature()
        self.train = self.load_train()
        item_cate_list = self.item_cate_df.values
        # self.item_cate_dict = {item[0]: item[1] for item in item_cate_list}
        # self.cate_item_dict = {item[1]: item[0] for item in item_cate_list}
        self.item_brand_dict = {item[0]: item[2] for item in item_cate_list}
        # self.train['cate_id'] = self.train['item_id'].apply(lambda x: self.replace_item_id(x))
        self.train['cate_id'] = self.train['item_id'].apply(lambda x: self.replace_item_id_with_brand(x))
        self.train['num'] = 1
        self.train.drop(index=self.train[self.train['cate_id'] == -1].index, inplace=True)
        # 每个用户对应的品牌，去重
        self.train = self.train.groupby(by=['user_id', 'cate_id'])['num'].sum().reset_index()
        self.train['num'] = 1
        self.user_set = set(self.train['user_id'])
        self.total_user_num = len(self.user_set)
        user_dict = self.cal_brand_id_with_user(df=self.train, user_set=self.user_set, item_cate_df=self.item_cate_df)
        # 每个品牌在不同的用户中出现的次数
        self.item_num = self.train.groupby(by=['cate_id'])['num'].sum().reset_index()
        support_num = self.support_degree * self.total_user_num
        base_frequent_item_list = self.item_num[self.item_num['num'] > support_num]['cate_id'].values
        self.all_frequent_item_list = []
        print(base_frequent_item_list)
        self.cal_frequent_items_iter(base_frequent_item_list, support_num)
        print("频繁项：", self.all_frequent_item_list)
        self.clean_frq_item_set()
        print("清洗后:", self.all_frequent_item_list)

        pass

    def cal_brand_id_with_user(self, df, user_set, item_cate_df):
        user_dict = {}
        for user in user_set:
            cate_list = df.loc[df.user_id == user, 'cate_id'].values
            for cate in cate_list:
                item_list = item_cate_df.loc[item_cate_df.brand_id == cate, 'item_id'].values
                item_list = list(map(int, item_list))
                user_dict[int(user)] = item_list
        with open(self.mid_pre + "user_brand_item_dict.json", 'w', encoding='utf-8') as w:
            json.dump(user_dict, w)
        return user_dict

    def clean_frq_item_set(self):
        for i, item in enumerate(self.all_frequent_item_list):
            for j, item2 in enumerate(self.all_frequent_item_list):
                if i == j:
                    continue
                else:
                     if item.issubset(item2):
                        try:
                            self.all_frequent_item_list.remove(item)
                        except:
                            print("item 已删除", item)

    def cal_frequent_items_iter(self, frequent_item_list, support_num):
        waste_group = []
        for i in range(2, 4):
            print("组合数：", i)
            frequent_items = combinations(frequent_item_list, i)
            find_combine = False
            for group in frequent_items:
                group = set(group)
                is_waste = False

                for wp in waste_group:
                    if wp.issubset(group):
                        is_waste = True
                        break
                if not is_waste:
                    item_set = set()
                    for index, item in enumerate(group):
                        temp_set = set(self.train.loc[self.train['cate_id'] == item, 'user_id'])
                        if index == 0:
                            item_set = temp_set
                        else:
                            item_set = item_set.intersection(temp_set)
                    if len(item_set) > support_num:
                        self.all_frequent_item_list.append(group)
                        find_combine = True
                    else:
                        waste_group.append(group)
            if not find_combine:
                break


    def replace_item_id(self, x):
        try:
            return self.item_cate_dict[x]
        except:
            return -1

    def replace_item_id_with_brand(self, x):
        try:
            return self.item_brand_dict[x]
        except:
            return -1

    def load_item_feature(self):
        file_name = self.mid_pre + "item_feature.csv" if self.small else self.pre + "item_feature"
        data = pd.read_csv(file_name, sep='\t', header=None,
                           names=['item_id', 'cate_1_id', 'cate_id', 'brand_id', 'price'])
        print("load item feature, shape:", data.shape)
        data = self.pre_process_item_feature(data)
        return data.loc[:, ['item_id', 'cate_id', 'brand_id']]

    @staticmethod
    def pre_process_item_feature(data):
        data.fillna({'cate_1_id': data['cate_1_id'].mode().values[0], 'cate_id': data['cate_id'].mode().values[0],
                     'brand_id': data['brand_id'].mode().values[0], 'price': data['price'].mean()})
        return data

    def load_train(self):
        file_name = self.mid_pre + "train.csv" if self.small else self.pre + "train.csv"
        data = pd.read_csv(file_name, sep='\t', header=None, names=['user_id', 'item_id', 'behavior_type', 'date'])
        print("load train data, shape:", data.shape)
        return data

if __name__ =='__main__':
    cd = clusterData(small=False)
    cd.find_frequent_cate()