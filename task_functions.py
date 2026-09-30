"""學生版：完成三題。只修改這個檔案，不需重寫連線或報表程式。

執行 BTC.py 或 ETH.py 時，未完成的題目會顯示清楚提示。
"""


def calculate_btc(vin, vout):
    """題一：回傳 (輸入總額, 輸出總額, 手續費)，全部為整數 satoshi。

    輸入金額在 item['prevout']['value']；輸出在 item['value']。
    要加總所有項目，不能只取第 0 筆。前置檢查已排除 coinbase。
    """
    input_total=sum(item["prevout"]["value"] for item in vin)
    output_total=sum(item["value"] for item in vout)
    fee=input_total-output_total
    return input_total,output_total,fee
    raise NotImplementedError("請完成題一 calculate_btc：兩個加總與一個差額。")


def calculate_eth_fee(gas_used, effective_gas_price):
    """題二：以實際 Gas 用量與實際單價算出整數 wei。"""
    raise NotImplementedError("請完成題二 calculate_eth_fee：實際費用算式。")


def decode_transfer(contract, input_data):
    """題三：呼叫 contract.decode_function_input(input_data)。

    該方法回傳 function 與 parameters。
    請回傳 (function 的 fn_name, 轉為 dict 的 parameters)。
    """
    raise NotImplementedError("請完成題三 decode_transfer：使用 ABI 解碼。")
