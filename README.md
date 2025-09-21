# API Chart Generator

A minimal Streamlit application for generating interactive charts using a custom API endpoint.

## Quick Start

### Windows Users
Simply double-click `run_ui.bat` - it will automatically:
- Check Python installation
- Install missing dependencies
- Validate configuration
- Launch the Streamlit UI

### Manual Setup

1. Configure your API endpoint in `.env`:
```env
API_URL=https://your-api-endpoint.com
TEMPERATURE=0.1
TOP_K=0.1
MAX_TOKENS=2048
OUTPUT_DIR=outputs
HTML_TEMPLATE_DIR=templates
DEBUG=false
VERBOSE=true
```

2. Install dependencies (if not using the launcher):
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
# Using the Python launcher (recommended)
python run_ui.py

# Or directly with Streamlit
streamlit run streamlit_app.py
```

## API Payload Structure

The application sends POST requests with this payload structure:
```json
{
  "PROJECT": "Chart Generator",
  "CONTEXT": "Generate interactive chart data based on user request",
  "INJECTION": {
    "INPUT": "enhanced_user_prompt"
  },
  "injection": {
    "temperature": "0.1",
    "topk": "0.1", 
    "token": "2048"
  }
}
```

## Features

- 🤖 **AI-Powered Chart Generation** - Uses your custom API endpoint
- 📊 **Multiple Chart Types** - Bar, Line, Pie, and Scatter plots
- 🎨 **Interactive Charts** - Built with Plotly for rich interactivity
- 💾 **Export Options** - Save as HTML files, download, or open in browser
- 🔧 **Easy Configuration** - Simple `.env` file setup
- 🚀 **One-Click Launch** - Automated setup and launch with batch file

## File Structure

```
api_chat_bot_py/
├── run_ui.bat             # Windows launcher (double-click to start)
├── run_ui.py              # Python launcher with dependency management
├── streamlit_app.py       # Main Streamlit UI
├── api_client.py          # API client for POST requests
├── config.py              # Configuration management
├── graph_generator.py     # Chart generation using Plotly
├── html_generator.py      # HTML file generation
├── requirements.txt       # Python dependencies
├── .env                   # Configuration file
├── templates/             # HTML templates
│   └── chart_template.html
└── outputs/               # Generated chart files
```

## Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `API_URL` | Your API endpoint URL | Required |
| `TEMPERATURE` | AI temperature setting | 0.1 |
| `TOP_K` | Top-K sampling parameter | 0.1 |
| `MAX_TOKENS` | Maximum response tokens | 2048 |
| `OUTPUT_DIR` | Chart output directory | outputs |
| `HTML_TEMPLATE_DIR` | Template directory | templates |
| `DEBUG` | Enable debug mode | false |
| `VERBOSE` | Enable verbose logging | true |
