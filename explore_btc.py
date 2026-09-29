"""助教延伸：示範正確區塊交易分頁。需要網路；不廣播交易。"""
import argparse
from lab_common import metadata,btc_page,run


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--start-index',type=int,default=0)
    args=p.parse_args()
    txs=btc_page(metadata('A')['btc']['block_hash'],args.start_index)
    print('start_index:',args.start_index,'count:',len(txs))
    for tx in txs:print(tx['txid'],'inputs:',len(tx['vin']),'outputs:',len(tx['vout']))


if __name__=='__main__':run(main)
