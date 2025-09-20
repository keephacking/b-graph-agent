# API Chart Generator

A minimal Streamlit application for generating interactive charts using a custom API endpoint.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure your API endpoint in `.env`:
```
API_URL=your_api_endpoint_here
TEMPERATURE=0.1
TOP_K=0.1
MAX_TOKENS=2048
```

## Usage

Run the Streamlit application:
```bash
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

## Files

- `streamlit_app.py` - Main Streamlit UI
- `api_client.py` - API client for POST requests
- `config.py` - Configuration management
- `graph_generator.py` - Chart generation using Plotly
- `html_generator.py` - HTML file generation
- `templates/` - HTML templates
- `outputs/` - Generated chart files
