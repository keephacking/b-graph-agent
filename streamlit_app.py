"""
Streamlit Desktop UI for API Chart Bot Application
Provides a beautiful chat-based interface for generating interactive charts.
"""

import streamlit as st
import os
import time
from pathlib import Path
from datetime import datetime
import webbrowser
from typing import Optional

# Import our existing components
try:
    from config import get_config
    from api_client import APIClient
    from graph_generator import GraphGenerator
    from html_generator import HTMLGenerator
except ImportError as e:
    st.error(f"❌ Import Error: {str(e)}")
    st.info("💡 Make sure you're running from the correct directory and all dependencies are installed")
    st.code("pip install -r requirements.txt")
    st.stop()


class StreamlitChatApp:
    """Streamlit chat interface for the API chart generator"""
    
    def __init__(self):
        self.config = None
        self.api_client = None
        self.graph_generator = None
        self.html_generator = None
        self.initialized = False
    
    def initialize_components(self) -> bool:
        """Initialize all application components"""
        try:
            if not self.initialized:
                with st.spinner("🚀 Initializing API Chart Generator..."):
                    self.config = get_config()
                    
                    if not self.config.validate():
                        st.error("❌ Configuration validation failed. Please check your .env file.")
                        return False
                    
                    self.api_client = APIClient()
                    
                    # Test API connection
                    if not self.api_client.test_connection():
                        st.error("❌ Failed to connect to API. Please check your API URL.")
                        return False
                    
                    self.graph_generator = GraphGenerator()
                    self.html_generator = HTMLGenerator()
                    
                    self.initialized = True
                    st.success("✅ API Chart Generator ready!")
            
            return True
            
        except Exception as e:
            st.error(f"❌ Initialization failed: {str(e)}")
            st.info("💡 Make sure your .env file exists with a valid API_URL")
            return False
    
    def process_chart_request(self, user_prompt: str, chart_type: Optional[str] = None) -> Optional[str]:
        """Process user request and generate chart"""
        try:
            with st.spinner("🧠 Processing with API..."):
                # Generate data with API
                api_response = self.api_client.generate_data_and_chart(user_prompt, chart_type)
            
            with st.spinner("📊 Creating interactive chart..."):
                # Create chart
                figure = self.graph_generator.create_chart(api_response)
            
            with st.spinner("🌐 Generating HTML file..."):
                # Generate HTML
                html_path = self.html_generator.generate_html(figure, api_response)
            
            return html_path, api_response
            
        except Exception as e:
            st.error(f"❌ Error generating chart: {str(e)}")
            return None, None
    
    def display_chart_info(self, html_path: str, api_response: dict):
        """Display chart information and actions"""
        chart_type = api_response.get('chart_type', 'Unknown')
        data_points = len(api_response.get('data', {}).get('labels', []))
        
        # Create columns for info display
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📊 Chart Type", chart_type.title())
        
        with col2:
            st.metric("📈 Data Points", data_points)
        
        with col3:
            file_size = Path(html_path).stat().st_size
            st.metric("💾 File Size", f"{file_size:,} bytes")
        
        # Action buttons
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🌐 Open in Browser", key=f"open_{hash(html_path)}"):
                webbrowser.open(f"file://{os.path.abspath(html_path)}")
                st.success("📂 File opened in browser!")
        
        with col2:
            if st.button("📁 Show in Folder", key=f"folder_{hash(html_path)}"):
                folder_path = Path(html_path).parent
                if os.name == 'nt':  # Windows
                    os.startfile(folder_path)
                elif os.name == 'posix':  # macOS/Linux
                    os.system(f'open "{folder_path}"' if os.uname().sysname == 'Darwin' else f'xdg-open "{folder_path}"')
                st.success("📂 Folder opened!")
        
        with col3:
            # Download button for HTML file
            with open(html_path, 'rb') as f:
                st.download_button(
                    label="⬇️ Download HTML",
                    data=f.read(),
                    file_name=Path(html_path).name,
                    mime="text/html",
                    key=f"download_{hash(html_path)}"
                )
        
        with col4:
            if st.button("🔄 Generate Another", key=f"another_{hash(html_path)}"):
                st.rerun()
        
        # Display file path
        st.info(f"📍 **File Location:** `{html_path}`")


def main():
    """Main Streamlit application"""
    
    # Page configuration
    st.set_page_config(
        page_title="API Chart Generator",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize app
    app = StreamlitChatApp()
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border-left: 4px solid #667eea;
        background-color: #f8f9fa;
    }
    
    .stButton > button {
        width: 100%;
        border-radius: 5px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🤖 API Chart Generator</h1>
        <p>Transform your ideas into beautiful interactive charts with AI</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Chart type selection
        chart_type_options = {
            "Auto-detect": None,
            "📊 Bar Chart": "bar",
            "📈 Line Chart": "line", 
            "🥧 Pie Chart": "pie",
            "📍 Scatter Plot": "scatter"
        }
        
        selected_chart_type = st.selectbox(
            "Chart Type",
            options=list(chart_type_options.keys()),
            help="Choose a specific chart type or let AI auto-detect"
        )
        chart_type = chart_type_options[selected_chart_type]
        
        st.divider()
        
        # App status
        if app.initialize_components():
            st.success("🟢 Ready to generate charts!")
            
            # Show recent files
            st.header("📁 Recent Charts")
            output_dir = Path("outputs")
            if output_dir.exists():
                html_files = sorted(output_dir.glob("*.html"), key=lambda x: x.stat().st_mtime, reverse=True)
                
                if html_files:
                    for i, file_path in enumerate(html_files[:5]):  # Show last 5 files
                        file_name = file_path.name[:30] + "..." if len(file_path.name) > 30 else file_path.name
                        if st.button(f"📄 {file_name}", key=f"recent_{i}"):
                            webbrowser.open(f"file://{file_path.absolute()}")
                else:
                    st.info("No charts generated yet")
        else:
            st.error("🔴 Initialization failed")
            st.stop()
    
    # Main chat interface
    st.header("💬 Chat with API")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "👋 Hi! I'm your AI chart generator. Tell me what kind of chart you'd like to create!\n\n**Examples:**\n- *Create a pie chart showing market share*\n- *Generate monthly sales trends as a line chart*\n- *Show quarterly revenue comparison*"
            }
        ]
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # If this is a chart response, show the chart info
            if message["role"] == "assistant" and "chart_info" in message:
                chart_info = message["chart_info"]
                # Handle both old and new response formats
                response_data = chart_info.get("api_response") or chart_info.get("gemini_response")
                if response_data:
                    app.display_chart_info(chart_info["html_path"], response_data)
    
    # Chat input
    if prompt := st.chat_input("Describe the chart you want to create..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            # Process the request
            result = app.process_chart_request(prompt, chart_type)
            
            if result[0]:  # If successful
                html_path, api_response = result
                
                # Success message
                chart_type_display = api_response.get('chart_type', 'Unknown').title()
                success_message = f"""
                🎉 **Chart Generated Successfully!**
                
                📊 **Chart Type:** {chart_type_display}
                📈 **Data Points:** {len(api_response.get('data', {}).get('labels', []))}
                💾 **Title:** {api_response.get('title', 'Generated Chart')}
                
                Your interactive chart has been created and saved!
                """
                
                st.markdown(success_message)
                
                # Display chart info
                app.display_chart_info(html_path, api_response)
                
                # Add to chat history with chart info
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": success_message,
                    "chart_info": {
                        "html_path": html_path,
                        "api_response": api_response
                    }
                })
            
            else:  # If failed
                error_message = """
                ❌ **Chart Generation Failed**
                
                Please try:
                - Being more specific about your data requirements
                - Checking your internet connection
                - Trying a different chart type
                
                Example: *"Create a pie chart showing smartphone market share with 5-6 brands"*
                """
                
                st.markdown(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})
    
    # Footer
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 1rem;'>
        🚀 Powered by <strong>Custom API</strong> & <strong>Plotly</strong> | 
        Built with ❤️ using <strong>Streamlit</strong>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
