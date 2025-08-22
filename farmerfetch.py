import streamlit as st
import pandas as pd
from io import BytesIO
from supabase import create_client, Client

# ---------------- Supabase Setup ----------------
# Fetch from secrets
import os
print("DEBUG SUPABASE_URL:", os.getenv("SUPABASE_URL"))
print("DEBUG SUPABASE_KEY:", os.getenv("SUPABASE_KEY"))
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

# Create Supabase client
supabase: Client = create_client(supabase_url, supabase_key)

st.logo("AgriSavant Logo wo tagline white wo tagline.png", size="large")
st.title("Agrisavant-kagome dashboard")

# ✅ Helper function to safely convert date strings/None
def to_date(val):
    if not val:
        return pd.Timestamp.today().date()
    try:
        return pd.to_datetime(val).date()
    except Exception:
        return pd.Timestamp.today().date()

# ---------------- Fetch Existing Farmers ----------------
farmers = supabase.table("farmers").select("*").execute()
farmer_options = {f["farmer_name"]: f["farmer_id"] for f in farmers.data}

# Dropdown to select farmer
selected_farmer = st.selectbox(
    "Select Farmer to Edit (or add new)",
    ["➕ Add New Farmer"] + list(farmer_options.keys())
)

farmer_data, nursery_data = {}, {}
farmer_id = None

if selected_farmer != "➕ Add New Farmer":
    farmer_id = farmer_options[selected_farmer]
    # Fetching all the data from the tables as per selected farmer
    farmer_data = supabase.table("farmers").select("*").eq("farmer_id", farmer_id).execute().data[0]
    nursery = supabase.table("nursery").select("*").eq("farmer_id", farmer_id).execute().data
    nursery_data = nursery[0] if nursery else {}
    spraying_data = supabase.table("spraying").select("*").eq("farmer_id", farmer_id).execute().data
    harvesting_data = supabase.table("harvesting").select("*").eq("farmer_id", farmer_id).execute().data
    receiving_data = supabase.table("receiving").select("*").eq("farmer_id", farmer_id).execute().data
    # ✅ Initialize session state with DB values (only once per farmer load)
    if "last_farmer" not in st.session_state or st.session_state.last_farmer != farmer_id:
        st.session_state.spraying = spraying_data.copy()
        st.session_state.harvesting = harvesting_data.copy()
        st.session_state.receiving = receiving_data.copy()
        st.session_state.last_farmer = farmer_id
else:
    # For adding new farmer, reset everything
    st.session_state.spraying = []
    st.session_state.harvesting = []
    st.session_state.receiving = []
    st.session_state.last_farmer = None

# ---------- Tabs ----------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "👨‍🌾 Farmer Info", "🌱 Nursery", "🧪 Spraying", "🌾 Harvesting", "📥 Receiving"
])

# ---------- Farmer Info ----------
with tab1:
    farmer_code = st.text_input("Farmer Code", farmer_data.get("farmer_code", ""))
    farmer_name = st.text_input("Farmer Name", farmer_data.get("farmer_name", ""))
    area = st.text_input("Area (location)", farmer_data.get("area", ""))
    soil_type = st.text_input("Soil Type", farmer_data.get("soil_type", ""))
    field = st.text_input("Field", farmer_data.get("field", ""))
    contract_date = st.date_input("Contract Date", value=to_date(farmer_data.get("contract_date")))
    contracted_area = st.text_input("Contracted Area (in acres)", farmer_data.get("contracted_area", ""))

# ---------- Nursery Info ----------
with tab2:
    seedling_supplier = st.text_input("Seedling Supplier", nursery_data.get("seedling_supplier", ""))
    seeding_receive_date = st.date_input("Seeding Receive Date", value=to_date(nursery_data.get("seeding_receive_date")))
    seeding_receive_qty = st.number_input("Seeding Receive Qty", min_value=0, value=int(nursery_data.get("seeding_receive_qty", 0)))
    transplanting_date = st.date_input("Transplanting Date", value=to_date(nursery_data.get("transplanting_date")))
    transplanting_qty_seedling = st.number_input("Transplanting Qty Seedling", min_value=0, value=int(nursery_data.get("transplanting_qty_seedling", 0)))

# ---------- Spraying ----------
with tab3:
    st.write("🧪 Spraying Records")
    for i, spray in enumerate(st.session_state.spraying):
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
        with col1:
            spray["chemical_name"] = st.text_input(f"Chemical {i+1}", value=spray.get("chemical_name", ""), key=f"chem_{i}")
        with col2:
            spray["spraying_date"] = st.date_input(f"Date {i+1}", value=to_date(spray.get("spraying_date")), key=f"spray_date_{i}")
        with col3:
            spray["spraying_qty"] = st.number_input(f"Qty {i+1} (ml) ", min_value=0, value=int(spray.get("spraying_qty", 0)), key=f"spray_qty_{i}")
        with col4:
            if st.button("❌", key=f"del_spray_{i}"):
                st.session_state.spraying.pop(i)
                st.rerun()
    if st.button("➕ Add Spraying Entry"):
        st.session_state.spraying.append({"chemical_name": "", "spraying_date": None, "spraying_qty": 0})

# ---------- Harvesting ----------
with tab4:
    st.write("🌾 Harvesting Records")
    for i, harvest in enumerate(st.session_state.harvesting):
        col1, col2, col3 = st.columns([3, 2, 1])
        with col1:
            harvest["harvest_date"] = st.date_input(f"Harvest Date {i+1}", value=to_date(harvest.get("harvest_date")), key=f"harvest_date_{i}")
        with col2:
            harvest["harvest_qty"] = st.number_input(f"Qty {i+1} (ml)", min_value=0, value=int(harvest.get("harvest_qty", 0)), key=f"harvest_qty_{i}")
        with col3:
            if st.button("❌", key=f"del_harvest_{i}"):
                st.session_state.harvesting.pop(i)
                st.rerun()
    if st.button("➕ Add Harvest Entry"):
        st.session_state.harvesting.append({"harvest_date": None, "harvest_qty": 0})

# ---------- Receiving ----------
with tab5:
    st.write("📥 Receiving Records")
    for i, recv in enumerate(st.session_state.receiving):
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
        with col1:
            recv["receiving_date"] = st.date_input(f"Receiving Date {i+1}", value=to_date(recv.get("receiving_date")), key=f"recv_date_{i}")
        with col2:
            recv["receiving_qty"] = st.number_input(f"Qty {i+1}", min_value=0, value=int(recv.get("receiving_qty", 0)), key=f"recv_qty_{i}")
        with col3:
            recv["accepted_qty"] = st.number_input(f"Accepted {i+1}", min_value=0, value=int(recv.get("accepted_qty", 0)), key=f"recv_acc_{i}")
        with col4:
            if st.button("❌", key=f"del_recv_{i}"):
                st.session_state.receiving.pop(i)
                st.rerun()
    if st.button("➕ Add Receiving Entry"):
        st.session_state.receiving.append({"receiving_date": None, "receiving_qty": 0, "accepted_qty": 0})

# ---------- Save Button ----------
if st.button("💾 Save Changes"):
    try:
        if farmer_id:  # Update existing farmer
            # Update farmer info
            supabase.table("farmers").update({
                "farmer_code": farmer_code,
                "farmer_name": farmer_name,
                "area": area,
                "soil_type": soil_type,
                "field": field,
                "contract_date": str(contract_date),
                "contracted_area": contracted_area
            }).eq("farmer_id", farmer_id).execute()

            # Update nursery info
            supabase.table("nursery").upsert({
                "farmer_id": farmer_id,
                "seedling_supplier": seedling_supplier,
                "seeding_receive_date": str(seeding_receive_date),
                "seeding_receive_qty": seeding_receive_qty,
                "transplanting_date": str(transplanting_date),
                "transplanting_qty_seedling": transplanting_qty_seedling
            }).execute()

            # Delete and re-insert spraying records if any
            supabase.table("spraying").delete().eq("farmer_id", farmer_id).execute()
            if st.session_state.spraying:
                supabase.table("spraying").insert([
                    {
                        "farmer_id": farmer_id,
                        "chemical_name": s.get("chemical_name", ""),
                        "spraying_date": str(to_date(s.get("spraying_date"))),
                        "spraying_qty": s.get("spraying_qty", 0)
                    }
                    for s in st.session_state.spraying
                ]).execute()

            # Delete and re-insert harvesting records if any
            supabase.table("harvesting").delete().eq("farmer_id", farmer_id).execute()
            if st.session_state.harvesting:
                supabase.table("harvesting").insert([
                    {
                        "farmer_id": farmer_id,
                        "harvest_date": str(to_date(h.get("harvest_date"))),
                        "harvest_qty": h.get("harvest_qty", 0)
                    }
                    for h in st.session_state.harvesting
                ]).execute()

            # Delete and re-insert receiving records if any
            supabase.table("receiving").delete().eq("farmer_id", farmer_id).execute()
            if st.session_state.receiving:
                supabase.table("receiving").insert([
                    {
                        "farmer_id": farmer_id,
                        "receiving_date": str(to_date(r.get("receiving_date"))),
                        "receiving_qty": r.get("receiving_qty", 0),
                        "accepted_qty": r.get("accepted_qty", 0)
                    }
                    for r in st.session_state.receiving
                ]).execute()

            st.success("✅ Farmer record updated successfully!")

        else:  # Insert new farmer
            # Insert farmer info
            farmer_insert = supabase.table("farmers").insert({
                "farmer_code": farmer_code,
                "farmer_name": farmer_name,
                "area": area,
                "soil_type": soil_type,
                "field": field,
                "contract_date": str(contract_date),
                "contracted_area": contracted_area
            }).execute()
            farmer_id = farmer_insert.data[0]["farmer_id"]

            # Insert nursery info
            supabase.table("nursery").insert({
                "farmer_id": farmer_id,
                "seedling_supplier": seedling_supplier,
                "seeding_receive_date": str(seeding_receive_date),
                "seeding_receive_qty": seeding_receive_qty,
                "transplanting_date": str(transplanting_date),
                "transplanting_qty_seedling": transplanting_qty_seedling
            }).execute()

            # Insert spraying records if any
            if st.session_state.spraying:
                supabase.table("spraying").insert([
                    {
                        "farmer_id": farmer_id,
                        "chemical_name": s.get("chemical_name", ""),
                        "spraying_date": str(to_date(s.get("spraying_date"))),
                        "spraying_qty": s.get("spraying_qty", 0)
                    }
                    for s in st.session_state.spraying
                ]).execute()

            # Insert harvesting records if any
            if st.session_state.harvesting:
                supabase.table("harvesting").insert([
                    {
                        "farmer_id": farmer_id,
                        "harvest_date": str(to_date(h.get("harvest_date"))),
                        "harvest_qty": h.get("harvest_qty", 0)
                    }
                    for h in st.session_state.harvesting
                ]).execute()

            # Insert receiving records if any
            if st.session_state.receiving:
                supabase.table("receiving").insert([
                    {
                        "farmer_id": farmer_id,
                        "receiving_date": str(to_date(r.get("receiving_date"))),
                        "receiving_qty": r.get("receiving_qty", 0),
                        "accepted_qty": r.get("accepted_qty", 0)
                    }
                    for r in st.session_state.receiving
                ]).execute()

            st.success("✅ New farmer record added successfully!")

    except Exception as e:
        st.error(f"❌ Error saving data: {e}")
        
# ---------------- Download All Data ----------------
if farmer_id or selected_farmer == "➕ Add New Farmer":
    st.subheader("📋 Download All Data")

    # Prepare data for all tabs
    farmer_data = {
        "Farmer Code": farmer_code,
        "Farmer Name": farmer_name,
        "Area": area,
        "Soil Type": soil_type,
        "Field": field,
        "Contract Date": str(contract_date),
        "Contracted Area": contracted_area,
        "Seedling Supplier": seedling_supplier,
        "Seeding Receive Date": str(seeding_receive_date),
        "Seeding Receive Qty": seeding_receive_qty,
        "Transplanting Date": str(transplanting_date),
        "Transplanting Qty Seedling": transplanting_qty_seedling,
    }

    # Create a list to hold all rows
    all_data = [farmer_data]

    # Add spraying data
    for i, spray in enumerate(st.session_state.spraying):
        all_data.append({
            "Spraying Chemical": spray.get("chemical_name", ""),
            "Spraying Date": str(to_date(spray.get("spraying_date"))),
            "Spraying Qty": spray.get("spraying_qty", 0),
        })

    # Add harvesting data
    for i, harvest in enumerate(st.session_state.harvesting):
        all_data.append({
            "Harvest Date": str(to_date(harvest.get("harvest_date"))),
            "Harvest Qty": harvest.get("harvest_qty", 0),
        })

    # Add receiving data
    for i, recv in enumerate(st.session_state.receiving):
        all_data.append({
            "Receiving Date": str(to_date(recv.get("receiving_date"))),
            "Receiving Qty": recv.get("receiving_qty", 0),
            "Accepted Qty": recv.get("accepted_qty", 0),
        })

    # Convert to DataFrame
    df = pd.DataFrame(all_data)

    # Export to Excel
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name="All Data", index=False)

    buffer.seek(0)
    st.download_button(
        label="📥 Download All Data as Excel",
        data=buffer,
        file_name="farmer_records.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
