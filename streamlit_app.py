import streamlit as st
import pandas as pd
import plotly.express as px

# Path to your CSV file
file_path = "fiches_de_poste_en_tension.csv"

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

# Filter Options
grand_domaine_options = data["grand_domaine"].unique()
domaine_professionnel_options = data["domaine_professionnel"].unique()
rome_options = data["rome"].unique()
type_structure_options = data["type_structure"].unique()

# Function to dynamically generate the label
def generate_label(selected_items, label, default_text=""):
    if len(selected_items) == 0:
        return f"{label}"
    elif len(selected_items) == 1:
        return f"{label}: {selected_items[0]}"
    else:
        return f"{label}: {len(selected_items)} selected"

# Horizontal Filters
st.markdown("### Filtres")
st.markdown("""
- Les filtres fonctionnent avec une logique **OU** :
    - Si plusieurs options sont sélectionnées dans un filtre, les résultats incluront toutes les lignes correspondant à **au moins une** des options sélectionnées.
    - Si plusieurs filtres sont utilisés, les résultats incluront toutes les lignes correspondant à **au moins une** des options de chaque filtre.
- Par défaut, aucun filtre n'est appliqué : aucun résultat n'est affiché.

*Exemple :* Sélectionnez "Santé" dans **Grand Domaines** et "Commerce" dans **Domaines Professionnels** :  
  Vous verrez les données correspondant à **Santé OU Commerce**.
""")
col1, col2, col3, col4 = st.columns(4)

with col1:
    selected_grand_domaine = st.multiselect(
        label="Grands Domaines",
        options=grand_domaine_options,
        default=[]
    )

with col2:
    selected_domaine_professionnel = st.multiselect(
        label="Domaines Professionnels",
        options=domaine_professionnel_options,
        default=[]
    )

with col3:
    selected_rome = st.multiselect(
        label="Codes ROME",
        options=rome_options,
        default=[]
    )

with col4:
    selected_type_structure = st.multiselect(
        label="Types de Structures",
        options=type_structure_options,
        default=[]
    )

# Filter the data based on user selections
filtered_data = data[
    (data["grand_domaine"].isin(selected_grand_domaine)) |
    (data["domaine_professionnel"].isin(selected_domaine_professionnel)) |
    (data["rome"].isin(selected_rome)) |
    (data["type_structure"].isin(selected_type_structure))
]

# Aggregate data by latitude and longitude
aggregated_data = filtered_data.groupby(['latitude', 'longitude'], as_index=False).agg(
    {"nombre_de_fiches_de_poste_en_tension": "sum", "ville": "first"}
)

# Plot filtered view
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
            "nombre_de_fiches_de_poste_en_tension": True,
        },
        color="nombre_de_fiches_de_poste_en_tension",
        size="nombre_de_fiches_de_poste_en_tension",
        size_max=50,
        color_continuous_scale=px.colors.sequential.Viridis,
        mapbox_style="open-street-map",
    )
    map_fig.update_layout(
        mapbox_zoom=5,
        mapbox_center={"lat": 46.603354, "lon": 1.888334}
    )
    st.plotly_chart(map_fig, use_container_width=True)
else:
    st.error("Latitude and Longitude data are not available for mapping.")

# Heatmap
heatmap_data = data.groupby(["type_structure", "grand_domaine"], as_index=False).agg(
    {"nombre_de_fiches_de_poste_en_tension": "sum"}
)

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
top_cities_data = data.groupby('ville', as_index=False).agg(
    {"nombre_de_fiches_de_poste_en_tension": "sum"}
)
top_cities_data = top_cities_data.sort_values(by="nombre_de_fiches_de_poste_en_tension", ascending=False)
top_5_cities = top_cities_data.head(5)
top_5_cities = top_5_cities.rename(
    columns={"nombre_de_fiches_de_poste_en_tension": "# fiches de poste en tension"}
)
st.header("Top 5 des villes avec le plus de postes sous tension")
st.table(top_5_cities.reset_index(drop=True))
