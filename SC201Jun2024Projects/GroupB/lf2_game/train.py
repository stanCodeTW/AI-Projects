import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from agent_duelingdqn import *
from lf2gym import *
import numpy as np
import argparse 
from util import *

N_BUF = 64 # Replay Buffer 大小
N_BAT = 32  # 訓練時使用 mini-batch 大小
DISC = 0.99  # discount factor
NUM_EPISODES = 100 # 總訓練回合數
FRAME_MAX = 700  # 每個回合的最大幀數
LR = 0.0005  # 學習率
EPS_START = 1.0  # 初始 epsilon
EPS_END = 0.01  # 最終 epsilon
EPS_DECAY = 1000  # epsilon 衰減速率
ESP_DECAY_FRACTION = 0.3  # epsilon 衰減分數
DECAY_EPSOIDE = int(NUM_EPISODES * 800 * ESP_DECAY_FRACTION)  # epsilon 衰減回合數
AGENT = Character.Freeze  # 選擇的代理角色
AI = Character.Louis  # 選擇的對手角色
LOAD_FROM_MODEL = True  # 是否從模型載入
HEADLESS = False  # 是否以無頭模式運行
TRAINING = True  # 是否進行訓練
MODEL_PATH = "duelingdqn_model0927.pth"  # 模型儲存路徑

parser = argparse.ArgumentParser()
parser.add_argument("--player", default = AGENT, help="your character")  # the AI
parser.add_argument("--opponent", default = AI, help="your enemy")  # the AI's enemy
parser.add_argument("--interval", default=0.9, help="interval between actions")
args = parser.parse_args()


def select_epsilon_greedy_action(env, main_agent, state, agent_info, action, epsilon, ep_step):
    if epsilon > EPS_END:
        epsilon -= ep_step  # 衰減 epsilon
    if np.random.rand() <= epsilon:
        return env.action_space.sample(), epsilon  # 以 epsilon 概率隨機選擇動作
    state = torch.as_tensor(state, dtype=torch.float32).permute(0, 3, 1, 2)
    action = torch.as_tensor(action, dtype=torch.float32)
    agent_info = torch.as_tensor(agent_info, dtype=torch.float32)
    agent_info = agent_info.unsqueeze(0)  # 增加批次維度
    # 通過模型計算 Q 值
    qs = main_agent(state, agent_info, action).cpu().data.numpy()
    return np.argmax(qs), epsilon  # 選擇 Q 值最高的動作
            
class ReplayBuffer(object):
    def __init__(self, size):
        self._size = size  # Buffer 最大容量
        self.buffer = []  # 儲存經驗的列表
        self._next_idx = 0  # 下一個插入的位置

    def add(self, state, player_info, action, reward, next_state, done):
        if self._next_idx >= len(self.buffer):
            self.buffer.append((state, player_info, action, reward, next_state, done))
        else:
            self.buffer[self._next_idx] = (state, player_info, action, reward, next_state, done)
        self._next_idx = (self._next_idx + 1) % self._size  # 更新 layer index


    def __len__(self):
        return len(self.buffer)

    def batch_sample(self, num_samples, state_size_x, state_size_y):
        states, agent_infos, actions, rewards, next_states, dones = [], [], [], [], [], []
        idx = np.random.choice(len(self.buffer), num_samples, replace=False)
        for i in idx:
            elem = self.buffer[i]
            state, player_info, action, reward, next_state, done = elem
            states.append(np.reshape(state, (state_size_x, state_size_y, 4)))
            agent_infos.append(player_info)
            actions.append(np.array(action))
            rewards.append(reward)
            next_states.append(np.reshape(next_state, (state_size_x, state_size_y, 4)))
            dones.append(done)

        states = torch.as_tensor(np.array(states, dtype=np.float32))
        actions = torch.as_tensor(np.array(actions, dtype=np.float32))
        agent_infos = torch.as_tensor(np.array(agent_infos, dtype=np.float32))
        rewards = torch.as_tensor(np.array(rewards, dtype=np.float32))
        next_states = torch.as_tensor(np.array(next_states, dtype=np.float32))
        dones = torch.as_tensor(np.array(dones, dtype=np.float32))
        return states, agent_infos, actions, rewards, next_states, dones


# 從遊戲中獲取玩家資訊
def get_player_information(env_details):
    player1_info = env_details[0] # 玩家資訊
    player2_info = env_details[1] # 對手資訊
    return np.array([
        player1_info['hp'], player1_info['mp'], player1_info['x'], player1_info['y'], player1_info['z'],
        player1_info['vx'], player1_info['vy'], player1_info['vz'],
        player2_info['hp'], player2_info['mp'], player2_info['x'], player2_info['y'], player2_info['z'],
        player2_info['vx'], player2_info['vy'], player2_info['vz']
    ])


def train(main_nn, target_nn, states, agent_infos, actions,
          action_size, rewards, next_states, dones, loss_fn, optimizer):
    states = states.permute(0, 3, 1, 2)  # states shape: torch.Size([2, 4, 160, 380])
    next_states = next_states.permute(0, 3, 1, 2)  # next_states shape: torch.Size([2, 4, 160, 380])
    # 計算下一狀態的最佳動作索引（Q-NN）
    next_qs_argmax = main_nn(next_states, agent_infos, actions).argmax(dim=-1, keepdim=True)  # [batch, 1]
    # 從 Target Q-NN 獲取對應的 Q 值
    masked_next_qs = target_nn(next_states, agent_infos, actions).gather(1, next_qs_argmax).squeeze()  # [batch]
    # 計算目標 Q 值
    mask = (1.0 - dones) * DISC 
    target = rewards + mask * masked_next_qs 
    # 從主網絡中獲取當前狀態下選擇的動作的 Q 值
    masked_qs = main_nn(states, agent_infos, actions).gather(1, actions.unsqueeze(dim=-1).long()).squeeze()
    # 計算損失
    loss = loss_fn(masked_qs, target.detach())
    optimizer.zero_grad()  # 清除之前的梯度
    loss.backward()  # 反向傳播
    optimizer.step()  # 更新參數
    return loss


def save_model(model):
    torch.save(model.state_dict(), './duelingdqn.pth')
    print("Model saved")


def load_model(model):
    model.load_state_dict(torch.load(MODEL_PATH))
    print("Model loaded")


def select_model(tpye_number,state_size,action_size):
    main_agent, target_agent = None, None
    if tpye_number == 1:
        main_agent = DuelingLSTMDQN(state_size[0], state_size[1], action_size)
        target_agent = DuelingLSTMDQN(state_size[0], state_size[1], action_size)
    # elif tpye_number == 2:
    #     main_agent = DuelingDQN(state_size[0], state_size[1], action_size)
    #     target_agent = DuelingDQN(state_size[0], state_size[1], action_size)
    # elif tpye_number == 3:
    #     main_agent = DQN(state_size[0], state_size[1], action_size)
    #     target_agent = DQN(state_size[0], state_size[1], action_size)
    return main_agent, target_agent


def main():
    selected_model = input("choose your model with number : \n [1] DeulingLSTM-DQN\n [2] DeulingL DQN\n [3] DQN\n enter:")
    # launch the game in web
    env = make(startServer=True, driverType=WebDriver.Chrome,
               background=Background.Stanley_Prison,
               characters=[args.player, args.opponent],  # [Me/AI]
               difficulty=Difficulty.Crusher,
               action_options=['Basic', 'AJD','Full Combos'],  # action space
               headless=HEADLESS,
               rewardList=['hp'],
               versusPlayer=False)
    
    # 獲取狀態空間和動作空間的大小
    state_size = env.observation_space.n  
    action_size = env.action_space.n
    
    # 選擇並初始化模型
    main_agent,target_agent =  select_model(int(selected_model),state_size,action_size)
    loss_fn = nn.MSELoss()
    # loss_fn = nn.MSELoss()
    optimizer = optim.Adam(main_agent.parameters(), lr=LR)
    # save the infomation of agent and env
    buffer = ReplayBuffer(size=N_BUF)
    epsilon = EPS_START
    cur_frame, ep_reward, loss, rewards_per_ep, loss_total, ep_lst = 0,0,0,[],0, []
    for e in range(1, NUM_EPISODES+1):
        state = env.reset()
        print(f"start with {e}")
        
        # 如果設定為從模型載入，則載入模型權重
        if LOAD_FROM_MODEL:
            load_model(main_agent)
            
        done = False
        epsilon_step = (epsilon - EPS_END) / DECAY_EPSOIDE # 每步 epsilon 衰減量Í
        previous_player_hp, previous_enemy_hp, previous_player_mp = None, None, None
        while not done:
            # env.start_recording()
            player_info = get_player_information(env.get_detail())
            action_last_episode = 0.0
            _action_last_episode = np.reshape(action_last_episode, (1, 1))
            # 將狀態標準化並增加批次維度
            state_in = np.expand_dims(np.array(state) / 255.0, axis=0)
            action,epsilon = select_epsilon_greedy_action(env, main_agent, state_in, player_info, _action_last_episode, epsilon, epsilon_step)
            ep_lst.append(epsilon) # 記錄 epsilon
            next_state, reward, done, _ = env.step(action)
            if env.get_detail():
                # 檢查對手是否被擊敗
                if not done and env.get_detail()[1]['hp'] == 0:
                    reward += 30  # 對手被擊敗獎勵
                if previous_player_hp is not None:
                    # 如果玩家被擊中，給予懲罰
                    if player_info[0] < previous_player_hp:
                        print("玩家受到傷害")
                        reward -= 5
                    # 如果成功攻擊對手，給予獎勵
                    if player_info[8] < previous_enemy_hp:
                        print("成功攻擊對手")
                        reward += 15
                    # 魔量管理獎勵
                    if (player_info[2] < previous_player_mp and 
                        player_info[8] < previous_player_mp and
                        abs(player_info[4] - player_info[12]) < 10):
                        print("空間攻擊")
                        reward += 10    
            # 更新之前的生命值和魔力值
            previous_player_hp = player_info[0]
            previous_enemy_hp = player_info[8]
            previous_player_mp = player_info[2]
            ep_reward += reward  # 累積回合獎勵
            rewards_per_ep.append(ep_reward)  # 記錄每回合的獎勵
            buffer.add(state, player_info, action, reward, next_state, done)  # 添加經驗到 Replay Buffer
            state = next_state  # 更新當前狀態
            cur_frame += 1  # 更新畫面幀數
            # 如果進行訓練且 Replay Buffer 中有足夠的樣本
            if TRAINING and len(buffer) >= N_BAT:   
                # 從 Replay Buffer 中抽取一個 mini-batch             
                states, agent_infos, actions, rewards, next_states, dones = buffer.batch_sample(N_BAT,
                                                                                                state_size[0],
                                                                                                state_size[1])
                states = states.type(torch.FloatTensor) / 255
                next_states = next_states.type(torch.FloatTensor) / 255
                loss = train(main_agent, target_agent, states, agent_infos, actions,
                                action_size, rewards, next_states, dones, loss_fn, optimizer)
                loss_total += loss.detach().item() # 累積損失

            # update model parameteres 
            if cur_frame % FRAME_MAX == 0:
                target_agent.load_state_dict(main_agent.state_dict()) # 更新 Target Q-NN 模型參數
                
            if e % 1 == 0:
                reward_plot_per_frame(cur_frame, rewards_per_ep, window=10)  # 繪製獎勵圖
                epsilon_plot_per_frame(cur_frame, ep_lst, window=10)  # 繪製epsilon圖
            
            # 如果回合結束，重置獎勵和損失
            if done:
                print("total reward is", ep_reward)
                ep_reward = 0
                loss_total = 0 
                # loss_plot_per_frame(cur_frame-(N_BAT-1), loss_lst) 
                    
            if e % 1 == 0:
                save_model(main_agent)
            
    env.close()


if __name__ == '__main__':
    main()


