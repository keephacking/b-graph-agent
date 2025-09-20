"""
HTML Generator for Simple Terminal App
Creates HTML files with embedded interactive Plotly charts.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import plotly.graph_objects as go
import plotly.io as pio
from jinja2 import Environment, FileSystemLoader, Template
from config import get_config


class HTMLGenerator:
    """Generates HTML files with embedded Plotly charts"""
    
    def __init__(self):
        """Initialize the HTML generator"""
        self.config = get_config()
        self.template_dir = self.config.template_dir
        self.output_dir = self.config.output_dir
        
        # Ensure directories exist
        try:
            self.template_dir.mkdir(exist_ok=True)
            self.output_dir.mkdir(exist_ok=True)
        except (OSError, PermissionError) as e:
            if self.config.verbose:
                print(f"⚠️ Warning: Could not create directories: {e}")
        
        # Initialize Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True
        )
        
        if self.config.verbose:
            print("✅ HTML generator initialized")
    
    def generate_html(self, 
                     figure: go.Figure, 
                     data: Dict[str, Any], 
                     output_filename: Optional[str] = None) -> str:
        """
        Generate HTML file with embedded Plotly chart
        
        Args:
            figure: Plotly figure object
            data: Original data dictionary from Gemini
            output_filename: Optional custom filename
            
        Returns:
            Path to generated HTML file
        """
        
        # Generate filename if not provided
        if not output_filename:
            title = data.get('title', 'chart').lower()
            # Clean title for filename
            clean_title = ''.join(c if c.isalnum() or c in '-_' else '_' for c in title)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{clean_title}_{timestamp}.html"
        
        # Ensure .html extension
        if not output_filename.endswith('.html'):
            output_filename += '.html'
        
        output_path = self.output_dir / output_filename
        
        try:
            # Prepare template data
            template_data = self._prepare_template_data(figure, data)
            
            # Load and render template
            template = self._load_template()
            html_content = template.render(**template_data)
            
            # Write HTML file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            if self.config.verbose:
                print(f"✅ HTML file generated: {output_path}")
            
            return str(output_path)
            
        except Exception as e:
            if self.config.debug:
                print(f"❌ Error generating HTML: {str(e)}")
            raise Exception(f"Failed to generate HTML file: {str(e)}")
    
    def _prepare_template_data(self, figure: go.Figure, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for template rendering"""
        
        # Convert Plotly figure to JSON
        chart_json = figure.to_json()
        
        # Plotly configuration
        plotly_config = {
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d'],
            'toImageButtonOptions': {
                'format': 'png',
                'filename': data.get('title', 'chart').lower().replace(' ', '_'),
                'height': 600,
                'width': 800,
                'scale': 2
            },
            'responsive': True
        }
        
        # Calculate data points
        data_points = 0
        chart_data = data.get('data', {})
        if 'datasets' in chart_data:
            for dataset in chart_data['datasets']:
                data_points += len(dataset.get('values', []))
        
        # Prepare template variables
        template_data = {
            'title': data.get('title', 'Generated Chart'),
            'description': data.get('description', ''),
            'chart_type': data.get('chart_type', 'unknown'),
            'chart_json': chart_json,
            'plotly_config': json.dumps(plotly_config),
            'data_points': data_points,
            'generation_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'model_used': data.get('model_used', 'Gemini'),
            'original_prompt': data.get('original_prompt', '')
        }
        
        return template_data
    
    def _load_template(self) -> Template:
        """Load HTML template"""
        
        template_path = self.template_dir / 'chart_template.html'
        
        if template_path.exists():
            # Load custom template
            return self.jinja_env.get_template('chart_template.html')
        else:
            # Use default template
            return Template(self._get_default_template())
    
    def _get_default_template(self) -> str:
        """Get default HTML template if custom template not found"""
        
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <script src="https://cdn.plot.ly/plotly-2.26.0.min.js"></script>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 20px; 
            background-color: #f5f5f5; 
        }
        .container { 
            max-width: 1200px; 
            margin: 0 auto; 
            background: white; 
            padding: 20px; 
            border-radius: 8px; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
        }
        h1 { 
            color: #333; 
            text-align: center; 
            margin-bottom: 10px; 
        }
        .description { 
            text-align: center; 
            color: #666; 
            margin-bottom: 30px; 
        }
        .metadata { 
            margin-top: 30px; 
            padding: 15px; 
            background-color: #f8f9fa; 
            border-radius: 5px; 
        }
        .metadata h3 { 
            margin-top: 0; 
        }
        .metadata p { 
            margin: 5px 0; 
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>{{ title }}</h1>
        {% if description %}
        <div class="description">{{ description }}</div>
        {% endif %}
        
        <div id="chart" style="width:100%; height:500px;"></div>
        
        <div class="metadata">
            <h3>Chart Information</h3>
            <p><strong>Type:</strong> {{ chart_type|title }}</p>
            <p><strong>Data Points:</strong> {{ data_points }}</p>
            <p><strong>Generated:</strong> {{ generation_time }}</p>
            <p><strong>Model:</strong> {{ model_used }}</p>
            {% if original_prompt %}
            <p><strong>Original Prompt:</strong> "{{ original_prompt }}"</p>
            {% endif %}
        </div>
    </div>

    <script>
        const chartData = {{ chart_json|safe }};
        const config = {{ plotly_config|safe }};
        
        Plotly.newPlot('chart', chartData.data, chartData.layout, config);
        
        window.addEventListener('resize', function() {
            Plotly.Plots.resize('chart');
        });
    </script>
</body>
</html>
        """
    
    def create_template_file(self) -> None:
        """Create the default template file if it doesn't exist"""
        
        template_path = self.template_dir / 'chart_template.html'
        
        if not template_path.exists():
            # The template content is already written in the previous step
            if self.config.verbose:
                print(f"✅ Template file should be created at: {template_path}")
    
    def generate_static_html(self, 
                           figure: go.Figure, 
                           data: Dict[str, Any], 
                           output_filename: Optional[str] = None) -> str:
        """
        Generate static HTML (no external dependencies)
        
        Args:
            figure: Plotly figure object
            data: Original data dictionary
            output_filename: Optional custom filename
            
        Returns:
            Path to generated HTML file
        """
        
        # Generate filename if not provided
        if not output_filename:
            title = data.get('title', 'chart').lower()
            clean_title = ''.join(c if c.isalnum() or c in '-_' else '_' for c in title)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{clean_title}_static_{timestamp}.html"
        
        if not output_filename.endswith('.html'):
            output_filename += '.html'
        
        output_path = self.output_dir / output_filename
        
        try:
            # Generate static HTML with embedded Plotly
            html_content = pio.to_html(
                figure,
                config={
                    'displayModeBar': True,
                    'displaylogo': False,
                    'responsive': True
                },
                include_plotlyjs=True,  # Embed Plotly.js
                div_id="chart"
            )
            
            # Wrap in a complete HTML document
            full_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{data.get('title', 'Generated Chart')}</title>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ text-align: center; margin-bottom: 20px; }}
        .metadata {{ margin-top: 20px; padding: 15px; background-color: #f5f5f5; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{data.get('title', 'Generated Chart')}</h1>
        <p>{data.get('description', '')}</p>
    </div>
    
    {html_content}
    
    <div class="metadata">
        <h3>Chart Information</h3>
        <p><strong>Type:</strong> {data.get('chart_type', 'unknown').title()}</p>
        <p><strong>Generated:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        <p><strong>Model:</strong> {data.get('model_used', 'Gemini')}</p>
        {f'<p><strong>Original Prompt:</strong> "{data.get("original_prompt", "")}"</p>' if data.get('original_prompt') else ''}
    </div>
</body>
</html>
            """
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(full_html)
            
            if self.config.verbose:
                print(f"✅ Static HTML file generated: {output_path}")
            
            return str(output_path)
            
        except Exception as e:
            if self.config.debug:
                print(f"❌ Error generating static HTML: {str(e)}")
            raise Exception(f"Failed to generate static HTML file: {str(e)}")
    
    def list_output_files(self) -> list:
        """List all generated HTML files"""
        
        html_files = list(self.output_dir.glob('*.html'))
        return [str(f) for f in html_files]
    
    def clean_output_directory(self) -> int:
        """Clean old HTML files from output directory"""
        
        html_files = list(self.output_dir.glob('*.html'))
        count = 0
        
        for file_path in html_files:
            try:
                file_path.unlink()
                count += 1
            except Exception as e:
                if self.config.debug:
                    print(f"❌ Error deleting {file_path}: {str(e)}")
        
        if self.config.verbose and count > 0:
            print(f"🗑️ Cleaned {count} HTML files from output directory")
        
        return count


def test_html_generator():
    """Test the HTML generator"""
    
    print("🧪 Testing HTML Generator...")
    
    try:
        from graph_generator import create_sample_chart
        
        # Create generator and sample chart
        generator = HTMLGenerator()
        figure = create_sample_chart()
        
        # Sample data
        sample_data = {
            'title': 'Test Chart Generation',
            'description': 'This is a test chart for HTML generation',
            'chart_type': 'bar',
            'original_prompt': 'Create a test chart',
            'model_used': 'gemini-2.0-flash-exp'
        }
        
        # Generate HTML
        output_path = generator.generate_html(figure, sample_data, 'test_chart.html')
        
        print(f"✅ HTML generated successfully: {output_path}")
        print(f"📁 Output directory: {generator.output_dir}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False


if __name__ == "__main__":
    test_html_generator()
