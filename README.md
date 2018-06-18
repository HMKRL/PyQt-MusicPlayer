# 2018 DBMS final project

contributed by <`梁祐承`>

## 系統架構與環境
- Ubuntu 18.04
- Python 3.6.5
- PyQt5 5.9.2

## ER & Relation Schema
![](https://raw.githubusercontent.com/HMKRL/PyQt-MusicPlayer/master/Pictures/ER.png)

![](https://raw.githubusercontent.com/HMKRL/PyQt-MusicPlayer/master/Pictures/Tables.png)

## 介面截圖 & 使用說明

- 音樂播放界面
![](https://raw.githubusercontent.com/HMKRL/PyQt-MusicPlayer/master/Pictures/db1.png)

- DB指令query
![](https://raw.githubusercontent.com/HMKRL/PyQt-MusicPlayer/master/Pictures/db2.png)

- button query
![](https://raw.githubusercontent.com/HMKRL/PyQt-MusicPlayer/master/Pictures/db3.png)

- 加歌: 拖放音樂檔案(限flac檔) 會自動讀標籤INSERT
- 選歌: 點擊查詢結果
- 刪資料: 選取資料後按delete

## table, attribute, relationship 的意義和關係
- Table
    - Company: 唱片公司
        - Name: 名稱
        - Since: 成立年份
        - Location: 公司地點
    - Album: 專輯
        - Title: 標題
        - Year: 專輯年份
    - Artist: 演出者
        - Name: 姓名
        - Since: 出生或成立年份
    - Song: 曲目
        - Title: 曲名
        - length: 長度(秒)
    - Composer: 作曲
        - Name: 姓名
        - Birthday: 出生年份
        - Gender: 性別

- *_ID 為所有Table的PK, 或出現在其他Table作為FK
