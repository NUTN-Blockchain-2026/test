# 第一次區塊鏈實作：交易資料解析與費用核算

這是一份幫助你理解區塊鏈基礎資料結構的實作作業。你將透過撰寫 Python 程式碼，解析比特幣 (BTC) 與以太坊 (ETH) 的真實歷史交易紀錄，並計算交易手續費與代幣轉帳結果。
本包僅查詢歷史交易，不需真實錢包、代幣或 API Key。
作業目標
了解 BTC 的 UTXO 模型，並透過程式計算交易手續費。

解析 ETH 交易收據 (Receipt) 中的 Gas 用量，計算實際執行費用。

使用 ABI (Application Binary Interface) 解析 ERC-20 代幣轉帳事件。

---

## 一、 接取專屬作業儲存庫

點擊本頁面右上角的綠色按鈕  Use this template，選擇 Create a new repository。

將新儲存庫建立在NUTN-Blockchain-2026組織下（設定成Public）。

將你專屬的儲存庫下載到本地端電腦。



## 二、 本地端環境建置
請確認你的電腦已安裝 Python (建議版本 3.12)。打開終端機 (Terminal) 或 PowerShell，並進入專案資料夾。
1. 建立虛擬環境
```powershell
# Windows
py -3.12 -m venv .venv

# Mac/Linux
python3 -m venv .venv
```
2. 安裝相依套件
```powershell
# Windows
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# Mac/Linux
.venv/bin/python -m pip install -r requirements.txt
```
3. 檢查環境與資料
```powershell
# Windows
.\.venv\Scripts\python.exe check_env.py

# Mac/Linux
./.venv/bin/python check_env.py
```

## 三、 完成核心程式碼 (TODO)
本次作業你需要修改的檔案只有一個：task_functions.py。
打開它，你會看到三個標註 TODO 的函式：

calculate_btc(vin, vout)：計算 BTC 一般交易的手續費。

calculate_eth_fee(gas_used, effective_gas_price)：計算 ETH 實際執行的 wei 費用。

decode_transfer(contract, input_data)：解碼 ETH 交易的 input 資料。

請根據註解提示與課堂所學，完成這三個函式的邏輯。

## 四、 本地端測試
在完成程式碼後，你可以透過以下指令在本地端測試三個歷史樣本 (A, B, C)：
測試 BTC 樣本：
```Bash
.\.venv\Scripts\python.exe BTC.py --sample A
```
測試 ETH 樣本：
```Bash
.\.venv\Scripts\python.exe ETH.py --sample A
```
如果終端機成功印出報表且未出現任何 [CALC] 或 [MISMATCH] 的紅字錯誤，請繼續將 --sample A 換成 B 和 C 進行測試。

## 五、 上傳到到 GitHub 進行雲端批改
當你在本地端確認所有樣本皆能正確執行後，請將程式碼上傳到到 GitHub 之後會自動批改

系統會在雲端自動測試你的程式碼。

如果執行紀錄顯示  綠色打勾，恭喜你完成本次作業！

如果顯示紅色叉叉，請點進去查看錯誤日誌 (Log)，了解是哪個測試條件失敗，並回到本地端修正程式碼後重新測試。

也可以點擊上方的 Action 去查看錯誤日誌 (Log)。
