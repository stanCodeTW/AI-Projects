import jieba
import jieba.analyse
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from wordcloud import WordCloud


def main():
    brand_name =\
        ['Anqueen', 'APTON', 'AUX', 'BD', 'CARRIER', 'CHIMEI', 'DAIKIN', 'DIKE', 'FUJITSU',
         'Giaretti', 'GREE', 'HAIER', 'HAWRIN', 'HERAN', 'HITACHI', 'Jiere', 'JJPRO', 'JUZCOOl', 'KOLIN', 'LENDIEN',
         'LG', 'MAXE', 'MIDEA', 'MITSUBISHI重工', 'MITSUBISHI電機', 'NEOKA', 'NEWWIDETECH', 'NIKKO', 'PANASONIC',
         'PROTON', 'RANSO', 'RENFOSS', 'SAMPO', 'SANLUX', 'SAPORO', 'SHARP', 'SONGEN', 'SOWA', 'TAIGA', 'TAIITSU',
         'TATUNG', 'TECO', 'TOSHIBA']
    for i in range(len(brand_name)):
        # 讀入資料
        txtfile = "整理_803.csv"  # 剛才下載存的文字檔
        stopfile = "stop_word.txt"

        # 使用者輸入品牌
        # brand_name = input("請輸入品牌名稱: ")

        # 讀取csv文件
        df = pd.read_csv(txtfile, encoding="utf-8")

        # 根據品牌名稱過濾數據
        filtered_df = df[df['brand'] == brand_name[i]]

        # 獲取評論列並合併成一個字符串
        comments = ' '.join(filtered_df['comment'].astype(str))

        # 讀取停止詞文件
        with open(stopfile, "r", encoding="utf-8") as f:
            stop_words = set(f.read().splitlines())

        # 設定jieba繁體中文字典
        file_path = 'dict.txt'
        jieba.set_dictionary(file_path)

        # 進行斷詞
        seg_list = jieba.lcut(comments, cut_all=False)

        # 去除停止詞
        seg_list = [word for word in seg_list if word not in stop_words and len(word.strip()) > 0]

        # 設定中文字型
        font_path = 'TaipeiSansTCBeta-Bold.ttf'  # 字型路徑
        font_prop = FontProperties(fname=font_path)

        seg_list_str = ' '.join(seg_list)  # 做成字符串

        # 文字雲繪製參數設定
        wc = WordCloud(
            width=1000,
            height=1000,
            background_color='white',  # 背景顏色
            max_words=200,  # 最大分詞數量
            font_path=font_path,  # 若為中文則需引入中文字型(.TTF)
            random_state=42,  # 隨機碼生成各分詞顏色
            prefer_horizontal=0.9  # 調整分詞中水平和垂直的比例
        )

        # 生成詞雲
        wc.generate(seg_list_str)

        # 繪製成圖形
        plt.figure(figsize=(10, 10))
        plt.imshow(wc, interpolation="bilinear")
        plt.axis('off')  # 關掉座標
        plt.title(f"{brand_name[i]}", fontsize=20, fontproperties=font_prop)  # 添加標題
        plt.savefig(f'word_cloud_{brand_name[i]}.png', bbox_inches='tight')  # 保存圖片，包含標題
        # plt.show()  # 展示圖片


if __name__ == "__main__":
    main()
