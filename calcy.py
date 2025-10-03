import streamlit as st
import math
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Machining Cost Calculator", layout="wide")

# --- Function to perform the cost calculation for a single part ---
def calculate_cost_for_row(L_raw, D_raw, D_final, density, cost_per_kg, feed_rate, cutting_speed, MHR, extra_time):
    """Calculates material, machining, and total cost for a single part."""
    # --- Material cost ---
    # Volume of raw rod (cylinder) in mm³: pi * r² * L
    volume_mm3 = math.pi * ((D_raw / 2) ** 2) * L_raw
    # Volume in cm³
    volume_cm3 = volume_mm3 / 1000.0
    # Weight in kg: (Volume in cm³ * Density in g/cm³) / 1000
    weight_kg = (volume_cm3 * density) / 1000.0
    material_cost = weight_kg * cost_per_kg

    # --- Machining time (for turning the rod) ---
    # Spindle Speed (N) in rev/min: (1000 * Vc) / (pi * D)
    spindle_speed = (1000.0 * cutting_speed) / (math.pi * D_final)
    # Machining Time (Tm) in min: L / (f * N)
    machining_time = L_raw / (feed_rate * spindle_speed) if spindle_speed > 0 and feed_rate > 0 else float("inf")

    total_time_min = machining_time + extra_time
    total_time_hr = total_time_min / 60.0
    machining_cost = total_time_hr * MHR

    total_cost = material_cost + machining_cost

    return material_cost, machining_cost, total_cost, machining_time, total_time_min

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
    st.write("---")
    st.markdown("""
        **Note on Bulk Calculation:**
        The bulk calculation is currently only available for the **Chamfer** process.
        The uploaded file must contain the columns:
        1.  `length` (for Rod Length in mm)
        2.  `dia` (for Required Diameter in mm)
        3.  `chamfer` (for Chamfer Time in minutes)
    """)

# --- Right: Parameters that change for each calculation ---
with right_col:
    st.header("🛠️ Process Parameters")

    # Common parameters for all processes (for manual input)
    with st.expander("📏 Rod Parameters (Manual Input)", expanded=True):
        L_raw = st.number_input("Rod Length (mm)", 50, 1000, 250, 1, key='L_raw_manual')
        D_raw = st.number_input("Available Rod Diameter (mm)", 10, 200, 38, 1, key='D_raw_manual')
        D_final = st.number_input("Required Diameter (mm)", 5, 200, 36, 1, key='D_final_manual')

    # Process-specific parameters
    extra_time = 0
    depth = 0
    df_bulk = None

    with st.expander("⚙️ Operation Details", expanded=True):
        if process == "Chamfer":
            # --- Bulk Upload Section for Chamfer ---
            st.markdown("### Bulk Calculation (Chamfer only)")
            uploaded_file = st.file_uploader(
                "Upload a CSV or Excel file for batch calculation",
                type=["csv", "xlsx"]
            )

            if uploaded_file is not None:
                try:
                    if uploaded_file.name.endswith('.csv'):
                        df_bulk = pd.read_csv(uploaded_file)
                    else:
                        df_bulk = pd.read_excel(uploaded_file, engine='openpyxl')

                    st.success(f"File uploaded successfully! Loaded {len(df_bulk)} rows.")
                    
                    # Need a common D_raw for all parts in the file
                    D_raw_bulk = st.number_input(
                        "Available Rod Diameter for Bulk Data (mm)", 
                        10, 200, 38, 1, 
                        key='D_raw_bulk'
                    )
                    
                    # Manual inputs are ignored for bulk calculation, but we must define extra_time for the single case
                    extra_time = 0
                
                except Exception as e:
                    st.error(f"Error reading file: {e}")
                    df_bulk = None
            
            if df_bulk is None:
                # Fallback to single calculation if no file is uploaded or upload failed
                st.markdown("### Single Part Calculation")
                extra_time = st.number_input("Chamfer Time (min)", 0, 30, 5, 1, key='extra_time_manual')


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

        if df_bulk is not None:
            # --- BULK CALCULATION ---
            
            # Map columns and perform calculation
            try:
                df_results = df_bulk.copy()
                
                # Apply the calculation function row-wise
                df_results[['Material Cost (Rs)', 'Machining Cost (Rs)', 'Total Cost (Rs)', 
                            'Machining Time (min)', 'Total Time (min)']] = df_results.apply(
                    lambda row: calculate_cost_for_row(
                        L_raw=row['length'],
                        D_raw=D_raw_bulk, # Use the common D_raw for bulk data
                        D_final=row['dia'],
                        density=density,
                        cost_per_kg=cost_per_kg,
                        feed_rate=feed_rate,
                        cutting_speed=cutting_speed,
                        MHR=MHR,
                        extra_time=row['chamfer'] # Use 'chamfer' column as extra time
                    ),
                    axis=1,
                    result_type='expand'
                )

                # --- Results (Bulk) ---
                st.subheader("📊 Bulk Calculation Results")
                st.write(f"Results for {len(df_results)} parts:")
                st.dataframe(df_results, use_container_width=True)

                # --- Export (Bulk) ---
                st.subheader("📥 Export Data")
                
                # Convert DataFrame to Excel in-memory
                output = BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    df_results.to_excel(writer, index=False, sheet_name="Bulk_Results")
                excel_data = output.getvalue()

                st.download_button(
                    label="⬇️ Download All Results (Excel)",
                    data=excel_data,
                    file_name="bulk_calculation_results.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

            except KeyError as e:
                st.error(f"Missing required column for bulk calculation: {e}. Please ensure your file has 'length', 'dia', and 'chamfer' columns.")
            except Exception as e:
                st.error(f"An error occurred during bulk calculation: {e}")

        else:
            # --- SINGLE CALCULATION ---
            if D_final >= D_raw:
                st.error("Error: Required Diameter ($D_{\\text{final}}$) must be less than Available Rod Diameter ($D_{\\text{raw}}$).")
            elif D_raw <= 0 or D_final <= 0 or L_raw <= 0:
                st.error("Error: Diameter and Length values must be positive.")
            else:
                material_cost, machining_cost, total_cost, machining_time, total_time_min = \
                    calculate_cost_for_row(
                        L_raw, D_raw, D_final, density, cost_per_kg, feed_rate, 
                        cutting_speed, MHR, extra_time
                    )

                # --- Results (Single) ---
                st.subheader("📊 Single Part Results")
                col1, col2, col3 = st.columns(3)
                col1.metric("Material Cost (Rs)", f"{material_cost:.2f}")
                col2.metric("Machining Cost (Rs)", f"{machining_cost:.2f}")
                col3.metric("Total Cost (Rs)", f"{total_cost:.2f}")

                # --- Export (Single) ---
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
                    "Machining Time (min)": [machining_time],
                    "Total Time (min)": [total_time_min],
                    "Material Cost (Rs)": [material_cost],
                    "Machining Cost (Rs)": [machining_cost],
                    "Total Cost (Rs)": [total_cost],
                }
                df_single = pd.DataFrame(data)

                st.subheader("📥 Export Data")
                st.dataframe(df_single, use_container_width=True)

                output = BytesIO()

                try:
                    # Try Excel first
                    with pd.ExcelWriter(output, engine="openpyxl") as writer:
                        df_single.to_excel(writer, index=False, sheet_name="Results")
                    excel_data = output.getvalue()

                    st.download_button(
                        label="⬇️ Download Excel",
                        data=excel_data,
                        file_name="calculation_results.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                except ImportError:
                    # Fallback to CSV if openpyxl is not installed
                    csv_data = df_single.to_csv(index=False).encode("utf-8")
                    st.warning("⚠️ Excel export unavailable (openpyxl not found). Falling back to CSV.")
                    st.download_button(
                        label="⬇️ Download CSV",
                        data=csv_data,
                        file_name="calculation_results.csv",
                        mime="text/csv",
                    )