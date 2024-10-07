import torch
from torchsummary import summary
import numpy as np
import random
from train import get_player_information
from agent_duelingdqn import DuelingLSTMDQN
import lf2gym
import os, sys
from time import sleep
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--player", default="Freeze", help="your character")
parser.add_argument("--opponent", default="Louis", help="your enemy")
parser.add_argument("--interval", default=0.2, help="your enemy")
args = parser.parse_args()
sys.path.append(os.path.abspath('..'))


def act(main_agent, state, agent_info, action, action_size, epsilon):
    """
    選擇動作的函數，根據epsilon-greedy策略決定是隨機選擇還是由模型決定。
    
    args：
        main_agent (DuelingLSTMDQN): 主要的DQN代理模型。
        state (torch.Tensor): 當前狀態。
        agent_info (torch.Tensor): 代理的附加資訊。
        action (torch.Tensor): 上一次的動作。
        action_size (int): 動作空間的大小。
        epsilon (float): 探索率，決定隨機選擇動作的概率。
        
    rerurn：
        int: 選擇的動作。
    """
    if np.random.rand() <= epsilon:
         # 以epsilon的概率隨機選擇動作 
        return random.randrange(action_size)
    # 使用模型預測Q值
    _, actions_out, _ = main_agent(state, agent_info, action)
    # 選擇具有最高Q值的動作
    return torch.argmax(actions_out).item()

# 創建遊戲環境
env = lf2gym.make(startServer=True, wrap='skip4', driverType=lf2gym.WebDriver.Chrome,
                  characters=[lf2gym.Character[args.player], lf2gym.Character[args.opponent]],
                  difficulty=lf2gym.Difficulty.Dumbass)
ep_rew, done = 0, False  # 初始化累積獎勵及遊戲是否結束 （done)
state_size = env.observation_space.n # 獲取狀態空間的大小（x, y）
action_size = env.action_space.n  # 獲取動作空間的大小
main_agent = DuelingLSTMDQN(state_size[0], state_size[1], action_size)
print('load model...')
# 載入預訓練的模型權重
main_agent.load_state_dict(torch.load("duelingdqn.pth"))
main_agent.eval()

state = env.reset()  # Reset environment
done = False
epsilon = 1.0
action = random.randrange(action_size)
while not done:
    with torch.no_grad():  # No gradient computation for testing
        player_info = get_player_information(env.get_detail())
        agent_info = torch.as_tensor(np.array(player_info, dtype=np.float32)).unsqueeze(0)
        state_in = torch.as_tensor(np.array(state, dtype=np.float32)).permute(2, 0, 1).unsqueeze(0)
        _action_last_episode = torch.as_tensor(np.array(action, dtype=np.float32).reshape((1,1)))
        # 根據模型和epsilon選擇當前動作
        action = act(main_agent, state_in, agent_info, _action_last_episode, action_size, epsilon)
   
    # 更新epsilon，逐漸減少 exploration
    if epsilon > 0.01:
        epsilon *= 0.99
    # 透過環境取得資料
    next_state, reward, done, _ = env.step(action)
    print('player1 took action %d.' % action)
    state = next_state # 更新當前狀態
    sleep(args.interval)
env.close()

