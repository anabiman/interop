import ray
import streamlit


@streamlit.cache_data
def get_resources():
    ray.init()
    available_resources = ray.available_resources()
    ray.shutdown()
    return available_resources


