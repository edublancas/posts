import requests
import streamlit as st
import pandas as pd


import lib


import plotly.express as px


def plot_results(df):
    # Create the scatter plot
    fig = px.scatter(
        df,
        x="cost",
        y="n_tokens",
        color="model",
        symbol="cleaner",
        hover_data=["model", "cleaner", "cost", "n_tokens"],
        labels={
            "cost": "Cost ($)",
            "n_tokens": "Number of Tokens",
            "model": "Model",
            "cleaner": "Cleaner",
        },
        title="Cost vs. Number of Tokens for Different Models and Cleaners",
    )

    # Customize the layout
    fig.update_layout(
        xaxis_type="log",
        yaxis_type="log",
        xaxis_title="Cost ($)",
        yaxis_title="Number of Tokens",
        legend_title="Model",
        font=dict(size=12),
        hoverlabel=dict(bgcolor="white", font_size=12),
        width=800,
        height=600,
    )

    # Add annotations for each point
    for i, row in df.iterrows():
        fig.add_annotation(
            x=row["cost"],
            y=row["n_tokens"],
            text=row["cleaner"],
            showarrow=False,
            yshift=10,
            font=dict(size=8),
        )

    # Customize hover information
    fig.update_traces(
        hovertemplate="<b>Model:</b> %{customdata[0]}<br>"
        + "<b>Cleaner:</b> %{customdata[1]}<br>"
        + "<b>Cost:</b> $%{x:.4f}<br>"
        + "<b>Tokens:</b> %{y:,}<extra></extra>"
    )

    # Add gridlines
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="LightGrey")
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="LightGrey")

    return fig


def display_results(url):
    response = requests.get(url)
    html_content = response.text

    results = {
        "model": [],
        "cleaner": [],
        "cost": [],
        "n_tokens": [],
    }

    for model in [lib.gpt4omini, lib.gpt4o, lib.gpt4o_2024_08_06]:
        for cleaner, cleaner_name in [
            (lib.minifier, "clean"),
            (lib.tag_remover, "unstructured"),
            (lib.markdown_converter, "markdown"),
            (lib.no_cleaner, "raw"),
        ]:
            cleaner.set_model_info(model)

            output = cleaner.clean(html_content)
            n_tokens = cleaner.count_tokens(output)
            cost = cleaner.compute_cost(n_tokens)

            results["model"].append(model.name)
            results["cleaner"].append(cleaner_name)
            results["cost"].append(cost)
            results["n_tokens"].append(n_tokens)
    df = pd.DataFrame(results)

    st.dataframe(
        df.style.format({"cost": "${:.3f}", "n_tokens": "{:,}"}),
        use_container_width=True,
    )

    # add another expander with the explanation of each pipeline
    with st.expander("See explanation"):
        st.write(
            """
**Cleaner**:

1. `raw`: HTML document without any processing
2. `clean`: excludes everything outside the `<body></body>` tags, removes all attributes from HTML tags (except `class`, `id`, and `data-testid`), replaces `class` and `id` with increasing numbers (1, 2, 3, etc.), cleans up whitespace, and replaces `<a>TEXT</a>` with `TEXT`
3. `unstructured`: completely removes all HTML and only keeps the text
4. `markdown`: converts the HTML into markdown
        """
        )

    fig = plot_results(df)
    st.plotly_chart(fig)


st.title("HTML pre-processing savings calculator")

st.write(
    """
This app calculates the savings from using GPT-4o when pre-processing HTML content.
"""
)

url = st.text_input(
    "Enter the URL to analyze", value="https://en.wikipedia.org/wiki/Mercury_Prize"
)

if st.button("Analyze"):
    if url:
        display_results(url)
    else:
        st.error("Please enter a URL.")


# Add a footer to the Streamlit app
st.markdown("---")  # Add a horizontal line for separation
st.markdown(
    """
    <div style="text-align: center; color: #888888; font-size: 1.0em;">
        Hosting sponsored by 
        <a href="https://ploomber.io/" target="_blank">Ploomber</a>
    </div>
    """,
    unsafe_allow_html=True,
)
