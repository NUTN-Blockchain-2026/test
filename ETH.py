"""ETH 實作入口：交易＋收據＋ABI；只讀資料，不建立／發送交易。"""
try:
    from web3 import Web3
except ImportError:
    raise SystemExit("缺少 web3。請先依 README 安裝 requirements.txt。")

from lab_common import (DATA, LabError, as_int, emit, metadata, parser,
                        read_json, require, rpc, run, units)
from task_functions import calculate_eth_fee, decode_transfer


def load_eth(sample, mode):
    meta = metadata(sample)
    expected = meta["eth"]
    if mode == "offline":
        tx = read_json(DATA / sample / "eth_transaction.json")
        receipt = read_json(DATA / sample / "eth_receipt.json")
    else:
        require(as_int(rpc("eth_chainId",[])) == 1, "CHAIN", "端點不是 Ethereum 主網 chain ID 1。")
        tx = rpc("eth_getTransactionByHash",[expected["tx_hash"]])
        receipt = rpc("eth_getTransactionReceipt",[expected["tx_hash"]])
    require(tx is not None and receipt is not None, "NOT_FOUND",
            "查無交易或收據。可能為錯鏈／供應商歷史資料限制；請使用 offline。")
    return tx,receipt,meta


def analyze_eth(tx, receipt, meta, abi=None):
    expected = meta["eth"]
    tx_hash = expected["tx_hash"].lower()
    require(tx["hash"].lower() == receipt["transactionHash"].lower() == tx_hash,
            "IDENTITY", "交易與收據不是同一筆樣本。")
    require(tx["blockHash"].lower() == receipt["blockHash"].lower() == expected["block_hash"].lower(),
            "IDENTITY", "交易、收據與樣本區塊雜湊不一致。")
    require(as_int(tx["blockNumber"]) == as_int(receipt["blockNumber"]) == expected["height"],
            "IDENTITY", "交易與收據高度不同。")
    require(as_int(tx.get("type",0)) in (0,2), "TYPE", "本教材費用分析只支援普通 L1 type 0／2。")
    require(tx.get("to") is not None, "CONTRACT_CREATION", "本題不是合約建立交易。")
    require(tx["to"].lower() == expected["token_address"].lower(),
            "TOKEN", "交易 to 與本樣本代幣合約不符。")
    if "chainId" in tx:
        require(as_int(tx["chainId"]) == 1, "CHAIN", "交易 chainId 不符。")

    status = as_int(receipt["status"])
    require(status in (0,1), "DATA", "未知的 receipt status。")
    gas_used = as_int(receipt["gasUsed"])
    gas_price = as_int(receipt["effectiveGasPrice"])
    fee = calculate_eth_fee(gas_used,gas_price)
    require(type(fee) is int and fee >= 0, "CALC", "ETH 費用必須回傳非負整數 wei。")
    require(fee == gas_used * gas_price, "MISMATCH", "ETH 費用算式錯誤，請使用實際用量與單價。")

    if abi is None:
        abi = read_json(DATA / "erc20_transfer_abi.json")
    # 無 provider 的 Web3 只在電腦內解碼；完全不需要錢包。
    contract = Web3().eth.contract(address=Web3.to_checksum_address(tx["to"]),abi=abi)
    try:
        function_name, parameters = decode_transfer(contract,tx["input"])
    except NotImplementedError:
        raise
    except Exception:
        raise LabError("ABI", "無法解碼 input；請核對 ABI、樣本及學生解碼函式。")
    require(function_name == "transfer", "ABI", "本題必須為直接 transfer，不支援任意合約呼叫。")
    recipient = Web3.to_checksum_address(parameters["to"])
    raw_amount = as_int(parameters["value"])

    # 只接受這個合約的 Transfer 事件，不能把其他合約的同名事件算進來。
    topic0 = Web3.to_hex(Web3.keccak(text="Transfer(address,address,uint256)"))
    matches = []
    for log in receipt["logs"]:
        if log["address"].lower() != tx["to"].lower() or not log.get("topics"):
            continue
        if log["topics"][0].lower() != topic0.lower() or log.get("removed",False):
            continue
        require(log.get("transactionHash",tx_hash).lower() == tx_hash,
                "IDENTITY", "事件來自不同交易。")
        try:
            event = contract.events.Transfer().process_log(log)
        except Exception:
            raise LabError("LOG", "Transfer 事件格式與 ABI 不符。")
        values = event["args"]
        if (values["from"].lower() == tx["from"].lower()
                and values["to"].lower() == recipient.lower()
                and as_int(values["value"]) == raw_amount):
            matches.append(log["logIndex"])
    # status=0 可以解碼「曾嘗試」做什麼，但不能說轉帳成功。
    require(status == 0 or len(matches) == 1, "LOG_MISMATCH",
            "成功樣本應有一筆完全對應的 Transfer 事件；請核對資料或 ABI。")

    return {"network":expected["network"],"chain_id":1,"tx_hash":tx["hash"],
            "block_number":expected["height"],"from":tx["from"],"transaction_to":tx["to"],
            "status":status,"execution_success":status == 1,"gas_limit":as_int(tx["gas"]),
            "gas_used":gas_used,"effective_gas_price_wei":gas_price,
            "effective_gas_price_gwei":units(gas_price,9),"fee_wei":fee,"fee_ETH":units(fee,18),
            "function":function_name,"token_recipient":recipient,"token_amount_raw":raw_amount,
            "token_decimals":expected["token_decimals"],"token_symbol":expected["token_symbol"],
            "token_amount":units(raw_amount,expected["token_decimals"]),
            "native_value_wei":as_int(tx["value"]),"transfer_log_matches":len(matches),
            "transfer_confirmed":status == 1 and len(matches) == 1,
            "explorer":expected["explorer"],"captured_at_utc":meta["captured_at_utc"]}


def main():
    args = parser("ETH").parse_args()
    tx,receipt,meta = load_eth(args.sample,args.mode)
    rows = analyze_eth(tx,receipt,meta)
    reference = read_json(DATA / args.sample / "reference_eth.json")
    reference_fee = as_int(reference["data"]["fee"]["value"])
    require(rows["fee_wei"] == reference_fee,
            "REFERENCE", "費用與獨立保存的 Blockscout 參考資料不同。")
    rows["reference_fee_wei"] = reference_fee
    rows["independent_fee_matches"] = True
    rows["independent_reference"] = reference["source_url"]
    emit("ETH",args.sample,args.mode,rows,args.out)


if __name__ == "__main__":
    run(main)
