import streamlit
from meta import APP_NAME

streamlit.set_page_config(
    page_title=APP_NAME,
)

streamlit.write("# Hello World! 😊")

streamlit.sidebar.success("Select a demo above.")

streamlit.markdown(
    """
    MDS dev is framework built specifically for Modeling & Data Science projects.
    **👈 Select a demo from the sidebar** to see some examples of what you can with this framework!
    ### Main Components
    - Frontend dev framework: [streamlit](https://streamlit.io)
    - Compute framework: [ray](https://ray.io)
    - Template management: [cruft](https://cruft.github.io/cruft)
    ### See more complex demos
    - Use a neural net to [analyze the Udacity Self-driving Car Image
        Dataset](https://github.com/streamlit/demo-self-driving)
    - Explore a [New York City rideshare dataset](https://github.com/streamlit/demo-uber-nyc-pickups)
"""
)
