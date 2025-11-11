"""
실시간 시세 테이블 출력 테스트
"""
from rich.console import Console
from rich.table import Table
from rich import box
from datetime import datetime

console = Console()

# 테스트 데이터
buy_info = {
    'stock_name': '중앙첨단소재',
    'stock_code': '051980',
    'buy_price': 10000,
    'quantity': 100,
    'target_profit_rate': 0.01
}

current_price = 10100
buy_price = 10000
profit_rate = (current_price - buy_price) / buy_price

# 실시간 시세 정보 테이블 생성
table = Table(title=f"📊 실시간 시세 정보 (WebSocket)", box=box.ROUNDED, show_header=False)
table.add_column("항목", style="cyan", width=15)
table.add_column("값", style="white")

# 수익률에 따른 색상 결정
profit_color = "red" if profit_rate >= 0 else "blue"
profit_sign = "+" if profit_rate >= 0 else ""

table.add_row("종목명", buy_info['stock_name'])
table.add_row("종목코드", buy_info['stock_code'])
table.add_row("평균 매수가", f"{buy_price:,}원")
table.add_row("현재가", f"{current_price:,}원")
table.add_row(
    "수익률",
    f"[{profit_color}]{profit_sign}{profit_rate*100:.2f}%[/{profit_color}] (목표: +{buy_info['target_profit_rate']*100:.2f}%)"
)
table.add_row(
    "수익금",
    f"[{profit_color}]{profit_sign}{(current_price - buy_price) * buy_info['quantity']:,}원[/{profit_color}]"
)
table.add_row("보유수량", f"{buy_info['quantity']:,}주")
table.add_row("총 투자금액", f"{buy_price * buy_info['quantity']:,}원")
table.add_row("업데이트", datetime.now().strftime("%H:%M:%S"))

print()
console.print(table)
print()

# 손실 케이스도 테스트
print("\n손실 케이스 테스트:")
print("=" * 60)

current_price_loss = 9750
profit_rate_loss = (current_price_loss - buy_price) / buy_price

table2 = Table(title=f"📊 실시간 시세 정보 (WebSocket)", box=box.ROUNDED, show_header=False)
table2.add_column("항목", style="cyan", width=15)
table2.add_column("값", style="white")

profit_color_loss = "red" if profit_rate_loss >= 0 else "blue"
profit_sign_loss = "+" if profit_rate_loss >= 0 else ""

table2.add_row("종목명", buy_info['stock_name'])
table2.add_row("종목코드", buy_info['stock_code'])
table2.add_row("평균 매수가", f"{buy_price:,}원")
table2.add_row("현재가", f"{current_price_loss:,}원")
table2.add_row(
    "수익률",
    f"[{profit_color_loss}]{profit_sign_loss}{profit_rate_loss*100:.2f}%[/{profit_color_loss}] (목표: +{buy_info['target_profit_rate']*100:.2f}%)"
)
table2.add_row(
    "수익금",
    f"[{profit_color_loss}]{profit_sign_loss}{(current_price_loss - buy_price) * buy_info['quantity']:,}원[/{profit_color_loss}]"
)
table2.add_row("보유수량", f"{buy_info['quantity']:,}주")
table2.add_row("총 투자금액", f"{buy_price * buy_info['quantity']:,}원")
table2.add_row("업데이트", datetime.now().strftime("%H:%M:%S"))

console.print(table2)
print()
