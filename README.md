# Voronoi Diagram Term Project

## 系級、姓名與學號
- **系級**: 資安碩一
- **姓名**: 尤心怡
- **學號**: M133140001

---

## 1. 題目
**Voronoi Diagram Term Project**

本專案旨在使用 Python 與 PyQt5 建構一個基於分治法的 Voronoi Diagram 視覺化系統，具備輸入點集、生成對應 Voronoi 圖的功能，並包含分步操作的說明與測試

---

## 2. 軟體規格書

### 輸出與輸入（資料）規格
1. **輸入**:
   - 使用者於畫布上點擊產生的點座標，或由檔案讀取點資料和邊資料
2. **輸出**:
   - 根據輸入點生成的 Voronoi 圖，包含邊的座標資訊，並以視覺化形式呈現
   - 可以儲存畫布上的點和邊資料，輸出資料格式 : 點 P x y，邊 E x1 y1 x2 y2，座標點以 lexical order順序排列（即先排序第一維座標，若相同，則再排序第二維座標；線段亦以 lexical order 順序排列

### 功能規格與介面規格
![介面設計](pic/program-design.png)
- 畫布區域 : 使用者可以用滑鼠在畫布區域中點擊來產生點
- 按鈕區域 :
  - 「Run」按鈕 : 根據畫布上的點產生 Voronoi 圖
  - 「清空」按鈕 : 可以清除畫面上的點和邊
  - 「Step by Step」按鈕 : 逐步展示 Voronoi 圖生成過程
  - 「讀取檔案」按鈕 : 讀入測試點資料
  - 「儲存檔案」按鈕 : 儲存畫布上的點和邊資料
  - 「載入結果」按鈕 : 讀入結果資料(點和邊)
  - 「下一組點」按鈕 : 讀入多筆資料時使用，可以看下一筆資料
  - 「上一組點」按鈕 : 讀入多筆資料時使用，可以看上一筆資料
  - 「看答案(4點UP)」按鈕 : 直接使用 scipy 套件觀看正確的 Voronoi Diagram
- 座標顯示區域 : 會顯示畫布上點的(x,y)座標

### 目前程式可以解出情況
- 1~3 點 : 直接去計算中垂線即可
- 4~5 點 : 使用 divide-and-conquer 方式，正常情況和共線可以解出來，特殊情況不行
- 所有點共線情況
- 
---

## 3. 軟體說明

### 安裝需求
- Python 環境安裝完整，並包含以下套件：
  - **PyQt5**
  - **SciPy**
  - **numpy**

### 使用方式
1. 啟動程式後，於畫布點擊產生點資料 ![軟體說明-畫點](/pic/usage1.png)
2. 使用者也可以按下「讀取檔案」和「載入結果」按鈕來賭檔 ![軟體說明-讀1](/pic/usage4.png) ![軟體說明-讀1](/pic/usage5.png)
3. 按下「Run」按鈕，會根據畫布上的點產生對應的 Voronoi Diagram ![軟體說明-R](/pic/usage2.png)
4. 按下「Step by Step」按鈕，會逐步展示 Voronoi 圖生成過程 ![軟體說明-S](/pic/usage3.png)
5. 按下「儲存檔案」按鈕，可以儲存畫布上的點和邊資料 ![軟體說明-存](/pic/usage6.png)

---

## 4. 程式設計

### 三點以下
對於三點以下的情況，直接計算三點的外心和中垂線即可找到 Voronoi Diagram
1. **1 點的情況** : 一個點的 Voronoi Diagram 是整個平面 ![點1](/pic/point1.png)
2. **2 點的情況** : 根據兩個點計算垂直平分線的方向向量，將平分線延伸，生成對應的邊 ![點2](/pic/point2.png)
3. **3 點的情況** : 
   - 共線 : 直接計算所有點的垂直平分線
   - 不共線 : 計算三角形外心並生成 Voronoi Diagram，邊的方向是由方向向量和點的內積所決定的 ![點3](/pic/point3.png)

### 四點以上
用 Divide-and-Conquer 方法來分割點集合並逐步合併生成 Voronoi 圖
1. **Divide** : 將點集合分為左右兩部分，如果是奇數個點，左邊點數 +1，然後遞迴計算左右兩邊的 Voronoi Diagram
2. **Convex Hull** : 找到左右兩邊的 Convex Hull，並合併成一個大的，然後求上下切線
   - Andrew's monotone chain
3. **Hyperplane** : 透過上下切線來找 Hyperplane 的起點和終點
4. **Merge** : 找到 Hyperplane 後即可合併左右兩個 Voronoi Diagram

---

## 5. 軟體測試與實驗結果

### 測試環境
- **硬體**:
  - CPU: Intel i5-10300H
  - RAM: 32GB
- **作業系統**: Windows 11
- **開發工具與版本**:
  - Python 3.10
  - PyQt5 5.15.11
  - numpy 1.24.4
  - scipy 1.9.1

### 測試結果
- **三點以下**:
  - ![P3](/pic/test2-3.png)
  - ![P3](/pic/test2-4.png)
  - ![P3](/pic/test2-5.png)
  - ![P3](/pic/test2-6.png)
- **四點以上**: 
  - ![P3](/pic/test3-1.png)
  - ![P3](/pic/test3-4.png)
  - ![P3](/pic/test3-6.png)
- **多點共線**:
  - ![MP](/pic/test4-1.png)
  - ![MP](/pic/test4-2.png)

### 問題與可能解決方案
1. **交點判斷 Bug**:
   - 原因: 預設下一個交點的 y 值一定比上一個交點大，並假設同一 Voronoi edge 僅有一個交點。
   - 可能解決方案: 修改交點判斷邏輯，考慮特殊情況。

