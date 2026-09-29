"""BTC 實作入口：固定樣本 → 載入／查詢 → 檢查 → 計算 → 核對 → 匯出。"""
from lab_common import (DATA, LabError, as_int, btc_get, emit, metadata,
                        parser, read_json, require, run, units)
from task_functions import calculate_btc


def load_btc(sample, mode):
    meta = metadata(sample)
    expected = meta["btc"]
    if mode == "offline":
        tx = read_json(DATA / sample / "btc_transaction.json")
        block = read_json(DATA / sample / "btc_block.json")
    else:
        # 從高度查 hash、再取 block 與指定交易，不隨機抽一筆。
        block_hash = btc_get(f"/block-height/{expected['height']}", want_text=True)
        require(block_hash == expected["block_hash"], "IDENTITY", "高度對應的區塊與樣本不符。")
        block = btc_get(f"/block/{block_hash}")
        tx = btc_get(f"/tx/{expected['txid']}")
    return tx, block, meta


def analyze_btc(tx, block, meta):
    expected = meta["btc"]
    require(tx["txid"] == expected["txid"], "IDENTITY", "交易 txid 與樣本不符。")
    require(block["id"] == expected["block_hash"] and block["height"] == expected["height"],
            "IDENTITY", "區塊資料與樣本不符。")
    require(tx["status"].get("confirmed") is True, "PENDING", "本題必須使用已確認交易。")
    require(tx["status"].get("block_hash") == block["id"] and
            tx["status"].get("block_height") == block["height"],
            "IDENTITY", "交易所屬區塊與提供區塊不同。")
    vin, vout = tx["vin"], tx["vout"]
    require(bool(vin) and bool(vout), "DATA", "輸入或輸出清單為空。")
    require(not any(item.get("is_coinbase") for item in vin),
            "COINBASE", "這是 coinbase，不能套用一般交易費用公式。")
    for item in vin:
        require(isinstance(item.get("prevout"), dict) and "value" in item["prevout"],
                "MISSING_PREVOUT", "缺少輸入的 prevout.value，不能當成零。")
        require(type(item["prevout"]["value"]) is int,
                "DATA", "BTC 金額預期為整數 satoshi。")
        as_int(item["prevout"]["value"])
    for item in vout:
        require(type(item["value"]) is int, "DATA", "BTC 輸出金額預期為整數。")
        as_int(item["value"])

    input_total, output_total, fee = calculate_btc(vin, vout)
    require(all(type(n) is int for n in (input_total, output_total, fee)),
            "CALC", "請用整數 satoshi，不要先轉浮點 BTC。")
    require(fee >= 0 and input_total >= 0 and output_total >= 0,
            "CALC", "得到負數；請核對加總欄位與減法方向。")
    require(input_total - output_total == fee, "CALC", "差額與回傳費用不一致。")
    require(fee == as_int(tx["fee"]), "MISMATCH", "自行計算的 BTC fee 與 API 原始 fee 不同。")

    rows = {"network": expected["network"], "block_height": block["height"],
            "block_hash": block["id"], "txid": tx["txid"], "coinbase": False,
            "input_count": len(vin), "output_count": len(vout),
            "input_total_sat": input_total, "output_total_sat": output_total,
            "fee_sat": fee, "fee_BTC": units(fee,8),
            "reference_fee_sat": tx["fee"], "fee_matches": True,
            "explorer": expected["explorer"], "captured_at_utc": meta["captured_at_utc"]}
    # 保留逐筆金額，方便學生證明沒有漏掉找零或其他輸出。
    for i,item in enumerate(vin):
        rows[f"input_{i}"] = f"{item['prevout'].get('scriptpubkey_address','無一般地址')} | {item['prevout']['value']} sat"
    for i,item in enumerate(vout):
        rows[f"output_{i}"] = f"{item.get('scriptpubkey_address','無一般地址')} | {item['value']} sat"
    return rows


def main():
    args = parser("BTC").parse_args()
    tx, block, meta = load_btc(args.sample,args.mode)
    rows = analyze_btc(tx,block,meta)
    reference = read_json(DATA / args.sample / "reference_btc.json")
    require(rows["fee_sat"] == as_int(reference["data"]["fee"]),
            "REFERENCE", "費用與獨立保存的 mempool.space 參考資料不同。")
    rows["independent_reference"] = reference["source_url"]
    rows["independent_fee_matches"] = True
    emit("BTC",args.sample,args.mode,rows,args.out)


if __name__ == "__main__":
    run(main)
