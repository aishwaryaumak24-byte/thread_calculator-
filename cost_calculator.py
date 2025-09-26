import streamlit as st
import math
import pandas as pd
from io import BytesIO

# Set a slightly more engaging page config
st.set_page_config(
    page_title="Machining Cost Calculator", 
    layout="wide",
    initial_sidebar_state="expanded" # Ensure sidebar is open
)

st.title("💰 Precision Machining Cost Estimator")

# --- Default Values for Machining Data (Used in Sidebar) ---
DEFAULT_CUTTING_SPEED = 50.0
DEFAULT_FEED_RATE = 0.35
DEFAULT_MHR = 1000
DEFAULT_CHAMFER_TIME = 2.0

# Initialize calculation state
if 'run_calculation' not in st.session_state:
    st.session_state.run_calculation = False

# --- Sidebar Inputs (Machining Data) ---
st.sidebar.header("⚙️ Machining Parameters")

# Slider: Final Diameter (Int values used, so no change needed)
D_final = st.sidebar.slider("Final Diameter ($D_{final}$, mm)", 5, 200, 36)

# CORRECTED: Changed 5 and 150 to 5.0 and 150.0 to match the float format ("%.1f")
cutting_speed = st.sidebar.slider(
    "Cutting Speed ($V_c$, m/min)", 5.0, 150.0, DEFAULT_CUTTING_SPEED, format="%.1f"
)

# CORRECTED: Changed 0.05 and 1.0 to 0.05 and 1.0 (already float, but ensuring consistency)
feed_rate = st.sidebar.slider(
    "Feed Rate ($f$, mm/rev)", 0.05, 1.0, DEFAULT_FEED_RATE, format="%.2f"
)

# Slider: MHR (Int values used, so no change needed)
MHR = st.sidebar.slider("Machine Hour Rate (MHR, Rs/hr)", 100, 2000, DEFAULT_MHR)

# CORRECTED: Changed 0.5 and 30.0 to 0.5 and 30.0 (already float, but ensuring consistency)
chamfer_time = st.sidebar.slider(
    "Chamfer/Load Time ($T_{aux}$, min)", 0.5, 30.0, DEFAULT_CHAMFER_TIME, format="%.1f"
)

# --- Main Area Layout ---
col_raw, col_results = st.columns([1.5, 2]) 

# --- Raw Material Data (Left Column) ---
with col_raw:
    st.header("🧱 Raw Material Data")
    
    # Sliders: D_raw, L_raw, Cost/kg (Int values used, so no change needed)
    D_raw = st.slider("Raw Diameter ($D_{raw}$, mm)", 10, 200, 38)
    L_raw = st.slider("Raw Length ($L_{raw}$, mm)", 50, 1000, 257)
    
    # Slider: Density (Float values used, so no change needed)
    density = st.slider("Density ($\rho$, g/cm³)", 1.0, 20.0, 7.85)
    cost_per_kg = st.slider("Cost per kg (Rs)", 10, 200, 55)
    
    st.markdown("---")
    
    # Button logic to trigger calculation
    if st.button("Calculate Cost", type="primary", use_container_width=True):
        st.session_state.run_calculation = True
    
# --- Calculations and Results Logic ---
if st.session_state.run_calculation:
    
    # --- Material Calculations ---
    volume_mm3 = math.pi * ((D_raw / 2) ** 2) * L_raw
    volume_cm3 = volume_mm3 / 1000
    weight_kg = (volume_cm3 * density) / 1000
    material_cost = weight_kg * cost_per_kg

    # --- Machining Calculations ---
    if D_final > 0:
        spindle_speed = (1000 * cutting_speed) / (math.pi * D_final)
    else:
        # Display error in the results column
        with col_results:
            st.error("Final Diameter ($D_{final}$) must be greater than 0.")
        # Stop further calculation
        st.session_state.run_calculation = False 
        spindle_speed = 0
        machining_cost = 0.0
        total_cost = material_cost # Only material cost applies if machining fails
    
    if st.session_state.run_calculation:
        if spindle_speed > 0 and feed_rate > 0:
            machining_time = L_raw / (feed_rate * spindle_speed)  # min
        else:
            machining_time = 0.0
    
        total_time_min = machining_time + chamfer_time
        total_time_hr = total_time_min / 60
        machining_cost = total_time_hr * MHR
    
        # --- Total Cost ---
        total_cost = material_cost + machining_cost

        # --- Display Results (Right Column) ---
        with col_results:
            st.header("📈 Cost Analysis Results")
            
            # Use st.metric for a dynamic, attractive summary
            cost_col1, cost_col2, cost_col3 = st.columns(3)
            
            with cost_col1:
                st.metric(
                    label="Total Material Cost", 
                    value=f"Rs. {material_cost:.2f}",
                    delta=f"{weight_kg:.3f} kg"
                )
            with cost_col2:
                st.metric(
                    label="Total Machining Cost", 
                    value=f"Rs. {machining_cost:.2f}",
                    delta=f"{total_time_min:.2f} min"
                )
            with cost_col3:
                st.metric(
                    label="GRAND TOTAL COST", 
                    value=f"Rs. {total_cost:.2f}",
                    delta_color="off"
                )
    
            st.markdown("---")
            
            # Display key intermediate metrics
            st.markdown("##### Performance Metrics")
            time_col1, time_col2 = st.columns(2)
            
            time_col1.info(f"**Calculated Spindle Speed (N):** {spindle_speed:.0f} RPM")
            time_col2.info(f"**Total Manufacturing Time:** {total_time_min:.2f} minutes")
    
        # --- Save DataFrame and Export Data (Below the main columns) ---
        st.markdown("## 📥 Data Export")
    
        data = {
            "D_raw (mm)": [D_raw],
            "L_raw (mm)": [L_raw],
            "Density (g/cm³)": [density],
            "Cost/kg (Rs)": [cost_per_kg],
            "D_final (mm)": [D_final],
            "Cutting Speed (m/min)": [cutting_speed],
            "Feed Rate (mm/rev)": [feed_rate],
            "MHR (Rs/hr)": [MHR],
            "Chamfer Time (min)": [chamfer_time],
            "Material Cost (Rs)": [material_cost],
            "Machining Cost (Rs)": [machining_cost],
            "Total Cost (Rs)": [total_cost],
        }
        df = pd.DataFrame(data)
    
        st.dataframe(df, use_container_width=True)
    
        # Download Buttons in a clean column layout
        dl_col1, dl_col2, _ = st.columns([1, 1, 4]) 
        
        # CSV Export
        csv = df.to_csv(index=False).encode("utf-8")
        with dl_col1:
            st.download_button(
                label="⬇️ Download CSV",
                data=csv,
                file_name="machining_cost_results.csv",
                mime="text/csv",
                use_container_width=True
            )
    
        # Excel Export (requires openpyxl)
        try:
            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Results")
            excel_data = output.getvalue()
            
            with dl_col2:
                st.download_button(
                    label="⬇️ Download Excel",
                    data=excel_data,
                    file_name="machining_cost_results.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        except ImportError:
            st.warning("⚠️ Excel export requires 'openpyxl'. Please install it (`pip install openpyxl`).")

# --- Initial state or when button is not clicked ---
if not st.session_state.run_calculation:
    with col_results:
        st.header("📈 Cost Analysis Results")
        st.info("👈 Set the raw material and machining parameters, then click **Calculate Cost** to view your financial breakdown.")