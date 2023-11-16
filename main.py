import dash
from dash import dcc, html, callback
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import numpy as np
import math



# Create a Dash app
app = dash.Dash(__name__)

# Sample data for demonstration
df = pd.read_csv('/Users/deianhrehorciuc/Documents/billionaire_project/Billionaires Statistics Dataset.csv')

# Count the number of people in each country
country_counts = df['country'].value_counts().reset_index()
country_counts.columns = ['country', 'Count']

#count how many status
status_df = df['status'].value_counts().reset_index()
status_df = status_df.drop([2, 3, 4, 5])

#count cumulative years
df_sorted = df.sort_values(by='birthYear').copy()
cumulative_years = df_sorted.groupby('birthYear').size().reset_index(name='count')
cumulative_years['cumulative_count'] = cumulative_years['count'].cumsum()

#age / count / gender
gender_age = df.groupby(['age', 'gender']).size().reset_index(name='count')

#correlation
df_correlation = df.groupby(['gdp_country', 'cpi_country', 'total_tax_rate_country']).size().reset_index(name='count')
#convert to integer the gdp
df_correlation['gdp_country'] = df_correlation['gdp_country'].replace('[$,]', '', regex=True).astype(int)


#filtered_df = gender_age[gender_age['gender'] == ['M']]
status_df['status'] = status_df['status'].str.replace('D', 'Self-made')
status_df['status'] = status_df['status'].str.replace('U', 'Inherited')
gender_count = df.groupby(['country', 'gender']).size().reset_index(name='count')
gender_count_pivot = gender_count.pivot(index='country', columns='gender', values='count')
gender_count_pivot.reset_index(inplace=True)
gender_count_pivot = gender_count_pivot.fillna(0)
gender_count_pivot['F_ratio'] = np.where(gender_count_pivot['M'] == 0, np.nan, np.round(gender_count_pivot['F'] / gender_count_pivot['M'] * 100, 2))
gender_count_pivot['M_ratio'] = np.where(gender_count_pivot['F'] == 0, np.nan, np.round(gender_count_pivot['M'] / gender_count_pivot['F'] * 100, 2))

population_countries = df[['country', 'population_country']].drop_duplicates()
merged_df = country_counts.merge(population_countries, on='country')
merged_df['population_country'].fillna(0, inplace=True)
merged_df['ratio'] = np.ceil((merged_df['Count'] / merged_df['population_country']) * 1000000)

industry_counts = df['industries'].value_counts().reset_index()

figure_nr = px.choropleth(
                    country_counts,
                    locations='country',
                    locationmode='country names',
                    color='Count',
                    color_continuous_scale='Viridis',  # You can choose a different color scale
                    title='Count of People by Country',
                    projection='natural earth',
                    width=1100, height=700)

map_distribution = px.choropleth(merged_df,
                                locations='country',
                                locationmode = 'country names',
                                color = 'ratio',
                                color_continuous_scale = 'Viridis',  # You can choose a different color scale
                                title = 'Count of Billionaires per Country',
                                projection='natural earth',
                                width=1100, height=700)

year_trending = px.line(cumulative_years, x='birthYear', y='cumulative_count', title='Billionaires over years')
#gdp_correlation = px.line(df_gdp, x='gdp_country', y='count', title='GDP country vs number of billionaires')

pie_industry = px.pie(industry_counts, values='count', names='industries', title='Industries')
status_pie = px.pie(status_df, values='count', names='status', title='Founders/Entrepreneurs vs. Inherited fortune')
# Define the app layout
app.layout = html.Div([
    dcc.Tabs([
        dcc.Tab(label='Number analysis', children=[
            dcc.Graph(figure=figure_nr)
        ]),
        dcc.Tab(label='Gender analysis', children=[
            dcc.Dropdown(
                id='variable-dropdown',
                options=[
                    {'label': 'Female Ratio', 'value': 'F_ratio'},
                    {'label': 'Male Ratio', 'value': 'M_ratio'}
                ],
                value='F_ratio'
            ),
            dcc.Graph(id='map_gender_ratio'),
        ]),
        dcc.Tab(label='Fortune source analysis', children=[
            dcc.Graph(figure=status_pie)
        ]),
        dcc.Tab(label='Industry analysis', children=[
            dcc.Graph(figure=pie_industry)
        ]),
        dcc.Tab(label='Year trending', children=[
            dcc.Graph(figure=year_trending)
        ]),
        dcc.Tab(label='Age histogram', children=[
            dcc.Checklist(
                id='radio-selector',
                options=[
                    {'label': 'Male', 'value': 'M'},
                    {'label': 'Female', 'value': 'F'}
                ],
                value=['M'],  # Default selection
                labelStyle={'display': 'block'}
            ),
            dcc.Graph(id='gender_histogram')
        ]),
        dcc.Tab(label='GDP Correlation', children=[
            dcc.RadioItems(
                id='radio-correlation',
                options=[
                    {'label': 'GDP', 'value': 'gdp_country'},
                    {'label': 'CPI', 'value': 'cpi_country'},
                    {'label': 'Tax rate', 'value': 'total_tax_rate_country'},
                ],
                value='gdp_country'
            ),
            dcc.Graph(id='graph_correlation')
        ]),
    ]),
])

# Define a callback to update the choropleth map
@callback(Output('map_gender_ratio', 'figure'),
                [Input('variable-dropdown', 'value')])
def update_choropleth(selected_variable):
    fig = px.choropleth(
        gender_count_pivot,
        locations='country',
        locationmode='country names',
        color=selected_variable,
        color_continuous_scale="Viridis",
        title=f"{selected_variable} by Country",
        projection='natural earth',
        width=1100, height=700,
    )

    return fig

@callback(Output('gender_histogram', 'figure'),
                [Input('radio-selector', 'value')]
          )
def update_histogram(selected_radio):
    filtered_df = gender_age[gender_age['gender'].isin(selected_radio)]
    fig_histogram = px.histogram(filtered_df, x='age', y='count', color='gender', barmode='overlay')

    return fig_histogram

@callback(Output('graph_correlation', 'figure'),
          [Input('radio-correlation', 'value')]
          )
def update_correlation(sel_correlation):
    filt_correlation = df_correlation[[sel_correlation, 'count']]
    fig_correlation = px.scatter(filt_correlation, x=sel_correlation, y='count', title=str(sel_correlation) + ' vs number of billionaires')

    return fig_correlation

if __name__ == '__main__':
    app.run_server(debug=True)
