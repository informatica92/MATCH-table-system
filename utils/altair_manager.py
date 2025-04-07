import altair as alt
import pandas as pd


def timeline_chart(df: pd.DataFrame):
    """
    Creates a timeline chart using Altair to visualize the data in the given DataFrame.

    Args:
        df (pd.DataFrame): The DataFrame containing the data to be visualized.

    Returns:
        alt.Chart: The Altair chart object representing the timeline chart.
    """
    # Create the timeline chart
    # Create the Altair chart
    # # Handle user selection based on Altair interaction (using nearest or selection)
    selection = alt.selection_point(
        fields=['table_id'],
        # on='mouseover',
        # empty='none',
        # clear='mouseout'
    )

    chart = alt.Chart(df).mark_bar(
        cornerRadius=5,
        strokeWidth=1.5
    ).encode(
        y=alt.Y(
            'start_datetime:T',
            title="date time",
            axis=alt.Axis(format='%Y-%m-%d %H:%M', labelLimit=600, labelColor='#999999'),
            scale=alt.Scale(reverse=True)
        ),
        y2='end_datetime:T',
        x=alt.X(
            'game_name:N',
            title=None,
            axis=alt.Axis(labelLimit=600, labelColor='#999999'),
            sort="y"
        ),
        color=alt.Color(
            'status:N',
            scale=alt.Scale(domain=['Full', 'Available'], range=['#FF5733', '#DAF7A6']),
            legend=alt.Legend(orient="top", direction="horizontal")
        ),
        tooltip=['game_name:N', 'proposed_by_username:N', 'max_players:Q', 'joined_count:Q', 'duration:Q'],
        stroke=alt.Stroke(
            'status:N',
            scale=alt.Scale(domain=['Full', 'Available'], range=['darkred', 'darkgreen'])
        )
    ).properties(
        # width=500,
        height=700
    ).add_params(
        selection
    ).encode(
        opacity=alt.condition(selection, alt.value(1), alt.value(0.1))
    ).configure_view(
        strokeWidth=0
    ).configure_axis(
        domain=False
    )

    return chart
