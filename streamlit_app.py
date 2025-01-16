import streamlit as st
import pandas as pd
import plotly.express as px

# Path to your CSV file
file_path = "/Users/thomaspc/streamlit-job-tension/fiches_de_poste_en_tension.csv"

# Load CSV data with caching
@st.cache_data
def load_data(file_path):
    # Load the dataset
    data = pd.read_csv(file_path)
    
    # Create a synthetic "location" column based on latitude and longitude
    if 'latitude' in data.columns and 'longitude' in data.columns:
        data['location'] = data['latitude'].astype(str) + "_" + data['longitude'].astype(str)
        data = data.drop_duplicates(subset=['id_asp', 'location'])
        data = data.drop(columns=['location'])  # Remove synthetic column after processing
    elif 'region' in data.columns:
        # Fallback if latitude/longitude are unavailable
        data = data.drop_duplicates(subset=['id_asp', 'region'])
    else:
        # If no location data, drop duplicates only on id_asp
        data = data.drop_duplicates(subset=['id_asp'])
    
    return data

# Load the data
data = load_data(file_path)

# Interactive Map Visualization

# Step 1: Add Filters 


# Filter Options
grand_domaine_options = data["grand_domaine"].unique()
domaine_professionnel_options = data["domaine_professionnel"].unique()
rome_options = data["rome"].unique()
type_structure_options = data["type_structure"].unique()

# Function to dynamically display the selection label
# Filter Options
grand_domaine_options = data["grand_domaine"].unique()
domaine_professionnel_options = data["domaine_professionnel"].unique()
rome_options = data["rome"].unique()
type_structure_options = data["type_structure"].unique()

# Function to dynamically generate the label
def generate_label(selected_items, label):
    if len(selected_items) == 0:
        return f"{label}: No selection"
    elif len(selected_items) == 1:
        return f"{label}: {selected_items[0]}"
    else:
        return f"{label}: {len(selected_items)} selected"

# Horizontal Filters
st.markdown("### Filters")
col1, col2, col3, col4 = st.columns(4)

with col1:
    selected_grand_domaine = st.multiselect(
        label=generate_label([], "Grand Domaines"),
        options=grand_domaine_options,
        default=[]
    )

with col2:
    selected_domaine_professionnel = st.multiselect(
        label=generate_label([], "Domaine Professionnels"),
        options=domaine_professionnel_options,
        default=[]
    )

with col3:
    selected_rome = st.multiselect(
        label=generate_label([], "ROME Codes"),
        options=rome_options,
        default=[]
    )

with col4:
    selected_type_structure = st.multiselect(
        label=generate_label([], "Structure Types"),
        options=type_structure_options,
        default=[]
    )


# # Step 3: Filter the data based on user selections
filtered_data = data[
    (data["grand_domaine"].isin(selected_grand_domaine)) &
    (data["domaine_professionnel"].isin(selected_domaine_professionnel)) &
    (data["rome"].isin(selected_rome)) &
    (data["type_structure"].isin(selected_type_structure))
]

# Step4: Aggregate data by latitude and longitude
# The .groupby(['latitude', 'longitude'], as_index=False) groups the data by unique latitude and longitude pairs.
# The .agg() function specifies how to aggregate the data: 
# {"nombre_de_fiches_de_poste_en_tension": "sum"}: For each group, it calculates the sum of nombre_de_fiches_de_poste_en_tension.
# {"ville": "first"}: Keeps the first ville in the group for hover information.

aggregated_data = filtered_data.groupby(['latitude', 'longitude'], as_index=False).agg(
    {"nombre_de_fiches_de_poste_en_tension": "sum", "ville": "first"}
)

# Step 5: plot filtered view

st.title("Fiches de postes en tension")
st.markdown("Cette carte visualise les métiers en tension basé sur le nombre de fiches de postes en tension par adresse.")

st.header("Carte interactive")
if "latitude" in aggregated_data.columns and "longitude" in aggregated_data.columns:
    map_fig = px.scatter_mapbox(
        aggregated_data,
        lat="latitude",
        lon="longitude",
        hover_name="ville",
        hover_data={
            "nombre_de_fiches_de_poste_en_tension": True,  # Show total job tension
        },
        color="nombre_de_fiches_de_poste_en_tension",
        size="nombre_de_fiches_de_poste_en_tension",  # Circle size by total tension
        size_max=50,  # Max circle size
        color_continuous_scale=px.colors.sequential.Viridis,  # Color scale
        mapbox_style="open-street-map",
    )
    map_fig.update_layout(
        mapbox_zoom=5,  # Set default zoom level to cover all of France
        mapbox_center={"lat": 46.603354, "lon": 1.888334}  # Center the map over France
    )
    st.plotly_chart(map_fig, use_container_width=True)  # Ensure the map is big
else:
    st.error("Latitude and Longitude data are not available for mapping.")

# Heatmap: Aggregate data by type_structure and grand_domaine

heatmap_data = filtered_data.groupby(["type_structure", "grand_domaine"], as_index=False).agg(
    {"nombre_de_fiches_de_poste_en_tension": "sum"}
)

# Plot the Heatmap
st.title("Heatmap sur les métiers en tension selon domaine / catégorie")
fig = px.density_heatmap(
    heatmap_data,
    x="type_structure",
    y="grand_domaine",
    z="nombre_de_fiches_de_poste_en_tension",
    color_continuous_scale="Viridis",
    labels={
        "type_structure": "Structure Type",
        "grand_domaine": "Grand Domain",
        "nombre_de_fiches_de_poste_en_tension": "Job Tensions"
    },
)
fig.update_layout(
    xaxis=dict(tickangle=45),
    margin=dict(l=0, r=0, t=30, b=0),
    height=600
)

st.plotly_chart(fig, use_container_width=True)


# Table of top cities

# Step 1: Aggregate data by city
# as_index=False ensures that when you group data using groupby(), the grouped columns (e.g., ville) are kept as regular columns in the resulting DataFrame rather than being set as the index.
top_cities_data = data.groupby('ville', as_index=False).agg(
    {"nombre_de_fiches_de_poste_en_tension": "sum"}
)

# Step 2: Sort the data by job tension in descending order
top_cities_data = top_cities_data.sort_values(
    by="nombre_de_fiches_de_poste_en_tension", ascending=False
)

# Step 3: Select the top 5 cities
top_5_cities = top_cities_data.head(5)

# Step 4: Rename the columns for clarity
top_5_cities = top_5_cities.rename(
    columns={
        "nombre_de_fiches_de_poste_en_tension": "# fiches de poste en tension"
    }
)
# Step 5: Display the table in Streamlit
st.header("Top 5 des villes avec le plus de postes sous tension")
st.table(top_5_cities.reset_index(drop=True))  # Reset the index and drop the old one
