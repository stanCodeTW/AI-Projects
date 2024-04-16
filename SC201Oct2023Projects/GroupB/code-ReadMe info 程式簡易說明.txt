程式執行順序如下所示：
Pre_split_file.ipynb
用於將原始圖片隨機依照train, val, test切割，並轉存到對應的資料夾中
Prototype v02.ipynb
用於讀取資料並訓練ResNet50模型
簡易的結果判讀
輸出權重：resnet50_finetuned_weights_0325_6_800.pth
Data Post-Processing.ipynb
讀取test data跟權重，進行進階結果判讀
Confusion matrix
Saliency map
Gradio_example.ipynb
讀取權重，建立gradio互動頁面
Line bot
讀取權重，串接ngrok和Line Developer的Messaging API，用Line進行互動