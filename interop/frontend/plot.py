import plotly.express as px
import streamlit as st


def get_demo_data1():
    df = px.data.gapminder()

    return px.scatter(
        df.query("year==2007"),
        x="gdpPercap",
        y="lifeExp",
        size="pop",
        color="continent",
        hover_name="country",
        log_x=True,
        size_max=60,
    )


def get_demo_data2():
    df = px.data.iris()

    return px.scatter(
        df,
        x="sepal_width",
        y="sepal_length",
        color="species",
    )


def demo_plot(nplots: int = 1):
    figs = [get_demo_data1, get_demo_data2]
    tabs = st.tabs([f"Sim{i} Result" for i in range(nplots)])
    for i, tab in enumerate(tabs):
        with tab:
            st.plotly_chart(figs[i](), theme="streamlit", use_container_width=True)
