"""刻意修改記憶體副本觀察錯誤，不改原始 data 檔案。"""
import argparse
from copy import deepcopy
from BTC import load_btc,analyze_btc
from ETH import load_eth,analyze_eth
from lab_common import DATA,LabError,read_json,run


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--case',choices=['coinbase','missing-prevout','wrong-abi','failed-tx'],required=True)
    args=p.parse_args()
    if args.case in ('coinbase','missing-prevout'):
        tx,b,m=load_btc('A','offline')
        tx=deepcopy(tx)
        if args.case=='coinbase':tx['vin'][0]['is_coinbase']=True
        else:tx['vin'][0]['prevout']=None
        action=lambda:analyze_btc(tx,b,m)
    else:
        tx,r,m=load_eth('A','offline');r=deepcopy(r)
        if args.case=='wrong-abi':action=lambda:analyze_eth(tx,r,m,abi=[])
        else:
            r['status']='0x0';r['logs']=[]
            action=lambda:analyze_eth(tx,r,m)
    print('注意：這是人工修改的教學情境，不是樣本真實交易的新狀態。')
    try:
        result=action()
    except LabError as e:
        print(f'預期觀察到 [{e.code}] {e}')
        print('修復方式：重新執行原本 BTC.py／ETH.py；本程序未更改資料檔。')
    else:
        print('status:',result['status'],'fee_wei:',result['fee_wei'],
              'transfer_confirmed:',result['transfer_confirmed'])
        print('解碼仍可能成功，但 status=0 不能當成功轉帳；已消耗的執行費仍存在。')


if __name__=='__main__':run(main)
