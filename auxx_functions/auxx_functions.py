import geopandas as gpd
import pandas as pd 
import json
from esda import Moran, Moran_Local, G_Local
from libpysal.weights import W
from typing import Tuple, Union, Dict, List
from plotly.subplots import make_subplots
import plotly.express as px
import plotly.graph_objects as go
import altair as alt

def shp_to_json(shapefile: gpd.GeoDataFrame):
    shapefile['geometry'] = shapefile['geometry'].simplify(0.01)
    shapefile['const'] = 1
    geojson = json.loads(shapefile.to_json())
    
    return shapefile, geojson

def autocorr_stats(y: pd.Series,
                   w: W, 
                   autocorr_df: pd.DataFrame,
                   metric: str) -> Union[Tuple[float, pd.DataFrame], pd.DataFrame]:
    
    if metric == 'Global Morans I':
        
        global_moransI =Moran(y, w)
        return global_moransI, autocorr_df
    
    elif metric == 'Local Morans I':
        
        quadrant_colors = {
        1: 'rgb(23, 28, 66)',    # HH - Alto-Alto
        2: 'rgb(72, 202, 228)',   # LH - Baixo-Alto
        3: 'rgb(224, 30, 55)',  # LL - Baixo-Baixo
        4: 'rgb(120, 14, 40)', # HL - Alto-Baixo
        }
        
        nonsignificant_color = 'lightgray'

        lisa = Moran_Local(y, w)
        autocorr_df['LISA'] = lisa.Is
        autocorr_df['Significância_lisa'] = lisa.p_sim
        autocorr_df['quadrant'] = lisa.q

        autocorr_df['color'] = autocorr_df.apply(
            lambda row: quadrant_colors.get(row['quadrant'], nonsignificant_color) if row['Significância_lisa'] < 0.05 else nonsignificant_color,
            axis=1
        )

        autocorr_df['quadrant'] = autocorr_df.apply(
            lambda row: 0 if row['color'] == 'lightgray' else row['quadrant'],
            axis=1
        )
        
        
        return autocorr_df
    
    elif metric == 'G_local':
        gi_star = G_Local(y, w, star=True)
        autocorr_df['Gi*'] = gi_star.Zs
        autocorr_df['Significância_Gi*'] = gi_star.p_sim
        
        # Categoriza cada região como Hotspot, Coldspot ou Não Significativo
        def categorize(row):
            if row['Gi*'] > 1.96 and row['Significância_Gi*'] < 0.05:
                return 'Hotspot'
            elif row['Gi*'] < -1.96 and row['Significância_Gi*'] < 0.05:
                return 'Coldspot'
            else:
                return 'Não significativo'
        autocorr_df['category'] = autocorr_df.apply(categorize, axis=1)
        return autocorr_df
    else:
        raise ValueError(f"Métrica '{metric}' não reconhecida. Escolha entre 'Global Morans I', 'Local Morans I' ou 'G_local'.")

def mapa_dist_altair(geojson: Dict, nome_variavel_interesse: str) -> alt.Chart:
    """
    Plota um mapa coroplético usando Altair.

    Args:
        geojson (Dict): GeoJSON contendo os dados dos estados.
        nome_variavel_interesse (str): Nome da variável de interesse para exibição no mapa.

    Returns:
        alt.Chart: Gráfico Altair contendo o mapa coroplético.
    """
    # Carregar o GeoJSON como fonte de dados para Altair
    geojson_data = alt.Data(values=geojson['features'])

    # Criar o mapa coroplético
    chart = alt.Chart(geojson_data).mark_geoshape(
        stroke='black',
        strokeWidth=0.5
    ).encode(
        color=alt.Color(f'properties.{nome_variavel_interesse}:Q', 
                        title=f'Valor do {nome_variavel_interesse}',
                        scale=alt.Scale(scheme='tealblues')),
        tooltip=[
            alt.Tooltip('properties.state:N', title='Estado'),
            alt.Tooltip(f'properties.{nome_variavel_interesse}:Q', 
                        title=f'Valor do {nome_variavel_interesse}', format=',.2f')
        ]
    ).properties(
        width=800,
        height=500
    ).project(
        type='mercator',
        center=[-95.7129, 37.0902],
        scale=500
    ).interactive()

    return chart


def G_local_altair(geojson: Dict, nome_variavel_interesse: str) -> alt.Chart:
    """
    Plota um mapa coroplético para identificar Hotspots e Coldspots usando Altair.

    Args:
        geojson (Dict): GeoJSON contendo os dados dos estados.
        nome_variavel_interesse (str): Nome da variável de interesse (Z-score da Gi*).

    Returns:
        alt.Chart: Gráfico Altair contendo o mapa coroplético.
    """
    # Carregar o GeoJSON como fonte de dados para Altair
    geojson_data = alt.Data(values=geojson['features'])

    # Obter valores do Z-score para definir a escala de cores
    gi_values = [feature['properties'][nome_variavel_interesse] for feature in geojson['features']]
    gi_min = min(gi_values)
    gi_max = max(gi_values)

    # Definir esquema de cores contínuo para refletir a intensidade do Z-score
    color_scale = alt.Scale(
        domain=[gi_min, 0, gi_max],
        range=['rgb(23, 28, 66)', 'lightgray', 'rgb(224, 30, 55)']
    )

    # Criar o mapa
    mapa = alt.Chart(geojson_data).mark_geoshape(
        stroke='black',
        strokeWidth=0.5
    ).encode(
        color=alt.Color(f'properties.{nome_variavel_interesse}:Q', title='Z-score', scale=color_scale),
        tooltip=[
            alt.Tooltip('properties.state:N', title='Estado'),
            alt.Tooltip(f'properties.{nome_variavel_interesse}:Q', title='Z-score', format=".2f")
        ]
    ).properties(
        width=800,
        height=500,
        title="Identificação de Hot e Coldspots pela Gi*"
    ).project(
        type='mercator',
        center=[-95.7129, 37.0902],
        scale=500  # Ajuste a escala conforme necessário
    ).configure_view(
        stroke=None
    ).interactive()

    return mapa

def line_plot_with_dropdown(df, date_col, value_col, category_col):
    """
    Cria um gráfico de linha simples que visualiza 'value_col' ao longo de 'date_col',
    com um dropdown para selecionar uma categoria de 'category_col'.

    Args:
        df (pd.DataFrame): DataFrame contendo os dados.
        date_col (str): Nome da coluna de datas (por exemplo, 'transaction_dt').
        value_col (str): Nome da coluna de valores (por exemplo, 'transaction_amt').
        category_col (str): Nome da coluna categórica (por exemplo, 'entity_type').

    Returns:
        alt.Chart: Gráfico Altair com o line plot e o dropdown.
    """

    # Garantir que a coluna de datas esteja no formato datetime
    if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
        df[date_col] = df[date_col].astype(int).astype(str).str.zfill(8)
        df[date_col] = pd.to_datetime(df[date_col], format='%m%d%Y')

    # Filtrar os dados para o intervalo de 2011 a 2013
    filtered_df = df[(df[date_col].dt.year >= 2011) & (df[date_col].dt.year <= 2013)]

    # Agregar os dados por mês e categoria
    aggregated = filtered_df.groupby([pd.Grouper(key=date_col, freq='M'), category_col])[value_col].sum().reset_index()

    # Criar o dropdown para selecionar a categoria
    category_dropdown = alt.binding_select(options=sorted(aggregated[category_col].unique()), name="Categoria: ")
    category_param = alt.param(name="selected_category", bind=category_dropdown, value=aggregated[category_col].unique()[0])

    # Filtrar os dados com base na categoria selecionada
    line_chart = alt.Chart(aggregated).transform_filter(
        alt.datum[category_col] == category_param
    ).mark_line(point=True).encode(
        x=alt.X(f"{date_col}:T", title="Data"),
        y=alt.Y(f"{value_col}:Q", title="Valor Total"),
        tooltip=[
            alt.Tooltip(f"{date_col}:T", title="Data", format="%Y-%m"),
            alt.Tooltip(f"{value_col}:Q", title="Valor Total", format=",.0f"),
            alt.Tooltip(f"{category_col}:N", title="Categoria")
        ]
    ).add_params(
        category_param
    ).properties(
        width=800,
        height=400,
        title=f"Valor das Transações por {category_col} ao Longo do Tempo (2011-2013)"
    ).interactive()

    return line_chart
