from DRL.DDPG import DDPG
import fgmodule.fgenv as fgenv
import scaffold.pidpilot as PID
import scaffold.fgdata as dfer
import time
import numpy as np
import os
import tensorflow as tf
import pandas as pd
from scipy import stats

LLC_FEATURE_BOUNDS = {
    'aileron': [-1, 1],  # 副翼 控制飞机翻滚 [-1,1] left/right
    'rudder': [-1, 1],  # 方向舵 控制飞机转弯（地面飞机方向控制） 0 /enter
    # 'throttle': [0, 1],  # 油门0
    # 'uBody-fps': [0., 600.],  # 飞机沿机身X轴的速度
    # 'vBody-fps': [-200., 200.],  # 飞机沿机身Y轴的速度
    # 'wBody-fps': [-200., 200.],  # 飞机沿机身Z轴的速度
    'pitch-deg': [-90., 90.],  # 飞机俯仰角
    'roll-deg': [-180., 180.],  # 飞机滚转角
    'heading-deg': [0., 360.],  # 飞机朝向
}
LLC_GOAL_BOUNDS = {
    'pitch-deg': [-90., 90.],  # 飞机俯仰角
    'roll-deg': [-180., 180.],  # 飞机滚转角
    'heading-deg': [0., 360.],  # 飞机朝向
}

LLC_ACTION_BOUNDS = {
    'aileron': [-1, 1],  # 副翼 控制飞机翻滚 [-1,1] left/right
    'rudder': [-1, 1],  # 方向舵 控制飞机转弯（地面飞机方向控制） 0 /enter
    # 'throttle': [0, 1],  # 油门0
}

DATA_BOUNDS = {
    'pitch-deg': [-90., 90.],  # 飞机俯仰角
    'roll-deg': [-180., 180.],  # 飞机滚转角
    'heading-deg': [0., 360.],  # 飞机朝向
    'vsi-fpm': [0., 10.0],  # 爬升速度
    'uBody-fps': [0., 600.],  # 飞机沿机身X轴的速度
    'vBody-fps': [-200., 200.],  # 飞机沿机身Y轴的速度
    'wBody-fps': [-200., 200.],  # 飞机沿机身Z轴的速度
    'x-accel-fps_sec': [0., 50.],  # 飞机沿机身X轴的加速度
    'y-accel-fps_sec': [-30., 30.],  # 飞机沿机身Y轴的加速度
    'z-accel-fps_sec': [-300., 300.],  # 飞机沿机身z轴的加速度
    'aileron': [-1, 1],  # 副翼 控制飞机翻滚 [-1,1] left/right
    'elevator': [-1, 1],  # 升降舵 控制飞机爬升 [-1,1] up/down
    'rudder': [-1, 1],  # 方向舵 控制飞机转弯（地面飞机方向控制） 0 /enter
    'throttle0': [0, 1],  # 油门0
    'throttle1': [0, 1],  # 油门1
    'flaps': [0, 1],  # 襟翼 在飞机起降过程中增加升力，阻力  Key[ / ]	Extend / retract flaps
    #TODO: 方向舵调整片
    'a_aileron': [-1, 1],  # 副翼 控制飞机翻滚 [-1,1] left/right
    'a_elevator': [-1, 1],  # 升降舵 控制飞机爬升 [-1,1] up/down
    'a_rudder': [-1, 1],  # 方向舵 控制飞机转弯（地面飞机方向控制） 0 /enter
    'a_throttle0': [0, 1],  # 油门0
    'a_throttle1': [0, 1],  # 油门1
}


MAX_EPISODE = 1000
MAX_EP_STEPS = 200

GAMMA = 0.9
LR_A = 0.001    # learning rate for actor
LR_C = 0.01     # learning rate for critic


def get_lower_upper_bound(bounds):
    '''
    format bound dict to lower and upper array
    '''
    lower = []
    upper = []
    for key in bounds.keys():
        lower.append(bounds[key][0])
        upper.append(bounds[key][1])
    return np.array(lower, dtype=np.float), np.array(upper, dtype=np.float)


np.random.seed(2)
tf.random.set_seed(2)  # reproducible


def _llc_reward(state, goal, old_action, action, reward):
    goal_diff = 0.0
    for key in goal.keys():
        goal_diff += np.math.tanh((state[key] - goal[key])**2)
    goal_diff = goal_diff  # /len(state)

    ## 滚转角和俯仰角不能过大


    action_diff =np.math.tanh(((action - old_action)**2).sum())

    r_ = -0.8*action_diff - 0.4* goal_diff
    return r_


def llc_reward(state, goal, old_action, action, reward):
    #!!! 角度的距离计算需要考虑到360度的情况
    #!!! 需要衡量飞机的飞行情况  是否达到目标; 飞行的安全性;

    goal_diff = 0.0
    # 飞机滚转角
    key = 'roll-deg'
    diff = state[key] - goal[key]
    diff = max(abs(diff), abs(diff+360), abs(diff-360))
    goal_diff += np.math.tanh(diff**2)

    # 飞机朝向
    key = 'heading-deg'
    diff = state[key] - goal[key]
    diff = max(abs(diff), abs(diff+360), abs(diff-360))
    goal_diff += np.math.tanh(diff**2)

    # 飞机俯仰角 无

    ## 滚转角和俯仰角不能过大
    state_penalty = 0.0
    # 滚转角
    state_penalty += (1 - stats.norm(0,
                                     5).pdf(state['roll-deg']) / stats.norm(0, 5).pdf(0))
    # 飞机俯仰角
    state_penalty += (1 - stats.norm(0,
                                     5).pdf(state['pitch-deg']) / stats.norm(0, 5).pdf(0))

    # 倾向于不做动作 动作幅度不能太大
    action_penalty = 0.0
    # 方向舵
    action_penalty += (1 - stats.norm(0,
                                      0.3).pdf(action[1]) / stats.norm(0, 0.3).pdf(0))
    # 副翼
    action_penalty += (1 - stats.norm(0,
                                      0.3).pdf(action[0]) / stats.norm(0, 0.3).pdf(0))

    # 动作具有连续性
    action_diff = np.math.tanh(((action - old_action)**2).sum())

    r_ = 0.2*action_diff + goal_diff + state_penalty + action_penalty
    # print("action_diff :  ", action_diff)
    # print("goal_diff :  ", goal_diff)
    # print("state_penalty :  ", state_penalty)
    # print("action_penalty :  ", action_penalty)
    # print("")
    r_ = -1 * r_
    return r_

class LLC():
    def __init__(self, states=LLC_FEATURE_BOUNDS, goals=LLC_GOAL_BOUNDS, actions=LLC_ACTION_BOUNDS,data_bounds=DATA_BOUNDS,n_old_actions = 0):
        '''
        Our LLC with sepcific sate features and actions list
        ----
        Inputs:
            - states(dict): 状态上下界的字典
                {"feature": [lower, upper],...}
            - goals(dict): 目标状态上下界的字典
                {"feature": [lower, upper],...}
            - actions(dict): 动作空间上下界的字典
                {"feature": [lower, upper],...}
        '''
        # self.var = 3.0  # add randomness to action selection for exploration
        self.var = 0.3

        self.n_states = len(states)
        self.n_goals = len(goals)
        self.n_actions = len(actions)

        self.states = states
        self.goals = goals
        self.databounds = data_bounds

        self.action_bounds = dfer.bounds_dict2arr(actions)

        # 初始化DRL模型
        # 对于ddpg的action bounds 特殊规定
        self.action_bound = (
            self.action_bounds[1]-self.action_bounds[0])/2.0  # 动作空间范围的一半
        self.action_mid = self.action_bounds[0]+self.action_bound  # 动作空间范围的均值
        ## a_ddpg = ddpg_tanh * a_bound
        ## a = a_mid + a_ddpg
        self.ddpg = DDPG(self.n_actions, self.n_states+self.n_goals+self.n_actions*n_old_actions, self.action_bound)

        ## ddpg 模型初始话完成
        self.sess = self.ddpg.sess
        self.saver = self.ddpg.saver

    def load(self, path):
        self.saver.restore(self.sess, path)

    def save(self, path):
        self.saver.save(self.sess, path)

    def choose_action(self, state, goal, old_actions = [] ):
        '''
        input: 
            state(dict):原始数据即可
            goal(dict):原始数据即可
            old_actions(list):3个历史动作的列表
        output:
            action(np.array):
                DRL输出的action再加入一定随机性后的结果,可用于feed_back
            action_true(np.array):
                用于控制的action(DRL 加上均值后的结果)，不可用与feed_back
        '''
        # 过滤输入状态
        s_ = dfer.filter_state(state, bounds=self.states, objtype="array")
        g_ = dfer.filter_state(goal, bounds=self.goals, objtype="array")

        # 输入合并 state 和 goal
        ob =np.append(s_, g_)
        ob = np.append(ob, old_actions)

        action = self.ddpg.choose_action(ob)
        # add randomness to action selection for exploration
        action = action + self.action_mid

        action_true = np.clip(np.random.normal(
            action, self.var), self.action_bounds[0], self.action_bounds[1])

        action = action_true - self.action_mid
        return action, action_true

    def learn(self, state, goal, reward, action, next_state, next_goal,old_actions=[],next_old_actions=[]):
        '''
        Input:
            -state(dict)
                环境返回状态
            -goal(dict)
                目标状态
            -reward(float)
                环境提供的reward
            -action(np.array)
                agent采取的动作
            -next_state(dict)
                获取到的新状态 
            -next_goal(dict)
                获取到的新目标 
        '''
        # 过滤输入状态
        s_ = dfer.filter_state(state, bounds=self.states, objtype="array")
        g_ = dfer.filter_state(goal, bounds=self.goals, objtype="array")

        # 输入合并 state 和 goal
        ob = np.append(s_, g_)
        ob = np.append(ob, old_actions)
        r = reward
        a = action

        n_s_ = dfer.filter_state(
            next_state, bounds=self.states, objtype="array")
        n_g_ = dfer.filter_state(
            next_goal, bounds=self.goals, objtype="array")

        n_ob =np.append(n_s_ ,n_g_)
        n_ob = np.append(n_ob, next_old_actions)

        self.ddpg.store_transition(ob, a, r, n_ob)
        if self.ddpg.pointer > self.ddpg.MEMORY_CAPACITY:
                self.var *= .99995    # decay the action randomness
                self.ddpg.learn()


'''
class HLC():
    def __init__(self):
        pass

    def choose_action(self, state, goal):

        return action

    def learn(self, state, reward, action):
        pass

    def cal_reward(self, state):

        return reward

'''

if __name__ == "__main__":
    # N_F = len(LLC_FEATURES)
    # N_A = len(LLC_ACTIONS)
    # myllc = LLC(N_F, N_A, LLC_ACTION_BOUNDS, LLC_GOALS)

    # myllc.critic_pre_train()
    # myllc.actor_critic_pre_train()
    # myllc.test_actor()
    pass
