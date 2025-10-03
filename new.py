import streamlit as st
import math
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Machining Cost Calculator", layout="wide")

# --- Sidebar for process selection ---
st.sidebar.title("⚙️ Select Process / Operation")
process = st.sidebar.radio(
    "Choose an operation:",
    [
        "Chamfer",
        "Chamfer Drill Slot",
        "Chamfer Groove Slot",
        "Chamfer Groove Drill"
    ]
)

st.sidebar.markdown("---")
st.sidebar.header("Default Parameters")

# --- Default parameters (common across all processes) with collapsible section ---
with st.sidebar.expander("⚡ Default Parameters", expanded=True):
    density = st.number_input("Density (g/cm³)", 1.0, 20.0, 7.85, 0.01)
    cost_per_kg = st.number_input("Cost per kg (Rs)", 1, 200, 55, 1)
    feed_rate = st.number_input("Feed Rate (mm/rev)", 0.05, 1.0, 0.20, 0.01)
    cutting_speed = st.number_input("Cutting Speed (m/min)", 5, 100, 20, 1)
    MHR = st.number_input("Machine Hour Rate (Rs/hr)", 100, 2000, 800, 50)

# --- Layout with two main columns ---
left_col, right_col = st.columns([1.2, 1])

# --- Left: Process Info ---
with left_col:
    st.title("✨ Machining Cost Calculator")

    # Emoji icons for each process
    process_icons = {
        "Chamfer": "✂️",
        "Chamfer Drill Slot": "🛠️",
        "Chamfer Groove Slot": "⚒️",
        "Chamfer Groove Drill": "🔩"
    }

    st.subheader(f"{process_icons.get(process, '⚙️')} Selected Process: {process}")
    st.write("Default parameters are fixed in the sidebar. Fill in the process-specific parameters on the right.")

# --- Right: Parameters that change for each calculation ---
with right_col:
    st.header("🛠️ Process Parameters")

    # Common parameters for all processes
    with st.expander("📏 Rod Parameters", expanded=True):
        L_raw = st.number_input("Rod Length (mm)", 50, 1000, 250, 1)
        D_raw = st.number_input("Available Rod Diameter (mm)", 10, 200, 38, 1)
        D_final = st.number_input("Required Diameter (mm)", 5, 200, 36, 1)

    # Process-specific parameters
    extra_time = 0
    depth = 0

    with st.expander("⚙️ Operation Details", expanded=True):
        if process == "Chamfer":
            extra_time = st.number_input("Chamfer Time (min)", 0, 30, 5, 1)

        elif process == "Chamfer Drill Slot":
            depth = st.number_input("Drill Depth (mm)", 1, 200, 20, 1)
            extra_time = st.number_input("Drill Slot Time (min)", 0, 60, 10, 1)

        elif process == "Chamfer Groove Slot":
            depth = st.number_input("Groove Depth (mm)", 1, 200, 15, 1)
            extra_time = st.number_input("Groove Slot Time (min)", 0, 60, 8, 1)

        elif process == "Chamfer Groove Drill":
            depth = st.number_input("Groove Drill Depth (mm)", 1, 200, 25, 1)
            extra_time = st.number_input("Groove Drill Time (min)", 0, 60, 12, 1)

    # --- Calculate Button ---
    if st.button("🚀 Calculate Cost", use_container_width=True):
        # --- Material cost ---
        volume_mm3 = math.pi * ((D_raw / 2) ** 2) * L_raw
        volume_cm3 = volume_mm3 / 1000.0
        weight_kg = (volume_cm3 * density) / 1000.0
        material_cost = weight_kg * cost_per_kg

        # --- Machining time ---
        spindle_speed = (1000.0 * cutting_speed) / (math.pi * D_final)
        machining_time = L_raw / (feed_rate * spindle_speed) if spindle_speed > 0 else float("inf")

        total_time_min = machining_time + extra_time
        total_time_hr = total_time_min / 60.0
        machining_cost = total_time_hr * MHR

        total_cost = material_cost + machining_cost

        # --- Results ---
        st.subheader("📊 Results")
        col1, col2, col3 = st.columns(3)
        col1.metric("Material Cost (Rs)", f"{material_cost:.2f}")
        col2.metric("Machining Cost (Rs)", f"{machining_cost:.2f}")
        col3.metric("Total Cost (Rs)", f"{total_cost:.2f}")

        # --- Export ---
        data = {
            "Process": [process],
            "Rod Length (mm)": [L_raw],
            "Available Rod Dia (mm)": [D_raw],
            "Required Dia (mm)": [D_final],
            "Density (g/cm³)": [density],
            "Cost/kg (Rs)": [cost_per_kg],
            "Feed Rate (mm/rev)": [feed_rate],
            "Cutting Speed (m/min)": [cutting_speed],
            "MHR (Rs/hr)": [MHR],
            "Extra Time (min)": [extra_time],
            "Material Cost (Rs)": [material_cost],
            "Machining Cost (Rs)": [machining_cost],
            "Total Cost (Rs)": [total_cost],
        }
        df = pd.DataFrame(data)

        st.subheader("📥 Export Data")
        st.dataframe(df, use_container_width=True)

        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Results")
        excel_data = output.getvalue()

        st.download_button(
            label="⬇️ Download Excel",
            data=excel_data,
            file_name="calculation_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    else:
        st.info("Enter parameters and click **Calculate Cost** to see results.")

st.markdown("---")
st.caption("Dependencies: `streamlit`, `pandas`, `openpyxl`")