import plotly.express as px
import plotly.graph_objects as go

def gerar_grafico2(sensor, hora_data, nome_sensor):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=hora_data,
        y=sensor,
        mode='lines+markers',
        name=nome_sensor,
        marker=dict(size=3, color='red')
    ))
    fig.update_layout(title="Variação de +" + nome_sensor,
                      xaxis_title="Horário",
                      yaxis_title=nome_sensor)
    return fig.to_html()


def gerar_grafico(sensor, hora_data, nome_sensor):

    fig = px.line(
        x=hora_data,
        y=sensor,
        title=nome_sensor,
        labels={'x': 'Horário', 'y': nome_sensor}
    )

    fig.update_layout(
        title=None,
        margin=dict(t=15)
    )
    fig.update_layout(
        legend=dict(
            title=None, orientation="h", y=1, yanchor="bottom", x=0.5, xanchor="center"
        )
    )

    return fig.to_html()
