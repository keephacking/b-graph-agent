"""
Graph Generator for Simple Terminal App
Converts structured data into interactive Plotly charts.
"""

import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, List, Optional
import pandas as pd
from config import get_config


class GraphGenerator:
    """Generates interactive charts using Plotly"""
    
    def __init__(self):
        """Initialize the graph generator"""
        self.config = get_config()
        self.color_schemes = {
            'viridis': px.colors.sequential.Viridis,
            'plotly': px.colors.qualitative.Plotly,
            'blues': px.colors.sequential.Blues,
            'reds': px.colors.sequential.Reds,
            'greens': px.colors.sequential.Greens,
            'set1': px.colors.qualitative.Set1,
            'pastel': px.colors.qualitative.Pastel,
        }
        
        if self.config.verbose:
            print("✅ Graph generator initialized")
    
    def create_chart(self, data: Dict[str, Any]) -> go.Figure:
        """
        Create a chart based on structured data
        
        Args:
            data: Dictionary containing chart data and configuration
            
        Returns:
            Plotly Figure object
        """
        chart_type = (data.get('chart_type') or 'bar').lower()
        
        # Route to appropriate chart creation method
        if chart_type == 'bar':
            return self._create_bar_chart(data)
        elif chart_type == 'line':
            return self._create_line_chart(data)
        elif chart_type == 'pie':
            return self._create_pie_chart(data)
        elif chart_type == 'scatter':
            return self._create_scatter_chart(data)
        else:
            if self.config.verbose:
                print(f"⚠️ Unknown chart type '{chart_type}', defaulting to bar chart")
            return self._create_bar_chart(data)
    
    def _create_bar_chart(self, data: Dict[str, Any]) -> go.Figure:
        """Create a bar chart"""
        
        chart_data = data['data']
        labels = chart_data['labels']
        datasets = chart_data['datasets']
        config_data = data.get('chart_config', {})
        
        fig = go.Figure()
        
        # Get colors
        colors = self._get_colors(config_data.get('color_scheme', 'plotly'), len(datasets))
        
        # Add bars for each dataset
        for i, dataset in enumerate(datasets):
            fig.add_trace(go.Bar(
                name=dataset['name'],
                x=labels,
                y=dataset['values'],
                marker_color=colors[i % len(colors)]
            ))
        
        # Update layout
        fig.update_layout(
            title=data.get('title', 'Bar Chart'),
            xaxis_title=config_data.get('x_axis_title', 'Categories'),
            yaxis_title=config_data.get('y_axis_title', 'Values'),
            showlegend=config_data.get('show_legend', len(datasets) > 1),
            template='plotly_white',
            hovermode='x unified'
        )
        
        return fig
    
    def _create_line_chart(self, data: Dict[str, Any]) -> go.Figure:
        """Create a line chart"""
        
        chart_data = data['data']
        labels = chart_data['labels']
        datasets = chart_data['datasets']
        config_data = data.get('chart_config', {})
        
        fig = go.Figure()
        
        # Get colors
        colors = self._get_colors(config_data.get('color_scheme', 'plotly'), len(datasets))
        
        # Add lines for each dataset
        for i, dataset in enumerate(datasets):
            fig.add_trace(go.Scatter(
                name=dataset['name'],
                x=labels,
                y=dataset['values'],
                mode='lines+markers',
                line=dict(color=colors[i % len(colors)], width=3),
                marker=dict(size=8)
            ))
        
        # Update layout
        fig.update_layout(
            title=data.get('title', 'Line Chart'),
            xaxis_title=config_data.get('x_axis_title', 'X-axis'),
            yaxis_title=config_data.get('y_axis_title', 'Y-axis'),
            showlegend=config_data.get('show_legend', len(datasets) > 1),
            template='plotly_white',
            hovermode='x unified'
        )
        
        return fig
    
    def _create_pie_chart(self, data: Dict[str, Any]) -> go.Figure:
        """Create a pie chart"""
        
        chart_data = data['data']
        labels = chart_data['labels']
        
        # For pie charts, use the first dataset
        dataset = chart_data['datasets'][0]
        values = dataset['values']
        config_data = data.get('chart_config', {})
        
        # Get colors
        colors = self._get_colors(config_data.get('color_scheme', 'plotly'), len(labels))
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.3,  # Create a donut chart
            marker_colors=colors
        )])
        
        # Update layout
        fig.update_layout(
            title=data.get('title', 'Pie Chart'),
            template='plotly_white',
            showlegend=config_data.get('show_legend', True)
        )
        
        return fig
    
    def _create_scatter_chart(self, data: Dict[str, Any]) -> go.Figure:
        """Create a scatter plot"""
        
        chart_data = data['data']
        labels = chart_data['labels']
        datasets = chart_data['datasets']
        config_data = data.get('chart_config', {})
        
        fig = go.Figure()
        
        # Get colors
        colors = self._get_colors(config_data.get('color_scheme', 'plotly'), len(datasets))
        
        # For scatter plots, we need at least 2 datasets (x and y)
        if len(datasets) >= 2:
            x_data = datasets[0]['values']
            y_data = datasets[1]['values']
            
            fig.add_trace(go.Scatter(
                x=x_data,
                y=y_data,
                mode='markers',
                marker=dict(
                    size=12,
                    color=colors[0],
                    opacity=0.7
                ),
                text=labels,
                hovertemplate='<b>%{text}</b><br>X: %{x}<br>Y: %{y}<extra></extra>'
            ))
        else:
            # Fallback: create scatter with indices as x
            dataset = datasets[0]
            fig.add_trace(go.Scatter(
                x=list(range(len(dataset['values']))),
                y=dataset['values'],
                mode='markers',
                marker=dict(
                    size=12,
                    color=colors[0],
                    opacity=0.7
                ),
                text=labels,
                hovertemplate='<b>%{text}</b><br>Index: %{x}<br>Value: %{y}<extra></extra>'
            ))
        
        # Update layout
        fig.update_layout(
            title=data.get('title', 'Scatter Plot'),
            xaxis_title=config_data.get('x_axis_title', 'X Values'),
            yaxis_title=config_data.get('y_axis_title', 'Y Values'),
            template='plotly_white',
            showlegend=False
        )
        
        return fig
    
    def _get_colors(self, color_scheme: str, count: int) -> List[str]:
        """Get color palette for charts"""
        
        scheme = color_scheme.lower()
        if scheme in self.color_schemes:
            colors = self.color_schemes[scheme]
        else:
            colors = self.color_schemes['plotly']
        
        # Ensure we have enough colors
        while len(colors) < count:
            colors.extend(colors)
        
        return colors[:count]
    
    def add_annotations(self, fig: go.Figure, annotations: List[Dict[str, Any]]) -> go.Figure:
        """Add annotations to the chart"""
        
        for annotation in annotations:
            fig.add_annotation(
                x=annotation.get('x', 0),
                y=annotation.get('y', 0),
                text=annotation.get('text', ''),
                showarrow=annotation.get('show_arrow', True),
                arrowhead=annotation.get('arrow_head', 2),
                arrowsize=annotation.get('arrow_size', 1),
                arrowwidth=annotation.get('arrow_width', 2),
                arrowcolor=annotation.get('arrow_color', '#636363')
            )
        
        return fig
    
    def customize_layout(self, fig: go.Figure, customizations: Dict[str, Any]) -> go.Figure:
        """Apply custom layout settings"""
        
        layout_updates = {}
        
        # Font settings
        if 'font_family' in customizations:
            layout_updates['font_family'] = customizations['font_family']
        
        if 'font_size' in customizations:
            layout_updates['font_size'] = customizations['font_size']
        
        # Background colors
        if 'background_color' in customizations:
            layout_updates['paper_bgcolor'] = customizations['background_color']
        
        if 'plot_background_color' in customizations:
            layout_updates['plot_bgcolor'] = customizations['plot_background_color']
        
        # Margins
        if 'margins' in customizations:
            margins = customizations['margins']
            layout_updates['margin'] = dict(
                l=margins.get('left', 50),
                r=margins.get('right', 50),
                t=margins.get('top', 50),
                b=margins.get('bottom', 50)
            )
        
        # Apply updates
        if layout_updates:
            fig.update_layout(**layout_updates)
        
        return fig
    
    def export_config(self) -> Dict[str, Any]:
        """Export Plotly configuration for HTML embedding"""
        
        return {
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': ['pan2d', 'lasso2d'],
            'toImageButtonOptions': {
                'format': 'png',
                'filename': 'chart',
                'height': 600,
                'width': 800,
                'scale': 1
            },
            'responsive': True
        }


def create_sample_chart() -> go.Figure:
    """Create a sample chart for testing"""
    
    generator = GraphGenerator()
    
    sample_data = {
        'title': 'Sample Monthly Sales',
        'description': 'Sample data for testing',
        'chart_type': 'bar',
        'data': {
            'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            'datasets': [{
                'name': 'Sales',
                'values': [120, 190, 300, 500, 200, 300]
            }]
        },
        'chart_config': {
            'x_axis_title': 'Month',
            'y_axis_title': 'Sales ($)',
            'color_scheme': 'viridis',
            'show_legend': True
        }
    }
    
    return generator.create_chart(sample_data)


def test_all_chart_types():
    """Test all supported chart types"""
    
    print("🧪 Testing all chart types...")
    
    generator = GraphGenerator()
    
    # Test data
    test_data = {
        'labels': ['A', 'B', 'C', 'D', 'E'],
        'datasets': [
            {'name': 'Series 1', 'values': [10, 20, 15, 25, 30]},
            {'name': 'Series 2', 'values': [15, 25, 20, 30, 35]}
        ]
    }
    
    chart_types = ['bar', 'line', 'pie', 'scatter']
    
    for chart_type in chart_types:
        try:
            data = {
                'title': f'Test {chart_type.title()} Chart',
                'chart_type': chart_type,
                'data': test_data,
                'chart_config': {
                    'x_axis_title': 'Categories',
                    'y_axis_title': 'Values',
                    'color_scheme': 'plotly'
                }
            }
            
            fig = generator.create_chart(data)
            print(f"✅ {chart_type.title()} chart created successfully")
            
        except Exception as e:
            print(f"❌ Error creating {chart_type} chart: {str(e)}")
    
    print("🎯 Chart type testing completed!")


if __name__ == "__main__":
    test_all_chart_types()
