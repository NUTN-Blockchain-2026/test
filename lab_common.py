"""共用工具：檔案、單位、HTTP、唯讀 RPC 與報表。

所有路徑以此檔案的位置為基準，不要求使用者一定從特定工作目錄執行。
"""
import argparse
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import json
import os
from pathlib import Path
import re
import sys
import time

try:
    import requests
except ImportError:
    raise SystemExit("缺少 requests。請先依 README 安裝 requirements.txt。")

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DEFAULT_RPC = "https://ethereum-rpc.publicnode.com"
DEFAULT_BTC = "https://blockstream.info/api"
# RPC 使用 HTTP POST 不代表上鏈；只准以下查詢方法通過。
READ_METHODS = {"eth_chainId", "eth_getTransactionByHash",
                "eth_getTransactionReceipt", "eth_getBlockByNumber"}


class LabError(Exception):
    """可預期的課堂錯誤：讓訊息比一大串 traceback 更好理解。"""
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


def require(condition, code, message):
    if not condition:
        raise LabError(code, message)


def as_int(value):
    """接受非負整數、十進位字串或 RPC 的 0x 十六進位字串。"""
    if isinstance(value, bool):
        raise LabError("DATA", "布林值不能當成金額。")
    try:
        if isinstance(value, int):
            result = value
        elif isinstance(value, str):
            result = int(value, 16 if value.startswith("0x") else 10)
        else:
            raise ValueError()
    except (TypeError, ValueError):
        raise LabError("DATA", "預期整數或 0x 數字，實際資料不符。")
    require(result >= 0, "DATA", "本欄位不能是負數。")
    return result


def units(raw, decimals):
    """以 Decimal 轉顯示單位，避免 float 的二進位小數誤差。"""
    raw = as_int(raw)
    require(isinstance(decimals, int) and 0 <= decimals <= 36,
            "DATA", "不支援的 decimals。")
    with localcontext() as ctx:
        ctx.prec = 120
        return format(Decimal(raw) / (Decimal(10) ** decimals), f".{decimals}f")


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise LabError("FILE", f"無法讀取 JSON：{Path(path).name}。請確認已解壓縮完整資料包。")


def metadata(sample):
    require(sample in ("A", "B", "C"), "INPUT", "樣本只能為 A、B 或 C。")
    return read_json(DATA / sample / "metadata.json")


def http(url, payload=None, want_text=False):
    """最多 2 次請求；僅逾時、連線中斷、429 與 5xx 會重試。

    不直接印出 URL 或底層例外，避免自訂端點含 Key 時洩漏。
    """
    for attempt in range(2):
        try:
            response = requests.request(
                "GET" if payload is None else "POST", url,
                json=payload,
                headers={"User-Agent": "BlockchainTeachingLab/1.0"},
                timeout=(3.05, 8),
            )
        except (requests.Timeout, requests.ConnectionError):
            if attempt == 0:
                time.sleep(0.5)
                continue
            raise LabError("NETWORK", "連線或讀取逾時。請改 --mode offline，勿一直重跑。")
        except requests.RequestException:
            raise LabError("NETWORK", "請求失敗；檢查端點設定，或改用 offline。")

        status = response.status_code
        if (status == 429 or 500 <= status <= 599) and attempt == 0:
            time.sleep(0.5)
            continue
        require(status == 200, "HTTP", f"服務回傳 HTTP {status}；可改用 --mode offline。")
        if want_text:
            return response.text.strip()
        try:
            return response.json()
        except ValueError:
            raise LabError("JSON", "服務回傳的不是有效 JSON；可能是錯誤頁或限制頁。")


def rpc(method, params):
    require(method in READ_METHODS, "READ_ONLY", "本教材只允許指定的唯讀 RPC 方法。")
    endpoint = os.environ.get("ETH_RPC_URL", DEFAULT_RPC)
    body = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    result = http(endpoint, payload=body)
    require(isinstance(result, dict), "RPC", "RPC 回應不是物件。")
    require("error" not in result, "RPC", "RPC 拒絕查詢；可能不支援歷史資料，請用 offline。")
    require("result" in result, "RPC", "RPC 回應缺少 result。")
    return result["result"]


def btc_get(path, want_text=False):
    base = os.environ.get("BTC_API_BASE", DEFAULT_BTC).rstrip("/")
    return http(base + path, want_text=want_text)


def btc_page(block_hash, start_index=0):
    """區塊交易分頁是 0、25、50，不是上一筆 txid。"""
    require(bool(re.fullmatch(r"[0-9a-fA-F]{64}", block_hash)), "INPUT", "區塊雜湊格式錯誤。")
    require(type(start_index) is int and start_index >= 0 and start_index % 25 == 0,
            "INPUT", "分頁起始索引必須是 0、25、50 等。")
    return btc_get(f"/block/{block_hash}/txs/{start_index}")


def parser(chain):
    p = argparse.ArgumentParser(description=f"{chain} 唯讀交易實作，預設離線。")
    p.add_argument("--sample", choices=["A", "B", "C"], default="A")
    p.add_argument("--mode", choices=["offline", "online"], default="offline")
    p.add_argument("--out", type=Path, default=ROOT / "reports")
    return p


def emit(chain, sample, mode, rows, out):
    """終端、Markdown、JSON 使用同一份結果；每次生成新檔，不覆蓋前次。"""
    now = datetime.now(timezone.utc)
    report = {"chain": chain, "sample": sample, "mode": mode,
              "generated_at_utc": now.isoformat(), "results": rows}
    lines = [f"# {chain} 樣本 {sample}", "", f"模式：{mode}",
             "這是公開歷史交易的讀取結果；本次沒有簽名、發送交易或支付 Gas。", ""]
    for key, value in rows.items():
        lines.append(f"- {key}：{value}")
    text = "\n".join(lines) + "\n"
    out = Path(out)
    # 不允許把新報表寫到教材原始樣本目錄。
    require(not out.resolve().is_relative_to(DATA.resolve()),
            "OUTPUT", "報表請存到 reports 或其他資料夾，不要寫入 data。")
    try:
        out.mkdir(parents=True, exist_ok=True)
        stem = f"{chain}_{sample}_{mode}_{now.strftime('%Y%m%dT%H%M%S%fZ')}"
        (out / f"{stem}.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
        (out / f"{stem}.md").write_text(text,encoding="utf-8")
    except OSError:
        raise LabError("OUTPUT", "無法保存結果；請選擇可寫入的 --out 資料夾。")
    print(text)
    print("報表已保存：", out / f"{stem}.md")
    return report


def run(main):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        main()
    except LabError as e:
        print(f"[{e.code}] {e}", file=sys.stderr)
        raise SystemExit(2)
    except NotImplementedError as e:
        print(f"[TODO] {e}", file=sys.stderr)
        raise SystemExit(3)
    except (KeyError, TypeError, ValueError) as e:
        print(f"[DATA] 欄位或學生函式回傳格式有誤（{type(e).__name__}）。請核對資料與手冊。",file=sys.stderr)
        raise SystemExit(2)
