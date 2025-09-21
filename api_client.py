"""
API Client for Chart Generation
Handles POST requests to external API endpoint with custom payload structure.
"""

import json
import re
import requests
from typing import Dict, Any, Optional
from config import get_config


class APIClient:
    """Client for external API integration"""
    
    def __init__(self):
        """Initialize the API client"""
        self.config = get_config()
        
        if self.config.verbose:
            print(f"✅ API client initialized with URL: {self.config.api_url}")
    
    def generate_data_and_chart(self, user_prompt: str, chart_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate data and chart instructions based on user prompt
        
        Args:
            user_prompt: User's request for data visualization
            chart_type: Optional specific chart type (bar, line, pie, scatter)
        
        Returns:
            Dictionary containing data, chart configuration, and metadata
        """
        try:
            # Create the payload according to the specified structure
            payload = self._create_payload(user_prompt, chart_type)
            
            # Make POST request
            response = self._make_request(payload)
            
            # Parse the response
            parsed_response = self._parse_response(response, user_prompt, chart_type)
            
            # Add metadata
            parsed_response['original_prompt'] = user_prompt
            parsed_response['api_url'] = self.config.api_url
            
            return parsed_response
            
        except Exception as e:
            if self.config.debug:
                print(f"❌ Error generating content: {str(e)}")
            
            # Provide more specific error messages
            error_msg = str(e)
            if "API request failed" in error_msg:
                raise Exception(f"❌ **API Connection Error**\n\n{error_msg}\n\n💡 **Please check:**\n- Your API_URL is correct\n- The API endpoint is accessible\n- Your internet connection")
            elif "Failed to parse" in error_msg:
                raise Exception(f"❌ **API Response Error**\n\n{error_msg}\n\n💡 **The API returned an unexpected response format**")
            else:
                raise Exception(f"❌ **Chart Generation Error**\n\n{error_msg}")
    
    def _create_payload(self, user_prompt: str, chart_type: Optional[str] = None) -> Dict[str, Any]:
        """Create the payload structure as specified"""
        
        # Create enhanced prompt for data generation
        enhanced_prompt = self._create_data_prompt(user_prompt, chart_type)
        
        payload = {
            "PROJECT": "Chart Generator",
            "CONTEXT": "Generate interactive chart data based on user request",
            "INJECTION": {
                "INPUT": enhanced_prompt
            },
            "injection": {
                "temperature": str(self.config.temperature),
                "topk": str(self.config.top_k),
                "token": str(self.config.max_tokens)
            }
        }
        
        return payload
    
    def _make_request(self, payload: Dict[str, Any]) -> str:
        """Make POST request to the API endpoint"""
        
        try:
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            response = requests.post(
                self.config.api_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            response.raise_for_status()
            
            # Try to get JSON response, fallback to text
            try:
                return response.json()
            except json.JSONDecodeError:
                return response.text
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
    
    def _create_data_prompt(self, user_prompt: str, chart_type: Optional[str] = None) -> str:
        """Create an enhanced prompt for data generation"""
        
        chart_instruction = ""
        if chart_type:
            chart_instruction = f"The chart type should be: {chart_type}"
        
        enhanced_prompt = f"""
You are a data visualization assistant. Based on the user's request, generate realistic data and provide chart configuration.

User Request: {user_prompt}
{chart_instruction}

CHART TYPE SELECTION RULES:
- If user mentions "pie chart" or "pie" → use "pie"
- If user mentions "line chart", "line graph", "trend", "over time" → use "line"  
- If user mentions "bar chart", "bar graph", "comparison" → use "bar"
- If user mentions "scatter plot", "correlation", "relationship" → use "scatter"
- If unclear, choose the most appropriate type for the data

Please provide your response in the following JSON format:
{{
    "title": "Chart title",
    "description": "Brief description of the data",
    "chart_type": "bar|line|pie|scatter",
    "data": {{
        "labels": ["label1", "label2", "label3"],
        "datasets": [{{
            "name": "Dataset Name",
            "values": [10, 20, 30]
        }}]
    }},
    "chart_config": {{
        "x_axis_title": "X-axis label",
        "y_axis_title": "Y-axis label",
        "color_scheme": "viridis|plotly|blues",
        "show_legend": true
    }}
}}

CRITICAL: The chart_type field must EXACTLY match what the user requested. If they said "pie chart", use "pie". If they said "line chart", use "line".

Important guidelines:
1. Generate realistic, relevant data (5-20 data points)
2. ALWAYS set chart_type correctly based on user request
3. Provide meaningful labels and titles
4. Ensure data makes sense for the requested topic
5. Use proper JSON formatting

Response:
"""
        
        return enhanced_prompt
    
    def _parse_response(self, response: Any, user_prompt: str = "", chart_type: Optional[str] = None) -> Dict[str, Any]:
        """Parse API response and extract structured data"""
        
        try:
            # Handle different response types
            if isinstance(response, dict):
                response_text = json.dumps(response)
            elif isinstance(response, str):
                response_text = response
            else:
                response_text = str(response)
            
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                parsed_data = json.loads(json_str)
                
                # Validate required fields
                required_fields = ['title', 'chart_type', 'data']
                for field in required_fields:
                    if field not in parsed_data:
                        raise ValueError(f"Missing required field: {field}")
                
                # Set defaults for optional fields
                if 'description' not in parsed_data:
                    parsed_data['description'] = "Generated data visualization"
                
                if 'chart_config' not in parsed_data:
                    parsed_data['chart_config'] = self._default_chart_config()
                
                # Ensure chart_type is not None - detect from user prompt if missing
                if not parsed_data.get('chart_type'):
                    parsed_data['chart_type'] = self._detect_chart_type_from_prompt(user_prompt, chart_type)
                
                return parsed_data
            
            else:
                # No JSON found in response
                raise Exception(f"No valid JSON found in API response. Response: {response_text[:200]}...")
                
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse API response as JSON: {e}"
            if self.config.debug:
                print(f"❌ JSON parsing error: {e}")
                print(f"Response text: {str(response)[:500]}...")
            raise Exception(f"{error_msg}\n\nAPI Response: {str(response)[:200]}...")
        
        except Exception as e:
            if self.config.debug:
                print(f"❌ Response parsing error: {e}")
            raise Exception(f"Failed to parse API response: {str(e)}")
    
    def _detect_chart_type_from_prompt(self, user_prompt: str, explicit_chart_type: Optional[str] = None) -> str:
        """Detect chart type from user prompt or explicit type"""
        if explicit_chart_type:
            return explicit_chart_type
        
        prompt_lower = user_prompt.lower()
        
        # Check for specific chart type mentions
        if 'pie chart' in prompt_lower or 'pie' in prompt_lower:
            return 'pie'
        elif any(word in prompt_lower for word in ['line chart', 'line graph', 'trend', 'over time', 'time series']):
            return 'line'
        elif any(word in prompt_lower for word in ['scatter plot', 'correlation', 'relationship', 'vs', 'versus']):
            return 'scatter'
        elif any(word in prompt_lower for word in ['bar chart', 'bar graph', 'comparison', 'compare']):
            return 'bar'
        
        # Default fallback based on data type hints
        if any(word in prompt_lower for word in ['share', 'distribution', 'percentage', 'proportion']):
            return 'pie'
        elif any(word in prompt_lower for word in ['growth', 'change', 'monthly', 'yearly', 'daily']):
            return 'line'
        else:
            return 'bar'  # Final fallback
    
    
    def _default_chart_config(self) -> Dict[str, Any]:
        """Return default chart configuration"""
        
        return {
            'x_axis_title': 'Categories',
            'y_axis_title': 'Values',
            'color_scheme': 'viridis',
            'show_legend': True,
            'responsive': True
        }
    
    def test_connection(self) -> bool:
        """Test connection to API endpoint"""
        
        try:
            test_payload = {
                "PROJECT": "Test",
                "CONTEXT": "Connection test",
                "INJECTION": {
                    "INPUT": "Hello, please respond with 'API connection successful'"
                },
                "injection": {
                    "temperature": "0.1",
                    "topk": "0.1",
                    "token": "50"
                }
            }
            
            response = self._make_request(test_payload)
            
            if response and "successful" in str(response).lower():
                if self.config.verbose:
                    print("✅ API connection test successful")
                return True
            else:
                if self.config.verbose:
                    print("⚠️ API connection test returned unexpected response")
                return False
                
        except Exception as e:
            if self.config.verbose:
                print(f"❌ API connection test failed: {str(e)}")
            return False


def test_api_client():
    """Test function for the API client"""
    
    print("🧪 Testing API Client...")
    
    try:
        client = APIClient()
        
        # Test connection
        if not client.test_connection():
            print("❌ Connection test failed")
            return False
        
        # Test data generation
        test_prompt = "Create a simple bar chart showing monthly sales data"
        result = client.generate_data_and_chart(test_prompt)
        
        print("✅ Test successful!")
        print(f"Generated title: {result['title']}")
        print(f"Chart type: {result['chart_type']}")
        print(f"Data points: {len(result['data']['labels'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False


if __name__ == "__main__":
    test_api_client()
