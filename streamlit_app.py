import io
import re

import pandas as pd
import streamlit as st

GITHUB_URL = "https://github.com/LudwigStumpp/llm-leaderboard"


def extract_table_and_format_from_markdown_text(markdown_table: str) -> pd.DataFrame:
    """Extracts a table from a markdown text and formats it as a pandas DataFrame.

    Args:
        text (str): Markdown text containing a table.

    Returns:
        pd.DataFrame: Table as pandas DataFrame.
    """
    df = (
        pd.read_table(io.StringIO(markdown_table), sep="|", header=0, index_col=1)
        .dropna(axis=1, how="all")  # drop empty columns
        .iloc[1:]  # drop first row which is the "----" separator of the original markdown table
        .sort_index(ascending=True)
        .apply(lambda x: x.str.strip() if x.dtype == "object" else x)
        .replace("", float("NaN"))
        .astype(float, errors="ignore")
    )

    # remove whitespace from column names and index
    df.columns = df.columns.str.strip()
    df.index = df.index.str.strip()
    df.index.name = df.index.name.strip()

    return df


def extract_markdown_table_from_multiline(multiline: str, table_headline: str, next_headline_start: str = "#") -> str:
    """Extracts the markdown table from a multiline string.

    Args:
        multiline (str): content of README.md file.
        table_headline (str): Headline of the table in the README.md file.
        next_headline_start (str, optional): Start of the next headline. Defaults to "#".

    Returns:
        str: Markdown table.

    Raises:
        ValueError: If the table could not be found.
    """
    # extract everything between the table headline and the next headline
    table = []
    start = False
    for line in multiline.split("\n"):
        if line.startswith(table_headline):
            start = True
        elif line.startswith(next_headline_start):
            start = False
        elif start:
            table.append(line + "\n")

    if len(table) == 0:
        raise ValueError(f"Could not find table with headline '{table_headline}'")

    return "".join(table)


def remove_markdown_links(text: str) -> str:
    """Modifies a markdown text to remove all markdown links.
    Example: [DISPLAY](LINK) to DISPLAY
    First find all markdown links with regex.
    Then replace them with: $1
    Args:
        text (str): Markdown text containing markdown links
    Returns:
        str: Markdown text without markdown links.
    """

    # find all markdown links
    markdown_links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", text)

    # remove link keep display text
    for display, link in markdown_links:
        text = text.replace(f"[{display}]({link})", display)

    return text


def filter_dataframe(df: pd.DataFrame, ignore_columns: list[str] | None = None) -> pd.DataFrame:
    """
    Adds a UI on top of a dataframe to let viewers filter columns

    Modified from https://blog.streamlit.io/auto-generate-a-dataframe-filtering-ui-in-streamlit-with-filter_dataframe/

    Args:
        df (pd.DataFrame): Original dataframe
        ignore_columns (list[str], optional): Columns to ignore. Defaults to None.

    Returns:
        pd.DataFrame: Filtered dataframe
    """
    modify = st.checkbox("Add filters")

    if not modify:
        return df

    df = df.copy()

    if ignore_columns is None:
        ignore_columns = []

    modification_container = st.container()

    with modification_container:
        to_filter_index = st.multiselect("Filter by model:", df.index)
        if to_filter_index:
            df = pd.DataFrame(df.loc[to_filter_index])

        to_filter_columns = st.multiselect("Filter by benchmark:", [c for c in df.columns if c not in ignore_columns])
        if to_filter_columns:
            df = pd.DataFrame(df[ignore_columns + to_filter_columns])

    return df


def setup_basic():
    title = "🏆 LLM-Leaderboard"

    st.set_page_config(
        page_title=title,
        page_icon="🏆",
        layout="wide",
    )
    st.title(title)

    st.markdown(
        "A joint community effort to create one central leaderboard for LLMs."
        f" Visit [llm-leaderboard]({GITHUB_URL}) to contribute.",
    )


def setup_leaderboard(readme: str):
    leaderboard_table = extract_markdown_table_from_multiline(readme, table_headline="## Leaderboard")
    leaderboard_table = remove_markdown_links(leaderboard_table)
    df_leaderboard = extract_table_and_format_from_markdown_text(leaderboard_table)
    df_leaderboard["Commercial Use?"] = df_leaderboard["Commercial Use?"].map({"yes": 1, "no": 0}).astype(bool)

    st.markdown("## Leaderboard")
    st.dataframe(filter_dataframe(df_leaderboard, ignore_columns=["Commercial Use?"]))


def setup_benchmarks(readme: str):
    benchmarks_table = extract_markdown_table_from_multiline(readme, table_headline="## Benchmarks")
    df_benchmarks = extract_table_and_format_from_markdown_text(benchmarks_table)

    st.markdown("## Covered Benchmarks")

    selected_benchmark = st.selectbox("Select a benchmark to learn more:", df_benchmarks.index.unique())
    df_selected = df_benchmarks.loc[selected_benchmark]
    text = [
        f"Name: {selected_benchmark}",
    ]
    for key in df_selected.keys():
        text.append(f"{key}: {df_selected[key]} ")
    st.markdown("  \n".join(text))


def setup_sources():
    st.markdown("## Sources")
    st.markdown(
        "The results of this leaderboard are collected from the individual papers and published results of the model "
        "authors. If you are interested in the sources of each individual reported model value, please visit the "
        f"[llm-leaderboard]({GITHUB_URL}) repository."
    )
    st.markdown(
        """
    Special thanks to the following pages:
    - [MosaicML - Model benchmarks](https://www.mosaicml.com/blog/mpt-7b)
    - [lmsys.org - Chatbot Arena benchmarks](https://lmsys.org/blog/2023-05-03-arena/)
    - [Papers With Code](https://paperswithcode.com/)
    - [Stanford HELM](https://crfm.stanford.edu/helm/latest/)
    """
    )


def setup_disclaimer():
    st.markdown("## Disclaimer")
    st.markdown(
        "Above information may be wrong. If you want to use a published model for commercial use, please contact a "
        "lawyer."
    )


def setup_footer():
    st.markdown(
        """
        ---
        Made with ❤️ by the awesome open-source community from all over 🌍.
        """
    )


def main():
    setup_basic()

    with open("README.md", "r") as f:
        readme = f.read()

    setup_leaderboard(readme)
    setup_benchmarks(readme)
    setup_sources()
    setup_disclaimer()
    setup_footer()


if __name__ == "__main__":
    main()
