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

def mapa_dist(geojson: Dict,
              indices: Union[pd.Series, List[Union[str, int]]],
              estados: Union[pd.Series, List[str]],
              variavel_interesse: Union[pd.Series, List[float]],
              nome_variavel_interesse: str) -> go.Figure:   
    
    """
    Plots a choropleth map showing the distribution of a variable of interest across municipalities,
    with immediate regions overlaid.

    Args:
        geojson (dict): GeoJSON data for the municipalities.
        indices (pd.Series or list): Municipality indices corresponding to the 'locations' in the GeoJSON.
        municipios (pd.Series or list): Municipality names.
        variavel_interesse (pd.Series or list): Values of the variable of interest for each municipality.
        nome_variavel_interesse (str): Name of the variable of interest (for labeling).
        geojson_regiao_imediata (dict): GeoJSON data for the immediate regions.
        indices_regiao_imediata (pd.Series or list): Region indices corresponding to the GeoJSON.
        constante (pd.Series or list): Constant values used to overlay the immediate regions.

    Returns:
        go.Figure: A Plotly Figure object containing the choropleth map.
        
    """
    
    colorscale = px.colors.diverging.balance
    
    fig = go.Figure()
    fig.add_trace(go.Choroplethmap(
        geojson=geojson,
        locations=indices,
        z=variavel_interesse,
        colorscale=colorscale,
        marker_opacity=0.8,
        marker_line_width=0.5,
        colorbar_title=f"Valor do {nome_variavel_interesse}",
        text=estados,
        hoverinfo='text+z'
    ))
        
    fig.update_layout(
    map_zoom=4.0,  # Ajuste o nível de zoom para incluir todos os estados
    map_center={"lat": 37.0902, "lon": -95.7129},  # Centro aproximado dos EUA
    margin={"r": 0, "t": 0, "l": 0, "b": 0},
    map_style='carto-positron',
    paper_bgcolor="rgba(0, 0, 0, 0)",
    font=dict(color='black'),
    
)

    
    return fig
    

import plotly.graph_objects as go
from plotly.subplots import make_subplots


def morans_i(autocorr, morans_i_lag, geojson, variavel_interesse, variavel_interesse_lag):
    
    # Plot Morans'I e LISA
    fig = make_subplots(rows=1,
                        cols=2,
                        subplot_titles=(f"Moran's I Scatter Plot: {morans_i_lag.I:.3f}, p-valor: {morans_i_lag.p_sim}", "LISA Cluster Map"),
                        specs=[[{'type': 'scatter'}, {'type': 'choroplethmap'}]])

    fig.add_trace(
        go.Scatter(
            x=autocorr[variavel_interesse],
            y=autocorr[variavel_interesse_lag],
            mode='markers',
            text=autocorr['state'],
            marker=dict(size=8, color='rgba(23, 28, 66, 0.7)'),
            showlegend=False),

        row=1, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=[autocorr[variavel_interesse].min(), autocorr[variavel_interesse].max()],
            y=[autocorr[variavel_interesse_lag].min(), autocorr[variavel_interesse_lag].max()],
            mode='lines',
            line=dict(color='rgba(0, 0, 0, 0.6)', dash='dash'),
            showlegend=False
        ),
        row=1, col=1
    )

    fig.update_xaxes(title_text=f"Valores Observados ({variavel_interesse})", row=1, col=1) 
    fig.update_yaxes(title_text=f"Lag Espacial ({variavel_interesse_lag})", row=1, col=1)       

    fig.add_trace(
        go.Choroplethmap(
            geojson=geojson,
            locations=autocorr.index,
            z=autocorr['quadrant'],
            colorscale=[
            [0, 'lightgray'],
            [0.25, 'rgb(23, 28, 66)'],
            [0.5,'rgb(72, 202, 228)'],
            [0.75,'rgb(224, 30, 55)' ],
            [1, 'rgb(120, 14, 40)']
            ],
            marker_opacity=0.8,
            marker_line_width=0.5,
            text=autocorr['state'],
            hoverinfo='text+z',
            showscale=False

    ), row=1, col=2)

    fig.update_layout(
        map_zoom=0,
        map_center={"lat": -22.45, "lon": -48.63},
        map_style ='carto-positron',
        paper_bgcolor = 'rgba(0, 0, 0, 0)',
        font=dict(color='black')

    )

    return fig

def G_local(Estados: pd.Series,
            gi: Union[pd.Series, List[float]],
            geojson: Dict, 
            indices: Union[pd.Series, List[Union[str, int]]]) -> go.Figure:

    """
    Plots a Choropleth map to identify Hotspots and Coldspots using Gi* statistics.

    Args:
        Municipios (pd.Series or list of str): A series or list containing the names of the municipalities.
        gi (pd.Series or list of float): A series or list containing the Gi* Z-scores for each municipality.
        geojson (dict): A GeoJSON dictionary containing the geographical features of the municipalities.
        indices (pd.Series or list of str or int): A series or list containing the indices or IDs matching the 'locations' in the GeoJSON.

    Returns:
        go.Figure: A Plotly Figure object containing the Choropleth map.
        
    """
    
    hover = 'Estado: ' + Estados + '<br> Z-score: ' + gi.round(2).astype(str)

    fig = go.Figure()
    fig.add_trace(go.Choroplethmap(
        geojson=geojson,
        locations=indices,
        z=gi,
        marker_opacity=1,
        marker_line_width=0.5,
        text=hover,
        hoverinfo='text',
        colorscale=[[0, 'rgb(23, 28, 66)'], [0.5, 'lightgray'], [1, 'rgb(120, 0, 0)']],
        colorbar=dict(title="Categorias",
                      tickvals=[gi.min(), gi.median(), gi.max()],
                      ticktext=['Coldspot', 'Não significativo', 'Hotspot']))
    )
    
    fig.update_layout(
        title = "Identificação de Hot e Coldspots pela Gi*",
        map_zoom=5.4,
        map_center={"lat": -22.45, "lon": -48.63},
        map_style ='carto-positron',
    )
  
    return fig

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

def morans_i_altair(autocorr, morans_i_lag, geojson, variavel_interesse, variavel_interesse_lag):
    """
    Plota o gráfico de dispersão de Moran's I e o mapa LISA usando Altair.
    """
    # Preparar os dados
    source = autocorr.reset_index()

    # Encontrar valores mínimo e máximo para x e y
    min_val = min(source[variavel_interesse].min(), source[variavel_interesse_lag].min())
    max_val = max(source[variavel_interesse].max(), source[variavel_interesse_lag].max())

    # Gráfico de dispersão de Moran's I
    scatter = alt.Chart(source).mark_circle(size=60, color='rgba(23, 28, 66, 0.7)').encode(
        x=alt.X(f'{variavel_interesse}:Q', title=f'Valores Observados ({variavel_interesse})'),
        y=alt.Y(f'{variavel_interesse_lag}:Q', title=f'Lag Espacial ({variavel_interesse_lag})'),
        tooltip=[alt.Tooltip('state:N', title='Estado')]
    ).properties(
        width=400,
        height=400,
        title=f"Moran's I Scatter Plot: {morans_i_lag.I:.3f}, p-valor: {morans_i_lag.p_sim}"
    )

    # Adicionar linha x = y
    line = alt.Chart(pd.DataFrame({
        variavel_interesse: [min_val, max_val],
        variavel_interesse_lag: [min_val, max_val]
    })).mark_line(color='black', opacity=0.7).encode(
        x=alt.X(f'{variavel_interesse}:Q'),
        y=alt.Y(f'{variavel_interesse_lag}:Q')
    )

    # Combinar scatter plot e linha x = y
    scatter_plot = (scatter + line).interactive()

    # Preparar os dados do GeoJSON para Altair
    geojson_data = alt.Data(values=geojson['features'])

    # Definir esquema de cores para os quadrantes
    color_scale = alt.Scale(
        domain=['Not significant', 'HH', 'LL', 'LH', 'HL'],
        range=['lightgray', 'rgb(224, 30, 55)', 'rgb(23, 28, 66)', 'rgb(120, 14, 40)', 'rgb(72, 202, 228)']
    )

    # Ajustar a projeção e escala para o mapa LISA
    lisa_map = alt.Chart(geojson_data).mark_geoshape(
        stroke='black',
        strokeWidth=0.5
    ).encode(
        color=alt.Color('properties.quadrant:N', title='Quadrant', scale=color_scale, legend=alt.Legend(orient='bottom')),
        tooltip=[
            alt.Tooltip('properties.state:N', title='Estado'),
            alt.Tooltip('properties.quadrant:N', title='Quadrant')
        ]
    ).properties(
        width=400,
        height=400,
        title="LISA Cluster Map"
    ).project(
        type='mercator',
        center=[-95.7129, 37.0902],
        scale=500  # Ajuste a escala conforme necessário
    ).configure_view(
        stroke=None  # Remove a borda ao redor do mapa
    ).interactive()

    # Concatenar os gráficos
    final_chart = alt.hconcat(scatter_plot, lisa_map).resolve_scale(color='independent')

    return final_chart

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

def line_plot_with_dropdown(df, date_col, value_col, category_cols):
    """
    Cria um line plot de 'value_col' ao longo de 'date_col', com um dropdown para selecionar a variável categórica de agrupamento.

    Args:
        df (pd.DataFrame): DataFrame com os dados.
        date_col (str): Nome da coluna de datas (e.g., 'transaction_dt').
        value_col (str): Nome da coluna de valores (e.g., 'transaction_amt').
        category_cols (list of str): Lista das colunas categóricas para selecionar ('transaction_pgi', 'transaction_tp', 'entity_tp').

    Returns:
        alt.Chart: Gráfico Altair com o line plot e o dropdown.
    """

    # Converter a coluna de data para datetime se necessário
    if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
        df[date_col] = pd.to_datetime(df[date_col])

    # Criar uma seleção para a coluna categórica
    category_dropdown = alt.binding_select(options=category_cols, name='Agrupar por ')
    category_selection = alt.selection_single(fields=['category_col'], bind=category_dropdown, init={'category_col': category_cols[0]})

    # Transformar os dados para Altair
    base = alt.Chart(df).transform_fold(
        category_cols,
        as_=['category_col', 'category_value']
    ).transform_filter(
        category_selection
    )

    # Agregar os dados por data e categoria_value
    aggregated = base.transform_aggregate(
        total_value=f'sum({value_col})',
        groupby=[date_col, 'category_value']
    )

    # Criar o gráfico de linha
    line_chart = aggregated.mark_line().encode(
        x=alt.X(f'{date_col}:T', title='Data'),
        y=alt.Y('total_value:Q', title='Valor Total'),
        color=alt.Color('category_value:N', title='Categoria'),
        tooltip=[
            alt.Tooltip('category_value:N', title='Categoria'),
            alt.Tooltip('total_value:Q', title='Valor Total', format=',.2f'),
            alt.Tooltip(f'{date_col}:T', title='Data', format='%Y-%m-%d')
        ]
    ).add_selection(
        category_selection
    ).properties(
        width=800,
        height=400,
        title='Transaction Amount over Time by Category'
    ).interactive()

    return line_chart
