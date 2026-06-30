import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Page Configuration with Native Dark Palette Elements
st.set_page_config(
    page_title="ASOS Fashion Brand Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium Custom Styling Customizations via CSS Inject
st.markdown("""
    <style>
        /* Base Container Custom Padding & UI cleanup */
        .block-container { padding-top: 2rem; padding-bottom: 2rem; }
        div[data-testid="stMetricValue"] { font-size: 2rem !important; font-weight: 700; color: #00F2FE; }
        div[data-testid="stMetricLabel"] { font-size: 0.95rem !important; text-transform: uppercase; letter-spacing: 0.5px; }
    </style>
""", unsafe_allow_html=True)

# 2. Main Title Header Array
st.title("📊 ASOS Fashion Brand Portfolio Analysis")
st.caption("Inventory Optimization, Out-of-Stock Metrics & Revenue Leakage Dashboard")
st.markdown("---")

# 3. Cached Data Ingestion & String Matching Transformations
@st.cache_data
def load_data():
    try:
        df = pd.read_csv(
            "products_asos.csv",
            engine="python",
            on_bad_lines="skip"
        )
    except FileNotFoundError:
        # Fallback dummy dataframe configuration for seamless Streamlit Cloud deployments testing
        st.info("💡 Tip: Upload 'products_asos.csv' to your repository root for real production execution.")
        dummy_data = {
            "description": [f"Dress by New Look size {i}" for i in range(50)] + 
                           [f"Shirt by River Island denim" for i in range(50)] +
                           [f"Jacket by TopshopWelcome chic" for i in range(50)],
            "price": [25.0 + i for i in range(50)] + [45.0 + (i*1.5) for i in range(50)] + [60.0 + (i*2) for i in range(50)],
            "in_stock": [i % 5 != 0 for i in range(50)] + [i % 4 != 0 for i in range(50)] + [i % 3 != 0 for i in range(50)]
        }
        df = pd.DataFrame(dummy_data)

    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df = df.dropna(subset=["price"])
    df["description"] = df["description"].astype(str)

    def get_brand(text):
        if "by " in text:
            try:
                return text.split("by ")[1].split(" ")[0]
            except:
                return "Unknown"
        return "Unknown"

    df["brand_raw"] = df["description"].apply(get_brand)

    brand_map = {
        "New": "New Look",
        "River": "River Island",
        "Miss": "Miss Selfridge",
        "TopshopWelcome": "Topshop"
    }

    df["Brand"] = df["brand_raw"].map(brand_map).fillna(df["brand_raw"])
    
    # Filter out long tail data noise
    valid = df["Brand"].value_counts()
    valid = valid[valid > 5].index
    df = df[df["Brand"].isin(valid)].copy()

    return df

df = load_data()

# 4. Sidebar Filter Suite & Active Exporters
st.sidebar.header("🔍 Filter Suite")

brands = sorted(df["Brand"].unique())
selected = st.sidebar.multiselect(
    "Select Brands for Portfolio Review",
    brands,
    default=brands[:6] if len(brands) > 6 else brands
)

# Apply global slice filter
filtered = df[df["Brand"].isin(selected)].copy()

# Advanced Exporters Sub-Module inside Sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("📥 Actionable Pipelines")

@st.cache_data
def convert_df_to_csv(dataframe):
    return dataframe.to_csv(index=False).encode('utf-8')

csv_data = convert_df_to_csv(filtered)

st.sidebar.download_button(
    label="Download Filtered Data (.CSV)",
    data=csv_data,
    file_name="filtered_asos_inventory_data.csv",
    mime="text/csv",
    width="stretch"
)

# 5. Inventory Dynamic Variable Discovery Layer
possible_stock_cols = ["in_stock", "InStock", "In_Stock", "stock"]
actual_stock_col = None

for col in possible_stock_cols:
    if col in filtered.columns:
        actual_stock_col = col
        break

if actual_stock_col:
    filtered["Is_Stockout"] = filtered[actual_stock_col].isin([False, "False", 0, "0"])
else:
    filtered["Is_Stockout"] = False

# Portfolio Matrix Aggregates Calculation Loop
brand_summary = (
    filtered.groupby("Brand")
    .agg(
        Avg_Price=("price", "mean"),
        Total_Products=("Brand", "count"),
        Stockout_Count=("Is_Stockout", "sum")
    )
    .reset_index()
)

brand_summary["Stockout_Rate"] = (brand_summary["Stockout_Count"] / brand_summary["Total_Products"]) * 100
brand_summary["Estimated_Lost_Revenue"] = brand_summary["Stockout_Count"] * brand_summary["Avg_Price"]

# 6. Executive KPI Layout Block
st.subheader("📊 Operational Core KPIs")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    st.metric(label="Active Product Count", value=f"{len(filtered):,}")
with kpi2:
    st.metric(label="Monitored Brands", value=f"{filtered['Brand'].nunique()}")
with kpi3:
    st.metric(label="Portfolio Avg Price", value=f"£{filtered['price'].mean():.2f}")
with kpi4:
    st.metric(label="Aggregate Revenue Leakage", value=f"£{brand_summary['Estimated_Lost_Revenue'].sum():,.2f}")

st.markdown("---")

# 7. Dual Matrix Column Visualizations
st.subheader("📈 Supply Chain Fault Analysis")
chart_col1, chart_col2 = st.columns(2)

# Chart Theme Defaults
dark_layout_config = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font_color="#E0E0E0",
    xaxis=dict(showgrid=False, title_font=dict(size=12)),
    yaxis=dict(showgrid=True, gridcolor="#2D2D2D", title_font=dict(size=12)),
    margin=dict(l=40, r=40, t=50, b=40)
)

with chart_col1:
    fig_rev = px.bar(
        brand_summary.sort_values("Estimated_Lost_Revenue", ascending=False).head(15),
        x="Brand",
        y="Estimated_Lost_Revenue",
        color="Estimated_Lost_Revenue",
        color_continuous_scale="Viridis",
        title="💰 Revenue Loss Contribution by Brand"
    )
    fig_rev.update_layout(dark_layout_config)
    st.plotly_chart(fig_rev, width="stretch")

with chart_col2:
    fig_stockout = px.bar(
        brand_summary.sort_values("Stockout_Rate", ascending=False).head(15),
        x="Brand",
        y="Stockout_Rate",
        color="Stockout_Rate",
        color_continuous_scale="Magma",
        title="📦 Out-of-Stock (Stockout Rate %) Profiles"
    )
    fig_stockout.update_layout(dark_layout_config)
    st.plotly_chart(fig_stockout, width="stretch")

st.markdown("---")

# 8. Interactive Scatter Plot Block
st.subheader("🎯 Portfolio Position Strategy Mapping")
fig_scatter = px.scatter(
    brand_summary,
    x="Avg_Price",
    y="Stockout_Rate",
    size="Estimated_Lost_Revenue",
    color="Estimated_Lost_Revenue",
    color_continuous_scale="Plasma",
    hover_name="Brand",
    title="Price Architecture Point vs. Stockout Fragility Matrix",
    labels={"Avg_Price": "Average Price (£)", "Stockout_Rate": "Stockout Rate (%)"}
)
fig_scatter.update_layout(dark_layout_config)
st.plotly_chart(fig_scatter, width="stretch")

st.markdown("---")

# 9. Top 10 High-Risk Vulnerability Data Table Segment
st.subheader("🥇 Top High-Risk Pipeline Vulnerabilities")

high_risk_table = (
    brand_summary.sort_values(by="Estimated_Lost_Revenue", ascending=False)
    .head(10)[["Brand", "Total_Products", "Stockout_Count", "Stockout_Rate", "Estimated_Lost_Revenue"]]
    .reset_index(drop=True)
)

# Format for clean display presentation
high_risk_table["Stockout_Rate"] = high_risk_table["Stockout_Rate"].map("{:,.1f}%".format)
high_risk_table["Estimated_Lost_Revenue"] = high_risk_table["Estimated_Lost_Revenue"].map("£{:,.2f}".format)

st.dataframe(
    high_risk_table,
    column_config={
        "Brand": "Fashion Brand Line",
        "Total_Products": "Total Sku Count",
        "Stockout_Count": "Stocked Out Units",
        "Stockout_Rate": "Vulnerability Rate",
        "Estimated_Lost_Revenue": "Revenue At Risk"
    },
    width="stretch"
)

st.markdown("---")

# 10. Analytical Insights & Strategic Recommendations Action Block
st.subheader("📋 Executive Strategic Recommendations")

if not brand_summary.empty:
    highest_loss_row = brand_summary.sort_values("Estimated_Lost_Revenue", ascending=False).iloc[0]
    highest_stock_row = brand_summary.sort_values("Stockout_Rate", ascending=False).iloc[0]

    st.info(f"""
    ### 🎯 Critical Vulnerability Identifiers
    * **Primary Financial Threat:** **{highest_loss_row['Brand']}** dictates the highest absolute financial revenue leakage due to inventory failure (**£{highest_loss_row['Estimated_Lost_Revenue']:,.2f}** at risk).
    * **Supply Chain Disruption Target:** **{highest_stock_row['Brand']}** exhibits the lowest fulfillment health with an extreme out-of-stock rate of **{highest_stock_row['Stockout_Rate']:.1f}%**.
    
    ### 🛠 Strategic Action Directives
    1. **Dynamic Reorder Velocity Adjustment:** Immediately deploy safety stock buffers for premium tier lines where average unit prices cross **£{brand_summary['Avg_Price'].mean():.2f}**.
    2. **Fulfillment Logistics Audits:** Initiate supplier performance assessments for brand manufacturers matching high stockout quadrants (top right corner of the Scatter Plot matrix).
    3. **Automated Procurement Execution:** Use the structured data files exported via the application workspace sidebar downstream inside automated replenishment schedules to rebalance safety margins.
    """)
else:
    st.warning("Please adjust filter selections in the sidebar menu panel options to analyze current data allocations.")