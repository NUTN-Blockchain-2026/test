"""課前檢查；預設不連網，可加 --online 測試固定樣本。"""
import argparse
import hashlib
from importlib.metadata import PackageNotFoundError,version
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent


def check_data():
    errors=[]
    data=ROOT/'data'
    try:
        manifest=json.loads((data/'checksums.json').read_text(encoding='utf-8'))
        for name,digest in manifest.items():
            target=(data/name).resolve()
            if not target.is_relative_to(data.resolve()):
                errors.append('不合法的校驗路徑');continue
            if not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest()!=digest:
                errors.append('資料缺少或已變更：'+name)
    except (OSError,ValueError):
        errors.append('無法讀取資料校驗清單')
    return errors


def main():
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--online',action='store_true')
    args=p.parse_args()
    errors=[]
    print('Python:',sys.version.split()[0])
    if sys.version_info[:2]<(3,10):errors.append('需要 Python 3.10 以上；建議使用已測的 3.12。')
    for name,expected in [('requests','2.34.2'),('web3','8.0.0')]:
        try:
            actual=version(name);print(name,actual,'expected',expected)
            if actual!=expected:errors.append(name+' 版本與本教材不同；請按 requirements.txt 安裝。')
        except PackageNotFoundError:errors.append('未安裝 '+name)
    errors.extend(check_data())
    if not errors:
        # 不调用學生尚未完成的計算函式，學生包也可以通过环境检查。
        from web3 import Web3
        abi=json.loads((ROOT/'data/erc20_transfer_abi.json').read_text())
        tx=json.loads((ROOT/'data/A/eth_transaction.json').read_text())
        try:
            fn,_=Web3().eth.contract(abi=abi).decode_function_input(tx['input'])
            if fn.fn_name!='transfer':errors.append('ABI 解碼檢查不符')
        except Exception:errors.append('web3.py 解碼自我檢查失敗')
    if args.online and not errors:
        from BTC import load_btc
        from ETH import load_eth
        from lab_common import LabError
        for name,loader in [('BTC',load_btc),('ETH',load_eth)]:
            try:loader('A','online');print(name,'online read OK')
            except LabError as e:errors.append(f'{name} [{e.code}] {e}')
    if errors:
        for e in errors:print('FAIL:',e)
        print('網路失敗不代表離線不能做；未裝套件或資料損壞則需先修復。')
        return 1
    print('PASS: 環境、ABI 解碼與全部樣本檔案校驗正常。')
    return 0


if __name__=='__main__':raise SystemExit(main())
