from torch.utils.tensorboard import SummaryWriter
from torch.optim.lr_scheduler import _LRScheduler
import matplotlib.pyplot as plt
# import tensorflow as tf
import numpy as np
from IPython import display
from matplotlib.ticker import MaxNLocator
from collections import deque
import os
import glob

    
# plot loss by round of game
def loss_plot_per_frame(cur_ep,episode_loss):
    saved_images = deque(maxlen=10)
    plt.figure(figsize=(10, 5))
    x_axis = list(range(1, cur_ep + 1))
    losses = np.array(episode_loss, dtype=np.float32)
    plt.plot(x_axis, losses, label='Loss per Frame', alpha=0.6)
    plt.xlabel('Frame')
    plt.ylabel('Loss')
    plt.title('Training Loss over Frames')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    filename = f'img/{cur_ep}_loss_plot.png'
    saved_images.append(filename)
    if len(saved_images) > 10:
        old_filename = saved_images.popleft()  
        if os.path.exists(old_filename):
            os.remove(old_filename)
            print(f"已刪除舊的圖片: {old_filename}")
    plt.savefig(filename)
    plt.show()


# plot reward by round of game
def reward_plot_per_frame(cur_ep,episode_rewards, img_folder="img",window=10, max_images=5):
    display.clear_output(wait=True)
    display.display(plt.gcf())
    plt.clf()
    plt.title("Training process")
    plt.xlabel('Number of Epesoide')
    plt.ylabel('Rewards')
    x_axis = list(range(1,cur_ep+1))
    if window > 1 and len(episode_rewards) >= window:
        moving_avg = np.convolve(episode_rewards, np.ones(window)/window, mode='valid')
        plt.plot(range(window, len(episode_rewards) + 1), moving_avg, 
                label=f'Moving Average (window={window})', color='r', marker='o')

    plt.plot(x_axis, episode_rewards, label='Frame Reward', color='green')
    plt.gca().xaxis.set_major_locator(MaxNLocator(integer=True))
    plt.xlim(xmin=0)
    plt.show(block=False)
    plt.pause(.1)
    img_path = os.path.join(img_folder, f'reward_plot_ep_{cur_ep}.png')
    plt.savefig(img_path)

         
# plot epsilon by round of game           
def epsilon_plot_per_frame(cur_ep,episode_epsilon, img_folder="img",window=10, max_images=5):
    display.clear_output(wait=True)
    display.display(plt.gcf())
    plt.clf()
    plt.title("Training process")
    plt.xlabel('Number of Epesoide')
    plt.ylabel('Epsilon')
    x_axis = list(range(1,cur_ep+1))
    if window > 1 and len(episode_epsilon) >= window:
        moving_avg = np.convolve(episode_epsilon, np.ones(window)/window, mode='valid')
        plt.plot(range(window, len(episode_epsilon) + 1), moving_avg, 
                label=f'Moving Average (window={window})', color='r', marker='o')

    plt.plot(x_axis, episode_epsilon, label='Frame Reward', color='green')
    plt.gca().xaxis.set_major_locator(MaxNLocator(integer=True))
    plt.xlim(xmin=0)
    plt.show(block=False)
    plt.pause(.1)
    # if len(episode_n) == EPISODES:
    img_path = os.path.join(img_folder, f'epsilon_plot_ep_{cur_ep}.png')
    plt.savefig(img_path)
    png_files = glob.glob(os.path.join(img_folder, '*.png'))
    # 如果 PNG 檔案超過 max_images，則刪除最舊的檔案
    if len(png_files) > max_images:
        # 根據檔案的創建時間排序
        png_files.sort(key=lambda x: os.path.getctime(x))
        # 計算需要刪除的檔案數量
        files_to_delete = png_files[:len(png_files) - max_images]
        for file_path in files_to_delete:
            os.remove(file_path)

