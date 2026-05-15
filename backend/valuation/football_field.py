import plotly.graph_objects as go
from typing import Dict, Tuple, Any

def build_football_field(valuation_ranges: Dict[str, Tuple[float, float]], 
                         current_book_value: float, 
                         company_name: str) -> Dict[str, Any]:
    """
    Builds a horizontal football field valuation chart using Plotly.
    
    Args:
        valuation_ranges: Dict mapping methodologies to (low, high) Implied Equity Value tuples.
        current_book_value: The target company's current reported book value.
        company_name: Name of the target company.
        
    Returns:
        A Plotly figure represented as a JSON dictionary (can be returned directly by FastAPI).
    """
    
    methodologies = list(valuation_ranges.keys())
    lows = [valuation_ranges[m][0] for m in methodologies]
    highs = [valuation_ranges[m][1] for m in methodologies]
    
    # Calculate widths for the bars (high - low)
    widths = [high - low for low, high in zip(lows, highs)]
    
    # Curated vibrant colors for the dark theme
    colors = ['#00E5FF', '#2979FF', '#651FFF', '#D500F9']
    bar_colors = [colors[i % len(colors)] for i in range(len(methodologies))]

    fig = go.Figure()
    
    # Add the range bars
    fig.add_trace(go.Bar(
        x=widths,
        y=methodologies,
        base=lows,
        orientation='h',
        marker_color=bar_colors,
        text=[f"${low:,.0f}M - ${high:,.0f}M" for low, high in zip(lows, highs)],
        textposition='inside',
        insidetextanchor='middle',
        hoverinfo='y+text',
        name="Implied Range"
    ))
    
    # Add current book value vertical dashed line
    if current_book_value is not None:
        fig.add_vline(
            x=current_book_value, 
            line_width=3, 
            line_dash="dash", 
            line_color="#FF1744", # Vibrant Red
            annotation_text=f"Current Book Value: ${current_book_value:,.0f}M", 
            annotation_position="top right",
            annotation_font_color="white",
            layer="above"
        )
    
    # Layout and styling (Premium Dark Mode)
    fig.update_layout(
        title=dict(
            text=f"Valuation Football Field — {company_name}",
            font=dict(size=24, color='white', family="Inter, Arial, sans-serif")
        ),
        plot_bgcolor='#111827',  # Tailwind gray-900
        paper_bgcolor='#111827',
        font=dict(color='#E5E7EB', family="Inter, Arial, sans-serif"), # gray-200
        xaxis=dict(
            title="Implied Equity Value (Millions USD)",
            title_font=dict(color='#9CA3AF'), # gray-400
            tickfont=dict(color='#9CA3AF'),
            showgrid=True,
            gridcolor='#374151', # gray-700
            zeroline=False
        ),
        yaxis=dict(
            tickfont=dict(size=14, color='#F3F4F6', family="Inter, Arial, sans-serif"),
            autorange="reversed" # Makes methodologies read top-to-bottom
        ),
        margin=dict(l=20, r=40, t=80, b=40),
        showlegend=False
    )
    
    return fig.to_dict()
