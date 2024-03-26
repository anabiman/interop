import inspect
import textwrap

import streamlit
import toc
from meta import DEV_EMAIL, DEV_NAME

# from stpyvista import stpyvista
# from visualize import stpv_usage_example


def main():
    streamlit.title("Mathematical Model")
    #    stpyvista(stpv_usage_example())

    streamlit.write(r"""$\LaTeX$ is amazing!""")
    streamlit.latex(
        r"""
        a + ar + a r^2 + a r^3 + \cdots + a r^{n-1} =
        \sum_{k=0}^{n-1} ar^k =
        a \left(\frac{1-r^{n}}{1-r}\right)
        """
    )

    latext = r"""
    ## $\LaTeX$ example
    ### Full equation 
    $$ 
    \Delta G = \Delta\sigma \frac{a}{b} 
    $$ 
    ### Inline
    Assume $\frac{a}{b}=1$ and $\sigma=0$...  
    """
    streamlit.write(latext)
    streamlit.title("Table of contents")


if __name__ == "__main__":
    streamlit.set_page_config(
        page_title="Streamlit MDS App", page_icon=":chart_with_upwards_trend:"
    )
    main()

    toc_obj = toc.Toc()
    toc_obj.title("Table of Contents")
    toc_obj.header("Mathematical Model")
    toc_obj.subheader("Latex example")

    toc_obj.placeholder(sidebar=True)
    toc_obj.generate()

    with streamlit.sidebar:
        streamlit.markdown("---")
        streamlit.markdown(
            f'<h6>Made in &nbsp<img src="https://streamlit.io/images/brand/streamlit-mark-color.png" alt="Streamlit logo" height="16">&nbsp by <a href=mailto:{DEV_EMAIL} style="color:#BE541D;">@{DEV_NAME}</a></h6>',
            unsafe_allow_html=True,
        )
        streamlit.markdown(
            f'<h6>Generated by the MDS <a href="https://dev.azure.com/dcimds/MDS_Demo_Platform/_git/app-library-template" style="color:#BE541D;">app-library-template</a></h6>',
            unsafe_allow_html=True,
        )
