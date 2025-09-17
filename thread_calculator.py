import streamlit as st
import math

# Material properties for rolling speed and tool life
materials = {
    "Aluminium Alloys": {"speed": (20, 60), "n": 0.3, "C": (80, 120)},
    "Brass & Copper": {"speed": (15, 40), "n": 0.25, "C": (60, 100)},
    "Mild Steel": {"speed": (10, 30), "n": 0.2, "C": (40, 80)},
    "Medium Carbon Steel": {"speed": (8, 25), "n": 0.18, "C": (30, 70)},
    "High Carbon Steel": {"speed": (5, 15), "n": 0.15, "C": (20, 60)},
    "Alloy Steel": {"speed": (5, 15), "n": 0.13, "C": (15, 50)},
    "Stainless Steel": {"speed": (4, 12), "n": 0.12, "C": (10, 40)},
    "Titanium Alloys": {"speed": (3, 8), "n": 0.1, "C": (5, 25)},
}

st.title("Thread Rolling Calculator")

# Inputs
material = st.selectbox("Select Material", list(materials.keys()))
D = st.number_input("Thread Major Diameter (mm)", min_value=1.0, value=10.0)
P = st.number_input("Thread Pitch (mm)", min_value=0.1, value=1.5)
L = st.number_input("Thread Length (mm)", min_value=1.0, value=20.0)
S = st.slider("Rolling Speed (m/min)", 
              min_value=materials[material]["speed"][0],
              max_value=materials[material]["speed"][1],
              value=materials[material]["speed"][0])

# Cost Inputs
density = st.number_input("Material Density (g/cm³)", min_value=0.1, value=7.85)
cost_per_kg = st.number_input("Material Cost per kg ($)", min_value=0.1, value=1.0)
volume = st.number_input("Material Volume (cm³)", min_value=1.0, value=100.0)
machine_rate = st.number_input("Machine Hourly Rate ($/hr)", min_value=1.0, value=20.0)
operator_rate = st.number_input("Operator Hourly Rate ($/hr)", min_value=1.0, value=15.0)
tool_cost = st.number_input("Tool Cost ($)", min_value=1.0, value=100.0)
tool_life_parts = st.number_input("Tool Life (parts)", min_value=1, value=1000)

# Calculations
N = (1000 * S) / (math.pi * D)  # Spindle RPM
F = N * P  # Feed rate (mm/min)
T = L / F  # Time (min)

# Costs
material_cost = volume * density * cost_per_kg / 1000  # convert g to kg
machine_cost = (machine_rate / 60) * T
labor_cost = (operator_rate / 60) * T
tooling_cost = tool_cost / tool_life_parts
total_cost = material_cost + machine_cost + labor_cost + tooling_cost

# Results
st.subheader("Results")
st.write(f"**Spindle RPM (N):** {N:.2f}")
st.write(f"**Feed Rate (F):** {F:.2f} mm/min")
st.write(f"**Thread Rolling Time (T):** {T:.2f} min")
st.write(f"**Material Cost:** ${material_cost:.2f}")
st.write(f"**Machine Cost:** ${machine_cost:.2f}")
st.write(f"**Labor Cost:** ${labor_cost:.2f}")
st.write(f"**Tooling Cost per Part:** ${tooling_cost:.2f}")
st.write(f"### Total Cost per Part: ${total_cost:.2f}")
