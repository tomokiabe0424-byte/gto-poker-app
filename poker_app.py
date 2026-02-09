import streamlit as st
import random
import time

# --- 設定とスタイル ---
st.set_page_config(page_title="GTO Poker Trainer", layout="centered")

# カードのデザインをCSSで定義（白背景に赤/黒の文字）
st.markdown("""
<style>
    .card {
        display: inline-block;
        width: 60px;
        height: 90px;
        background-color: white;
        border-radius: 5px;
        border: 1px solid #ccc;
        text-align: center;
        vertical-align: middle;
        font-size: 24px;
        font-weight: bold;
        line-height: 90px;
        margin: 5px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
    }
    .suit-red { color: #d9534f; }
    .suit-black { color: #333; }
    .pot-box {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 20px;
    }
    .stButton>button {
        width: 100%;
        height: 50px;
        font-size: 18px;
    }
</style>
""", unsafe_allow_html=True)

# --- ロジック部分 ---
SUITS = ['♠', '♥', '♦', '♣']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']

class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit
    
    def render(self):
        color_class = "suit-red" if self.suit in ['♥', '♦'] else "suit-black"
        return f'<div class="card {color_class}">{self.rank}{self.suit}</div>'

def create_deck():
    return [Card(r, s) for s in SUITS for r in RANKS]

def get_gto_advice(hand, board, street):
    # 簡易GTOロジック
    hand_val = [c.rank for c in hand]
    is_pair = hand_val[0] == hand_val[1]
    
    # Preflop
    if street == "Preflop":
        if is_pair or hand_val[0] in ['A', 'K'] or hand_val[1] in ['A', 'K']:
            return "RAISE", "プレミアムハンドまたはハイカードです。参加して主導権を握りましょう。"
        else:
            return "FOLD", "期待値が低いため、フォールドが推奨されます。"
            
    # Postflop (簡易判定)
    board_ranks = [c.rank for c in board]
    hit = any(r in board_ranks for r in hand_val)
    
    if hit:
        return "BET", "ボードにヒットしています。バリューベットでポットを構築します。"
    return "CHECK", "ヒットしていません。ポットコントロールのためにチェックします。"

# --- アプリの状態管理 (Session State) ---
if 'game_active' not in st.session_state:
    st.session_state.game_active = False
    st.session_state.deck = []
    st.session_state.user_hand = []
    st.session_state.board = []
    st.session_state.pot = 0
    st.session_state.street = "Preflop"
    st.session_state.message = "ゲームを開始してください"
    st.session_state.feedback = ""

def start_new_hand():
    deck = create_deck()
    random.shuffle(deck)
    st.session_state.deck = deck
    st.session_state.user_hand = [deck.pop(), deck.pop()]
    st.session_state.board = []
    st.session_state.pot = 1.5 # SB+BB
    st.session_state.street = "Preflop"
    st.session_state.game_active = True
    st.session_state.feedback = ""
    st.session_state.message = "アクションを選択してください (BTN)"

def next_street():
    deck = st.session_state.deck
    current_street = st.session_state.street
    
    if current_street == "Preflop":
        st.session_state.street = "Flop"
        st.session_state.board = [deck.pop() for _ in range(3)]
    elif current_street == "Flop":
        st.session_state.street = "Turn"
        st.session_state.board.append(deck.pop())
    elif current_street == "Turn":
        st.session_state.street = "River"
        st.session_state.board.append(deck.pop())
    elif current_street == "River":
        st.session_state.message = "ハンド終了。ショーダウン！"
        st.session_state.game_active = False
        return

    st.session_state.message = f"{st.session_state.street} ラウンド。アクションを選択してください。"
    st.session_state.feedback = ""

def process_action(action):
    rec_action, reason = get_gto_advice(st.session_state.user_hand, st.session_state.board, st.session_state.street)
    
    is_correct = False
    if action == "FOLD" and rec_action == "FOLD": is_correct = True
    elif action == "CHECK" and rec_action == "CHECK": is_correct = True
    elif action in ["BET", "RAISE"] and rec_action in ["BET", "RAISE"]: is_correct = True
    
    if is_correct:
        st.session_state.feedback = f"✅ **正解!** (GTO: {rec_action})\n\n💡 {reason}"
        if action != "FOLD":
            if action in ["BET", "RAISE"]:
                st.session_state.pot += 5
            time.sleep(0.5)
            next_street()
        else:
            st.session_state.message = "フォールドしました。"
            st.session_state.game_active = False
    else:
        st.session_state.feedback = f"❌ **ミス!** 推奨: **{rec_action}**\n\n💡 {reason}"
        # ミスしてもゲームは続行（練習のため）
        if action != "FOLD":
            if action in ["BET", "RAISE"]:
                st.session_state.pot += 5
            next_street()
        else:
            st.session_state.game_active = False

# --- UI レイアウト ---

st.title("🃏 GTO Poker Trainer")
st.caption("AI Feedback & Street Progression")

# ゲーム開始ボタン
if not st.session_state.game_active:
    if st.button("ハンドを配る (Deal)", type="primary"):
        start_new_hand()
        st.rerun()

else:
    # 1. ボード表示エリア
    st.markdown("### Community Cards")
    board_html = "".join([c.render() for c in st.session_state.board]) if st.session_state.board else "<div style='color:gray; padding:20px;'>Wait for Flop...</div>"
    st.markdown(f"<div>{board_html}</div>", unsafe_allow_html=True)
    
    st.markdown("---")

    # 2. ポット情報
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown(f"""
        <div class="pot-box">
            <div style="font-size:12px; color:gray;">Current Pot</div>
            <div style="font-size:24px;">💰 {st.session_state.pot} BB</div>
            <div style="font-size:14px; color:blue;">{st.session_state.street}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # 解説・フィードバックエリア
        if st.session_state.feedback:
            if "正解" in st.session_state.feedback:
                st.success(st.session_state.feedback)
            else:
                st.error(st.session_state.feedback)
        else:
            st.info(st.session_state.message)

    # 3. プレイヤーハンド
    st.markdown("### Your Hand (BTN)")
    hand_html = "".join([c.render() for c in st.session_state.user_hand])
    st.markdown(f"<div>{hand_html}</div>", unsafe_allow_html=True)

    # 4. アクションボタン
    st.write("")
    col_a, col_b, col_c = st.columns(3)
    
    with col_a:
        if st.button("Check / Fold"):
            action = "CHECK" if st.session_state.pot <= 1.5 else "FOLD" # 簡易判定
            process_action(action)
            st.rerun()
            
    with col_b:
        if st.button("Call"):
            process_action("CALL") # 簡易的にはチェック扱いにするか要調整
            st.rerun()
            
    with col_c:
        if st.button("Bet / Raise"):
            process_action("RAISE")
            st.rerun()

# デバッグ用（本番では消す）
# st.write(st.session_state)
