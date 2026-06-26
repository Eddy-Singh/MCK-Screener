import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import datetime
import time

st.set_page_config(page_title="DMA Strategy Screener",
                   layout="wide", page_icon="📡")

st.title("📡 DMA Strategy Screener — Nifty 250")
st.markdown(
    "Screens Nifty 250 stocks for Mahesh Chander Kaushik's DMA setup: "
    "**Flag 1 → Dip → Flag 2 (Ready to Buy)**. "
    "Looks back 60 days for active setups and displays the complete event history."
)

# ── CONSTANTS ──────────────────────────────────────────────────────────────────
SETUP_EXPIRY_DAYS = 60      # Hard-coded as per requirement
# FIX #1: 260 calendar days (~185 trading days) was NOT enough to compute a
# 200-day SMA. We need at least 200 trading days of history, which requires
# ~300+ calendar days of fetching, matching app.py's approach of fetching
# 300 days before the analysis window starts.
LOOKBACK_DAYS = 400         # ~285 trading days — safely covers 200 SMA warmup
CURRENCY = "₹"

NIFTY_250_TICKERS = [
    "ABB.NS", "ACC.NS", "AUBANK.NS", "ADANIENSOL.NS", "ADANIENT.NS", "ADANIGREEN.NS", "ADANIPORTS.NS",
    "ADANIPOWER.NS", "ATGL.NS", "AWL.NS", "AJANTPHARM.NS", "ALKEM.NS", "AMBUJACEM.NS", "ANANDRATHI.NS",
    "ANGELONE.NS", "APOLLOHOSP.NS", "APOLLOTYRE.NS", "ASHOKLEY.NS", "ASIANPAINT.NS", "ASTRAL.NS",
    "AUROPHARMA.NS", "AXISBANK.NS", "BSE.NS", "BAJAJ-AUTO.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS",
    "BAJAJHLDNG.NS", "BALKRISIND.NS", "BALRAMCHIN.NS", "BANDHANBNK.NS", "BANKBARODA.NS", "BANKINDIA.NS",
    "MAHABANK.NS", "BATAINDIA.NS", "BEL.NS", "BHARATFORG.NS", "BHEL.NS", "BPCL.NS", "BHARTIARTL.NS",
    "BIOCON.NS", "BOSCHLTD.NS", "BRITANNIA.NS", "CGPOWER.NS", "CANFINHOME.NS", "CANBK.NS", "CAPLIPOINT.NS",
    "CASTROLIND.NS", "CENTRALBK.NS", "CHAMBLFERT.NS", "CHOLAFIN.NS", "CIPLA.NS",
    "CUB.NS", "CLEAN.NS", "COALINDIA.NS", "COCHINSHIP.NS", "COFORGE.NS", "COLPAL.NS", "CONCOR.NS",
    "COROMANDEL.NS", "CRAFTSMAN.NS", "CRISIL.NS", "CROMPTON.NS", "CUMMINSIND.NS", "CYIENT.NS",
    "DLF.NS", "DABUR.NS", "DALBHARAT.NS", "DEEPAKNTR.NS", "DELHIVERY.NS", "DIVISLAB.NS", "DIXON.NS",
    "LALPATHLAB.NS", "DRREDDY.NS", "EIDPARRY.NS", "EICHERMOT.NS", "ELGIEQUIP.NS", "EMAMILTD.NS",
    "ENDURANCE.NS", "ESCORTS.NS", "EXIDEIND.NS", "FEDERALBNK.NS", "FACT.NS", "FINEORG.NS",
    "FORTIS.NS", "GAIL.NS", "GMRINFRA.NS", "GLENMARK.NS", "GODREJCP.NS", "GODREJIND.NS", "GODREJPROP.NS",
    "GRASIM.NS", "GRINDWELL.NS", "GUJGASLTD.NS", "GSPL.NS", "HCLTECH.NS", "HDFCAMC.NS", "HDFCBANK.NS",
    "HDFCLIFE.NS", "HAVELLS.NS", "HEROMOTOCO.NS", "HINDALCO.NS", "HAL.NS", "HINDCOPPER.NS", "HINDPETRO.NS",
    "HINDUNILVR.NS", "HUDCO.NS", "ICICIBANK.NS", "ICICIGI.NS", "ICICIPRULI.NS",
    "ISEC.NS", "IDBI.NS", "IDFCFIRSTB.NS", "ITC.NS", "INDIAMART.NS", "INDIANB.NS", "IEX.NS", "INDHOTEL.NS",
    "IOC.NS", "IRCTC.NS", "IRFC.NS", "IGL.NS", "INDIGOPNTS.NS", "INDUSINDBK.NS", "NAUKRI.NS", "INFY.NS",
    "INOXWIND.NS", "INTELLECT.NS", "INDIGO.NS", "IPCALAB.NS", "JSWENERGY.NS", "JSWSTEEL.NS",
    "JINDALSTEL.NS", "JIOFIN.NS", "JUBLFOOD.NS", "KPRMILL.NS", "KALYANKJIL.NS", "KANSAINER.NS",
    "KARURVYSYA.NS", "KAYNES.NS", "KEC.NS", "KEI.NS", "KOTAKBANK.NS", "KPITTECH.NS", "KFINTECH.NS",
    "L&TFH.NS", "LTTS.NS", "LICHSGFIN.NS", "LT.NS", "LAURUSLABS.NS", "LICI.NS", "LINDEINDIA.NS",
    "LUPIN.NS", "MRF.NS", "MGL.NS", "M&MFIN.NS", "M&M.NS", "MANAPPURAM.NS", "MARICO.NS",
    "MARUTI.NS", "MASTEK.NS", "MAXHEALTH.NS", "MAZDOCK.NS", "METROPOLIS.NS",
    "MOTILALOFS.NS", "MPHASIS.NS", "MCX.NS", "MUTHOOTFIN.NS", "NATCOPHARM.NS", "NHPC.NS", "NLCINDIA.NS",
    "NMDC.NS", "NTPC.NS", "NATIONALUM.NS", "NAVINFLUOR.NS", "NESTLEIND.NS", "NIPPONNAM.NS", "OBEROIRLTY.NS",
    "ONGC.NS", "OIL.NS", "PAYTM.NS", "OFSS.NS", "POLICYBZR.NS", "PIIND.NS", "PNB.NS", "PVRINOX.NS",
    "PATANJALI.NS", "PERSISTENT.NS", "PETRONET.NS", "PIDILITIND.NS", "PEL.NS", "POLYCAB.NS", "POONAWALLA.NS",
    "PFC.NS", "POWERGRID.NS", "PRESTIGE.NS", "PNBHOUSING.NS", "RADICO.NS", "RVNL.NS", "RAYMOND.NS",
    "RECLTD.NS", "RELIANCE.NS", "RRKABEL.NS", "SBICARD.NS", "SBILIFE.NS", "SJVN.NS", "SKFINDIA.NS",
    "SRF.NS", "SCHAEFFLER.NS", "SHREECEM.NS", "SHRIRAMFIN.NS", "SIEMENS.NS",
    "SONACOMS.NS", "SBIN.NS", "SAIL.NS", "STARHEALTH.NS", "SUNPHARMA.NS", "SUNTV.NS", "SUPREMEIND.NS",
    "SUZLON.NS", "SYNGENE.NS", "TVSMOTOR.NS", "TATACHEM.NS", "TATACOMM.NS", "TATACONSUM.NS",
    "TATAELXSI.NS", "TATAINVEST.NS", "TATAMOTORS.NS", "TATAPOWER.NS", "TATASTEEL.NS", "TCS.NS", "TECHM.NS",
    "THERMAX.NS", "TITAN.NS", "TORNTPHARM.NS", "TORNTPOWER.NS", "TRENT.NS", "TRIDENT.NS",
    "TIINDIA.NS", "UCOBANK.NS", "UNOMINDA.NS", "ULTRACEMCO.NS", "UNIONBANK.NS", "UPL.NS",
    "VGUARD.NS", "VBL.NS", "VEDL.NS", "VOLTAS.NS", "WELSPUNLIV.NS", "WIPRO.NS",
    "YESBANK.NS", "ZEEL.NS", "ZENSARTECH.NS", "ZOMATO.NS", "ZYDUSLIFE.NS", "360ONE.NS"
]

# ── SIDEBAR ────────────────────────────────────────────────────────────────────
st.sidebar.header("⚙️ Screener Parameters")

upper_buffer_pct = st.sidebar.slider(
    "Upper Buffer over 200 SMA (%)",
    min_value=1.0, max_value=30.0, value=10.0, step=1.0
) / 100

drop_condition_pct = st.sidebar.slider(
    "Drop Below Flag 1 to Trigger Dip (%)",
    min_value=1.0, max_value=10.0, value=3.0, step=0.1
) / 100

st.sidebar.markdown("---")
as_of_date = st.sidebar.date_input(
    "📅 Screen As-Of Date",
    value=datetime.date.today(),
    max_value=datetime.date.today(),
    help="Screen the universe as if today were this date. Use any past date to replay historical setups."
)
st.sidebar.markdown("---")
st.sidebar.markdown(
    f"**Setup Expiry Window:** `{SETUP_EXPIRY_DAYS} days` *(fixed)*")
st.sidebar.markdown(f"**SMA Lookback:** `{LOOKBACK_DAYS} calendar days`")
st.sidebar.markdown("---")

with st.sidebar.expander(f"📋 Universe ({len(NIFTY_250_TICKERS)} stocks)", expanded=False):
    selected_tickers = st.multiselect(
        "Remove / add tickers:",
        options=NIFTY_250_TICKERS,
        default=NIFTY_250_TICKERS
    )

# ── HELPERS ────────────────────────────────────────────────────────────────────


def safe_float(val):
    """Safely extract a scalar float from a value that may be a pd.Series."""
    if isinstance(val, pd.Series):
        return float(val.iloc[0])
    return float(val)


def is_bull_aligned(row, upper_buf):
    """
    Mirrors app.py's Valid_Alignment column exactly:
      Close > SMA50 > SMA100 > SMA200  AND  Close < SMA200 * (1 + upper_buf)
    """
    try:
        close = safe_float(row['Close'])
        sma50 = safe_float(row['SMA_50'])
        sma100 = safe_float(row['SMA_100'])
        sma200 = safe_float(row['SMA_200'])
        return (
            close > sma50 and
            sma50 > sma100 and
            sma100 > sma200 and
            close < sma200 * (1 + upper_buf)
        )
    except Exception:
        return False


# ── SCREENING LOGIC ─────────────────────────────────────────────────────────────

def screen_ticker(ticker, upper_buf, drop_pct, as_of_date):
    """
    Runs the same 3-state machine as app.py's backtest engine and returns:
      1. A dict describing the stock's current active setup stage (or None)
      2. A list of historical events triggered within the 60-day reporting window
    """
    end_date = as_of_date
    # FIX #1 applied: fetch 400 calendar days back so SMA-200 is fully warmed up
    start_date = end_date - datetime.timedelta(days=LOOKBACK_DAYS)

    try:
        df = yf.download(ticker, start=start_date,
                         end=end_date, progress=False)
        if df.empty or len(df) < 205:   # must have at least 205 rows for SMA-200
            return None, []
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.index = df.index.tz_localize(None)
    except Exception:
        return None, []

    df['SMA_50'] = df['Close'].rolling(50).mean()
    df['SMA_100'] = df['Close'].rolling(100).mean()
    df['SMA_200'] = df['Close'].rolling(200).mean()
    df = df.dropna()

    if df.empty:
        return None, []

    today = pd.Timestamp(end_date)
    window_start = today - pd.Timedelta(days=SETUP_EXPIRY_DAYS)

    # ── State machine variables (mirrors app.py stock_states) ──────────────
    state = 0
    flag1_date = None
    flag1_price = None   # FIX #2: locked at first-entry price, NEVER updated
    dip_date = None
    dip_price = None
    flag2_date = None
    flag2_price = None
    state_date = None   # mirrors app.py's state_date for unified expiry tracking

    events_log = []
    clean_ticker = ticker.replace('.NS', '')

    dates = df.index.sort_values()

    for date in dates:
        row = df.loc[date]
        price = safe_float(row['Close'])
        aligned = is_bull_aligned(row, upper_buf)
        in_reporting_window = (date >= window_start)

        # ── Expiry check (matches app.py: days_waiting > max_setup_days) ──
        # FIX #3: use a single state_date per stage, reset when stage changes,
        # consistent with how app.py tracks it for states 1 and 2.
        if state in [1, 2] and state_date is not None:
            days_waiting = (date - state_date).days
            if days_waiting > SETUP_EXPIRY_DAYS:
                state = 0
                flag1_date = flag1_price = None
                dip_date = dip_price = None
                flag2_date = flag2_price = state_date = None
                continue

        # ── State transitions ───────────────────────────────────────────────

        if state == 0:
            if aligned:
                state = 1
                flag1_date = date
                flag1_price = price   # FIX #2: locked here, never raised again
                state_date = date
                if in_reporting_window:
                    events_log.append({
                        'Ticker': clean_ticker,
                        'Date':   date.date(),
                        'Event':  '🏁 Flag 1 — Breakout',
                        'Price':  round(price, 2)
                    })

        elif state == 1:
            # FIX #2: removed `flag1_price = max(flag1_price, price)`.
            # app.py never updates the flag price after the initial entry.
            # Raising it continuously makes the dip threshold a moving target
            # that gets progressively harder to trigger.
            if price <= flag1_price * (1 - drop_pct):
                state = 2
                dip_date = date
                dip_price = price
                state_date = date   # reset expiry clock for stage 2
                if in_reporting_window:
                    events_log.append({
                        'Ticker': clean_ticker,
                        'Date':   date.date(),
                        'Event':  '📉 Dip Pattern Triggered',
                        'Price':  round(price, 2)
                    })

        elif state == 2:
            if aligned:
                state = 3
                flag2_date = date
                flag2_price = price
                state_date = None   # no expiry once a buy signal fires
                if in_reporting_window:
                    events_log.append({
                        'Ticker': clean_ticker,
                        'Date':   date.date(),
                        'Event':  '🚀 Flag 2 — READY TO BUY',
                        'Price':  round(price, 2)
                    })

        elif state == 3:
            # FIX #4: In app.py the trade is entered immediately on Flag 2 and
            # the stock is no longer in 'watch' state — the screener equivalent
            # is that a Flag 2 signal is final and does NOT reset if the price
            # dips again slightly.  The original screener incorrectly reset to
            # state 0 whenever alignment was lost, causing valid buy signals to
            # silently disappear.
            # We keep state 3 until the trade is theoretically closed (i.e. we
            # don't model exits in the screener), so we do nothing here and let
            # the signal remain displayed.
            pass

    # ── Determine current active setup to surface in the UI ────────────────
    # FIX #5: Removed the `flag1_date >= window_start` gate.  A setup whose
    # Flag 1 fired more than 60 days ago can still have a *live* Dip or Flag 2
    # event within the window.  We check the stage-relevant date instead.
    active_setup = None
    if state != 0:
        # Choose the most-recent stage date to decide if it's "fresh" enough
        relevant_date = flag2_date if flag2_date is not None else (
            dip_date if dip_date is not None else flag1_date)

        if relevant_date is not None and relevant_date >= window_start:
            # Use last available row on or before as_of_date as "current"
            latest_row = df[df.index <= pd.Timestamp(as_of_date)].iloc[-1]
            latest_price = safe_float(latest_row['Close'])
            sma50 = safe_float(latest_row['SMA_50'])
            sma100 = safe_float(latest_row['SMA_100'])
            sma200 = safe_float(latest_row['SMA_200'])
            currently_aligned = is_bull_aligned(latest_row, upper_buf)

            pct_from_flag1 = ((latest_price - flag1_price) / flag1_price) * 100
            dip_pct_from_flag1 = (
                round(((dip_price - flag1_price) / flag1_price) * 100, 2)
                if dip_price is not None else '—'
            )
            flag2_pct_from_flag1 = (
                round(((flag2_price - flag1_price) / flag1_price) * 100, 2)
                if flag2_price is not None else '—'
            )

            active_setup = {
                'Ticker':            clean_ticker,
                'Stage':             state,
                'Flag 1 Date':       flag1_date.date(),
                'Flag 1 Price':      round(flag1_price, 2),
                'Dip Date':          dip_date.date() if dip_date is not None else '—',
                'Dip Price':         round(dip_price, 2) if dip_price is not None else '—',
                'Dip % from Flag 1': dip_pct_from_flag1,
                'Flag 2 Date':       flag2_date.date() if flag2_date is not None else '—',
                'Flag 2 Price':      round(flag2_price, 2) if flag2_price is not None else '—',
                'Flag 2 % from Flag 1': flag2_pct_from_flag1,
                'Latest Price':      round(latest_price, 2),
                'SMA 50':            round(sma50,  2),
                'SMA 100':           round(sma100, 2),
                'SMA 200':           round(sma200, 2),
                '% from Flag 1':     round(pct_from_flag1, 2),
                'Bull Aligned Now':  '✅' if currently_aligned else '❌',
            }

    return active_setup, events_log


# ── RUN BUTTON ─────────────────────────────────────────────────────────────────
if st.button("🔍 Run Screener", type="primary"):

    tickers_to_scan = selected_tickers
    total = len(tickers_to_scan)

    is_today = (as_of_date == datetime.date.today())
    date_label = "today" if is_today else f"**{as_of_date.strftime('%d %b %Y')}**"
    st.info(
        f"Scanning **{total} stocks** as of {date_label} — this takes ~{total // 5}–{total // 3} seconds. Please wait…")

    progress_bar = st.progress(0)
    status_text = st.empty()

    results = []
    all_historical_events = []

    for i, ticker in enumerate(tickers_to_scan):
        status_text.text(
            f"Scanning {ticker.replace('.NS', '')} ({i+1}/{total})…")

        res, history = screen_ticker(
            ticker, upper_buffer_pct, drop_condition_pct, as_of_date)

        if res is not None:
            results.append(res)
        if history:
            all_historical_events.extend(history)

        progress_bar.progress((i + 1) / total)
        time.sleep(0.05)

    progress_bar.empty()
    status_text.empty()

    # ── SPLIT BY STAGE ──────────────────────────────────────────────────────────
    stage3 = [r for r in results if r['Stage'] == 3]
    stage2 = [r for r in results if r['Stage'] == 2]
    stage1 = [r for r in results if r['Stage'] == 1]

    st.success(
        f"Scan complete — "
        f"**{len(stage3)} Ready to Buy** | "
        f"**{len(stage2)} Dipped** | "
        f"**{len(stage1)} Flag 1 Watch** | "
        f"out of {total} stocks scanned"
    )

    DISPLAY_COLS = [
        'Ticker', 'Flag 1 Date', 'Flag 1 Price',
        'Dip Date', 'Dip Price', 'Dip % from Flag 1',
        'Flag 2 Date', 'Flag 2 Price', 'Flag 2 % from Flag 1', 'Latest Price',
        'SMA 50', 'SMA 100', 'SMA 200',
        '% from Flag 1', 'Bull Aligned Now'
    ]

    # ───── STAGE 3: READY TO BUY ─────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🚀 Stage 3 — Flag 2 Ready to Buy")
    st.caption(
        "These stocks have completed the full setup: bull-aligned (Flag 1) → dropped → re-aligned (Flag 2).")
    if stage3:
        df3 = pd.DataFrame(stage3)[DISPLAY_COLS]
        st.dataframe(df3, use_container_width=True)
    else:
        st.info("No stocks are at Stage 3 right now.")

    # ───── STAGE 2: DIPPED ───────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("📉 Stage 2 — Dipped, Waiting for Re-alignment")
    st.caption(
        "These stocks passed Flag 1 and have since dipped the required %. Watching for bull re-alignment.")
    if stage2:
        df2 = pd.DataFrame(stage2)[DISPLAY_COLS]
        st.dataframe(df2, use_container_width=True)
    else:
        st.info("No stocks are at Stage 2 right now.")

    # ───── STAGE 1: FLAG 1 ───────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🏁 Stage 1 — Flag 1 Watch (Bull Aligned, No Dip Yet)")
    st.caption(
        "These stocks are currently in bull alignment. Waiting for them to pull back.")
    if stage1:
        df1 = pd.DataFrame(stage1)[DISPLAY_COLS]
        st.dataframe(df1, use_container_width=True)
    else:
        st.info("No stocks are at Stage 1 right now.")

    # ───── SUMMARY MINI-CHART ────────────────────────────────────────────────
    st.markdown("---")
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("📊 Setup Pipeline Summary")
        summary_df = pd.DataFrame({
            "Stage": ["🏁 Flag 1 Watch", "📉 Dipped", "🚀 Ready to Buy"],
            "Count": [len(stage1),       len(stage2),  len(stage3)],
        }).set_index("Stage")
        st.bar_chart(summary_df)

    # ───── HISTORICAL EVENT LOG ──────────────────────────────────────────────
    st.markdown("---")
    st.subheader(
        f"📜 60-Day Historical Event Log (ending {as_of_date.strftime('%d %b %Y')})")
    st.caption(
        "A chronological record of every Flag 1, Dip, and Flag 2 event "
        f"triggered across the scanned universe within the 60-day window ending {as_of_date.strftime('%d %b %Y')}.")

    if all_historical_events:
        history_df = pd.DataFrame(all_historical_events)
        history_df = history_df.sort_values(
            by="Date", ascending=False).reset_index(drop=True)

        st.dataframe(
            history_df,
            use_container_width=True,
            column_config={
                "Ticker": st.column_config.TextColumn("Ticker"),
                "Date":   st.column_config.TextColumn("Event Date"),
                "Event":  st.column_config.TextColumn("Pattern Trigger"),
                "Price":  st.column_config.NumberColumn(
                    f"Price ({CURRENCY})", format="%.2f"),
            }
        )
    else:
        st.info("No historical milestones triggered in the last 60 days.")

else:
    # ── Landing state ──────────────────────────────────────────────────────────
    st.markdown("""
    ### How the screener works

    | Stage | What it means |
    |-------|---------------|
    | 🏁 **Flag 1** | Stock entered full bull alignment: `Price > SMA50 > SMA100 > SMA200` and price is within the upper buffer above the 200 SMA |
    | 📉 **Dipped** | After Flag 1, price fell by at least the configured **drop %** |
    | 🚀 **Flag 2 — Ready to Buy** | After the dip, the stock has re-established full bull alignment — this is the **buy signal** |

    **Setup Expiry is fixed at 60 days.** If no dip or recovery happens within 60 days of the last stage trigger, the setup resets.

    Configure the **drop %** and **SMA upper buffer** in the sidebar, then press **Run Screener**.
    """)
# repo visibility changed to public
