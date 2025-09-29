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
        """Display chart information, analysis, and actions"""
        chart_type = api_response.get('chart_type', 'Unknown')
        data_points = len(api_response.get('data', {}).get('labels', []))
        
        # Display prediction analysis if available
        prediction_analysis = api_response.get('prediction_analysis')
        parsing_error = api_response.get('parsing_error', False)
        
        if prediction_analysis:
            # Show different header based on whether there was a parsing error
            if parsing_error:
                st.subheader("🧠 AI Analysis (Chart parsing had issues)")
                error_reason = api_response.get('error_reason', 'Unknown error')
                st.warning(f"⚠️ {error_reason}, but AI analysis was successfully extracted.")
            else:
                st.subheader("🧠 AI Analysis")
            
            with st.expander("📝 View Detailed Analysis", expanded=True):
                # Style the analysis text with better formatting
                formatted_analysis = self._format_analysis_text(prediction_analysis)
                st.markdown(formatted_analysis)
            
            st.divider()
        
        # Chart metrics section
        st.subheader("📊 Chart Details")
        
        # Create columns for info display
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📊 Chart Type", chart_type.title())
        
        with col2:
            st.metric("📈 Data Points", data_points)
        
        with col3:
            file_size = Path(html_path).stat().st_size
            st.metric("💾 File Size", f"{file_size:,} bytes")
        
        # Additional chart information
        with st.expander("📋 Chart Configuration Details"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Chart Information:**")
                st.write(f"• **Title:** {api_response.get('title', 'N/A')}")
                st.write(f"• **Description:** {api_response.get('description', 'N/A')}")
                st.write(f"• **Type:** {chart_type.title()}")
                
                # Data information
                data = api_response.get('data', {})
                labels = data.get('labels', [])
                datasets = data.get('datasets', [])
                
                st.write(f"• **Labels:** {', '.join(labels[:3])}{'...' if len(labels) > 3 else ''}")
                st.write(f"• **Datasets:** {len(datasets)} series")
            
            with col2:
                st.write("**Chart Configuration:**")
                chart_config = api_response.get('chart_config', {})
                st.write(f"• **X-Axis:** {chart_config.get('x_axis_title', 'N/A')}")
                st.write(f"• **Y-Axis:** {chart_config.get('y_axis_title', 'N/A')}")
                st.write(f"• **Color Scheme:** {chart_config.get('color_scheme', 'N/A')}")
                st.write(f"• **Show Legend:** {'Yes' if chart_config.get('show_legend', True) else 'No'}")
                
                # Show original prompt if available
                original_prompt = api_response.get('original_prompt', '')
                if original_prompt:
                    st.write("**Original Request:**")
                    st.write(f"*\"{original_prompt[:100]}{'...' if len(original_prompt) > 100 else ''}\"*")
        
        st.divider()
        
        # Action buttons
        st.subheader("🎯 Actions")
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
    
    def _format_analysis_text(self, analysis_text: str) -> str:
        """Format the analysis text for better display in Streamlit"""
        
        # Handle None or empty input
        if not analysis_text:
            return ""
        
        # Ensure we have a string
        if not isinstance(analysis_text, str):
            return str(analysis_text)
        
        # Split into paragraphs and format
        paragraphs = analysis_text.split('\n\n')
        formatted_paragraphs = []
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
                
            # Handle bullet points and lists
            if paragraph.startswith('*') or paragraph.startswith('-'):
                # Convert to markdown list
                lines = paragraph.split('\n')
                formatted_lines = []
                for line in lines:
                    line = line.strip()
                    if line.startswith('*') or line.startswith('-'):
                        formatted_lines.append(f"• {line[1:].strip()}")
                    else:
                        formatted_lines.append(line)
                formatted_paragraphs.append('\n'.join(formatted_lines))
            else:
                formatted_paragraphs.append(paragraph)
        
        return '\n\n'.join(formatted_paragraphs)


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
    
    # Debug information
    if st.checkbox("🔍 Debug Mode", help="Show debug information"):
        st.write("**Debug Info:**")
        st.write(f"- App initialized: {app.initialized}")
        st.write(f"- Messages in history: {len(st.session_state.get('messages', []))}")
        st.write(f"- Selected chart type: {chart_type}")
        st.write(f"- API URL: {app.config.api_url if app.config else 'Not loaded'}")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "👋 Hi! I'm your AI chart generator. Tell me what kind of chart you'd like to create!\n\n**Examples:**\n- *Create a pie chart showing market share*\n- *Generate monthly sales trends as a line chart*\n- *Show quarterly revenue comparison*\n\n💡 **Note:** If the chat input becomes unresponsive after your first message, please refresh the page. This is a known issue we're working to resolve."
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
    
    # Chat input - ensure it's always available
    prompt = st.chat_input("Describe the chart you want to create...")
    
    if prompt:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response with better error handling
        with st.chat_message("assistant"):
            try:
                # Process the request
                result = app.process_chart_request(prompt, chart_type)
                
                if result and result[0]:  # If successful
                    html_path, api_response = result
                    
                    # Success message
                    chart_type_display = api_response.get('chart_type', 'Unknown').title()
                    analysis_available = api_response.get('prediction_analysis') is not None
                    
                    success_message = f"""
                    🎉 **Chart Generated Successfully!**
                    
                    📊 **Chart Type:** {chart_type_display}
                    📈 **Data Points:** {len(api_response.get('data', {}).get('labels', []))}
                    💾 **Title:** {api_response.get('title', 'Generated Chart')}
                    {f"🧠 **AI Analysis:** Available below" if analysis_available else ""}
                    
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
            
            except Exception as e:
                # Handle any unexpected errors to prevent chat input from breaking
                error_message = f"""
                ❌ **Unexpected Error Occurred**
                
                Error details: {str(e)}
                
                Please try again with a different request. The chat input should remain functional.
                
                💡 **Tip:** Try a simpler request like "Create a bar chart with sample data"
                """
                
                st.error(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})
                
                # Force rerun to ensure chat input remains available
                st.rerun()
    
    # Chat controls
    st.divider()
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("🔄 Reset Chat", help="Clear all messages and reset the chat"):
            st.session_state.messages = [
                {
                    "role": "assistant",
                    "content": "👋 Chat has been reset! Tell me what kind of chart you'd like to create!"
                }
            ]
            st.rerun()
    
    with col2:
        if st.button("🧪 Test Input", help="Test if chat input is working"):
            st.session_state.messages.append({
                "role": "assistant", 
                "content": "✅ Chat input is working! You can continue chatting normally."
            })
            st.rerun()
    
    with col3:
        st.info("💡 If chat input stops working, try the Reset Chat button")
    
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
