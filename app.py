import streamlit as st
import json
from openai import OpenAI

# App UI Configuration
st.set_page_config(page_title="HiBid Arbitrage AI", page_icon="📈", layout="centered")

st.title("🪙 HiBid Arbitrage AI Analyzer")
st.markdown("Evaluate **Gold, Sterling Silver, and Fine Art** listings with a strict **30% minimum ROI** gatekeeper.")

# Sidebar for API Key input
st.sidebar.header("Configuration")
api_key_input = st.sidebar.text_input("OpenAI API Key", type="password")

# Market Baselines
CURRENT_SPOT_PRICES = {
    "gold_per_gram": 134.00,   # 2026 Gold spot/g
    "silver_per_gram": 1.93    # 2026 Silver spot/g
}
MIN_TARGET_ROI = 30.0

# Main Input Form
with st.form("arbitrage_form"):
    st.subheader("Enter Lot Details")
    title = st.text_input("Lot Title", "14K Yellow Gold Heavy Cuban Chain - 25g")
    description = st.text_area("Lot Description", "Solid 14k yellow gold chain, hallmarked 14k. Total weight 25 grams. Excellent condition.")
    current_bid = st.number_input("Current Bid ($)", min_value=0.0, value=2100.0, step=10.0)
    
    submitted = st.form_submit_button("Run AI Arbitrage Analysis")

if submitted:
    if not api_key_input:
        st.error("Please enter your OpenAI API Key in the sidebar.")
    else:
        client = OpenAI(api_key=api_key_input)
        
        with st.spinner("Analyzing market comps and calculating fees..."):
            prompt = f"""
            You are an expert auction arbitrage engine for Gold, Sterling Silver, and Fine Art.
            Analyze the following auction lot record:

            --- LOT RECORD ---
            Title: {title}
            Description: {description}
            Current Bid: ${current_bid}
            Estimated Buyer's Premium: 15.0%
            Estimated Sales Tax: 7.0%
            Estimated Shipping/Pickup Cost: $30.00

            --- MARKET BENCHMARKS ---
            Gold Spot: ${CURRENT_SPOT_PRICES['gold_per_gram']}/g | Silver Spot: ${CURRENT_SPOT_PRICES['silver_per_gram']}/g

            --- INSTRUCTIONS ---
            1. **Asset Categorization**: Classify into 'Gold/Bullion', 'Sterling Silver', or 'Fine Art'.
            2. **Financial Math**:
               - Total Acquisition Cost = Current Bid + (Bid * 15% Premium) + (Bid * 7% Tax) + $30 Shipping.
               - Net Resale Payout = Estimated Resale Midpoint - (13% Platform Selling Fees).
               - Net Profit = Net Resale Payout - Total Acquisition Cost.
               - ROI Percentage = (Net Profit / Total Acquisition Cost) * 100.
            3. **Recommendation**: 'STRONG BUY' ONLY if ROI Percentage >= 30.0%. Otherwise, recommend 'PASS'.

            Return ONLY a valid JSON object matching this schema:
            {{
                "category": "",
                "item_breakdown": "Brief note on purity, weight, or artist verification",
                "total_acquisition_cost": 0.00,
                "estimated_resale_mid": 0.00,
                "estimated_net_profit": 0.00,
                "roi_percentage": 0.0,
                "recommendation": "STRONG BUY | PASS",
                "risk_factors": ["risk 1", "risk 2"]
            }}
            """

            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                )
                
                result = json.loads(response.choices.message.content)
                
                # Programmatic Guardrail: Force PASS if ROI is under 30%
                ai_roi = float(str(result.get("roi_percentage", "0")).replace("%", ""))
                if ai_roi < MIN_TARGET_ROI:
                    result["recommendation"] = "PASS (Filtered: Below 30% Minimum ROI)"

                # Display Results in App Dashboard
                st.markdown("---")
                st.subheader("Evaluation Results")
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Acquisition Cost", f"${result.get('total_acquisition_cost', 0):,.2f}")
                col2.metric("Est. Net Profit", f"${result.get('estimated_net_profit', 0):,.2f}")
                col3.metric("ROI %", f"{result.get('roi_percentage', 0)}%")
                
                if "STRONG BUY" in result.get('recommendation', ''):
                    st.success(f"**Recommendation:** {result.get('recommendation')}")
                else:
                    st.error(f"**Recommendation:** {result.get('recommendation')}")
                    
                st.write("**Category:**", result.get('category'))
                st.write("**Item Breakdown:**", result.get('item_breakdown'))
                
                st.write("**Risk Factors:**")
                for risk in result.get('risk_factors', []):
                    st.markdown(f"- {risk}")
                    
                with st.expander("View Raw JSON Data"):
                    st.json(result)

            except Exception as e:
                st.error(f"An error occurred: {e}")
