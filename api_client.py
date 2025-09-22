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
                timeout=180
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
        """Parse API response and extract structured data from prediction field"""
        
        prediction_content = None
        chart_data = None
        
        try:
            # Handle different response types and extract prediction field
            prediction_content = self._extract_prediction_content(response)
            
            if not prediction_content:
                raise Exception("No prediction content found in API response")
            
            # Extract JSON from the prediction content
            chart_data = self._extract_chart_json_from_prediction(prediction_content)
            
            if not chart_data:
                raise Exception("No valid chart JSON found in prediction content")
            
            # Validate required fields
            required_fields = ['title', 'chart_type', 'data']
            for field in required_fields:
                if field not in chart_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Set defaults for optional fields
            if 'description' not in chart_data:
                chart_data['description'] = "Generated data visualization"
            
            if 'chart_config' not in chart_data:
                chart_data['chart_config'] = self._default_chart_config()
            
            # Ensure chart_type is not None - detect from user prompt if missing
            if not chart_data.get('chart_type'):
                chart_data['chart_type'] = self._detect_chart_type_from_prompt(user_prompt, chart_type)
            
            # Always try to extract analysis text if we have prediction content
            if prediction_content:
                analysis_text = self._extract_analysis_text_from_prediction(prediction_content)
                if analysis_text:
                    chart_data['prediction_analysis'] = analysis_text
            
            return chart_data
                
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse chart JSON from prediction: {e}"
            if self.config.debug:
                print(f"❌ JSON parsing error: {e}")
                print(f"Response: {str(response)[:500]}...")
            
            # Try to return analysis-only fallback
            fallback_data = self._create_fallback_response(prediction_content, user_prompt, chart_type, "JSON parsing failed")
            if fallback_data:
                return fallback_data
            
            raise Exception(f"{error_msg}\n\nAPI Response: {str(response)[:200]}...")
        
        except Exception as e:
            if self.config.debug:
                print(f"❌ Response parsing error: {e}")
            
            # Try to return analysis-only fallback for any other error
            fallback_data = self._create_fallback_response(prediction_content, user_prompt, chart_type, "Chart parsing failed")
            if fallback_data:
                return fallback_data
            
            raise Exception(f"Failed to parse API response: {str(e)}")
    
    def _create_fallback_response(self, prediction_content: Optional[str], user_prompt: str, chart_type: Optional[str], error_reason: str) -> Optional[Dict[str, Any]]:
        """Create a fallback response when chart parsing fails but analysis is available"""
        
        if not prediction_content:
            return None
        
        analysis_text = self._extract_analysis_text_from_prediction(prediction_content)
        if not analysis_text:
            return None
        
        fallback_data = {
            'title': 'AI Analysis Available',
            'description': f'{error_reason} but analysis was extracted',
            'chart_type': self._detect_chart_type_from_prompt(user_prompt, chart_type),
            'data': {'labels': ['Placeholder'], 'datasets': [{'name': 'Values', 'values': [1]}]},
            'chart_config': self._default_chart_config(),
            'prediction_analysis': analysis_text,
            'parsing_error': True,
            'error_reason': error_reason
        }
        
        if self.config.debug:
            print(f"✅ Created fallback response with analysis ({len(analysis_text)} chars)")
        
        return fallback_data
    
    def _extract_prediction_content(self, response: Any) -> Optional[str]:
        """Extract prediction content from API response"""
        
        try:
            # Handle different response formats
            if isinstance(response, dict):
                # Check for prediction field directly
                if 'prediction' in response:
                    return response['prediction']
                
                # If response is already the prediction content
                if 'title' in response and 'chart_type' in response:
                    return json.dumps(response)
                
                # Convert dict to JSON string for further processing
                response_text = json.dumps(response)
            elif isinstance(response, str):
                response_text = response
            else:
                response_text = str(response)
            
            # Try to find prediction field in JSON response
            try:
                parsed_response = json.loads(response_text)
                if isinstance(parsed_response, dict) and 'prediction' in parsed_response:
                    return parsed_response['prediction']
            except json.JSONDecodeError:
                pass
            
            # If no prediction field found, return the original response
            return response_text
            
        except Exception as e:
            if self.config.debug:
                print(f"❌ Error extracting prediction content: {e}")
            return None
    
    def _extract_chart_json_from_prediction(self, prediction_content: str) -> Optional[Dict[str, Any]]:
        """Extract chart configuration JSON from prediction content"""
        
        try:
            if self.config.debug:
                print(f"🔍 Extracting JSON from prediction content ({len(prediction_content)} chars)")
            
            # Clean up the prediction content - remove escape sequences and extra quotes
            cleaned_content = prediction_content
            if cleaned_content.startswith('"""') and cleaned_content.endswith('"'):
                cleaned_content = cleaned_content[3:-1]  # Remove triple quotes at start and quote at end
            
            # Handle escaped newlines and quotes
            cleaned_content = cleaned_content.replace('\\n', '\n').replace('\\"', '"')
            
            # Remove non-breaking spaces and other problematic Unicode characters
            cleaned_content = cleaned_content.replace('\xa0', ' ')  # Non-breaking space to regular space
            cleaned_content = cleaned_content.replace('\u2000', ' ')  # En quad
            cleaned_content = cleaned_content.replace('\u2001', ' ')  # Em quad
            cleaned_content = cleaned_content.replace('\u2002', ' ')  # En space
            cleaned_content = cleaned_content.replace('\u2003', ' ')  # Em space
            cleaned_content = cleaned_content.replace('\u2004', ' ')  # Three-per-em space
            cleaned_content = cleaned_content.replace('\u2005', ' ')  # Four-per-em space
            cleaned_content = cleaned_content.replace('\u2006', ' ')  # Six-per-em space
            cleaned_content = cleaned_content.replace('\u2007', ' ')  # Figure space
            cleaned_content = cleaned_content.replace('\u2008', ' ')  # Punctuation space
            cleaned_content = cleaned_content.replace('\u2009', ' ')  # Thin space
            cleaned_content = cleaned_content.replace('\u200a', ' ')  # Hair space
            
            if self.config.debug:
                print(f"📝 Cleaned content preview: {cleaned_content[:200]}...")
            
            # Look for JSON after "json" keyword (common pattern in the response)
            json_start_patterns = [
                r'json\s*\n\s*\{',  # "json" followed by newline and opening brace
                r'```json\s*\n\s*\{',  # markdown json block
                r'\{',  # Just look for opening brace
            ]
            
            for pattern in json_start_patterns:
                match = re.search(pattern, cleaned_content, re.IGNORECASE | re.MULTILINE)
                if match:
                    # Find the start of the JSON (the opening brace)
                    json_start = match.end() - 1 if pattern != r'\{' else match.start()
                    
                    # Extract everything from the opening brace onwards
                    json_candidate = cleaned_content[json_start:].strip()
                    
                    if self.config.debug:
                        print(f"🎯 Found JSON candidate starting at position {json_start}")
                        print(f"📄 JSON candidate preview: {json_candidate[:200]}...")
                    
                    # Try to parse this as JSON
                    parsed_json = self._try_parse_json_candidate(json_candidate)
                    if parsed_json:
                        return parsed_json
            
            # Fallback: try to find any JSON-like structure
            if self.config.debug:
                print("🔄 Trying fallback JSON extraction methods...")
            
            # Look for balanced braces
            brace_count = 0
            json_start = -1
            
            for i, char in enumerate(cleaned_content):
                if char == '{':
                    if json_start == -1:
                        json_start = i
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0 and json_start != -1:
                        # Found a complete JSON object
                        json_candidate = cleaned_content[json_start:i+1]
                        parsed_json = self._try_parse_json_candidate(json_candidate)
                        if parsed_json:
                            return parsed_json
                        # Reset for next potential JSON object
                        json_start = -1
            
            return None
            
        except Exception as e:
            if self.config.debug:
                print(f"❌ Error extracting chart JSON: {e}")
            return None
    
    def _try_parse_json_candidate(self, json_candidate: str) -> Optional[Dict[str, Any]]:
        """Try to parse a JSON candidate string and validate it's chart data"""
        
        try:
            # Remove any trailing non-JSON content
            json_candidate = json_candidate.strip()
            
            # Find the end of the JSON object
            brace_count = 0
            json_end = -1
            
            for i, char in enumerate(json_candidate):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_end = i + 1
                        break
            
            if json_end > 0:
                json_str = json_candidate[:json_end]
            else:
                json_str = json_candidate
            
            if self.config.debug:
                print(f"🧪 Trying to parse JSON: {json_str[:100]}...")
            
            parsed_json = json.loads(json_str)
            
            # Validate this is chart data
            if (isinstance(parsed_json, dict) and 
                'title' in parsed_json and 
                'chart_type' in parsed_json and 
                'data' in parsed_json):
                
                if self.config.debug:
                    print(f"✅ Found valid chart JSON with title: {parsed_json.get('title', 'N/A')}")
                
                return parsed_json
            else:
                if self.config.debug:
                    print(f"❌ JSON object doesn't have required chart fields")
                return None
                
        except json.JSONDecodeError as e:
            if self.config.debug:
                print(f"❌ JSON decode error: {e}")
            return None
        except Exception as e:
            if self.config.debug:
                print(f"❌ Error parsing JSON candidate: {e}")
            return None
    
    def _extract_analysis_text_from_prediction(self, prediction_content: str) -> Optional[str]:
        """Extract the analysis text from prediction content (everything before the JSON)"""
        
        try:
            # Clean up the prediction content
            cleaned_content = prediction_content
            if cleaned_content.startswith('"""') and cleaned_content.endswith('"'):
                cleaned_content = cleaned_content[3:-1]
            
            # Handle escaped newlines and quotes
            cleaned_content = cleaned_content.replace('\\n', '\n').replace('\\"', '"')
            
            # Remove non-breaking spaces and other problematic Unicode characters
            cleaned_content = cleaned_content.replace('\xa0', ' ')
            for unicode_char in ['\u2000', '\u2001', '\u2002', '\u2003', '\u2004', 
                               '\u2005', '\u2006', '\u2007', '\u2008', '\u2009', '\u200a']:
                cleaned_content = cleaned_content.replace(unicode_char, ' ')
            
            # Find where the JSON starts
            json_patterns = [
                r'json\s*\n\s*\{',  # "json" followed by newline and opening brace
                r'```json\s*\n\s*\{',  # markdown json block
                r'\{(?=\s*"title")',  # opening brace followed by "title" field
            ]
            
            json_start_pos = len(cleaned_content)  # Default to end if no JSON found
            
            for pattern in json_patterns:
                match = re.search(pattern, cleaned_content, re.IGNORECASE | re.MULTILINE)
                if match:
                    json_start_pos = match.start()
                    break
            
            # Extract everything before the JSON as analysis text
            analysis_text = cleaned_content[:json_start_pos].strip()
            
            # Clean up the analysis text
            if analysis_text:
                # Remove any remaining markdown artifacts
                analysis_text = re.sub(r'^```.*?\n', '', analysis_text, flags=re.MULTILINE)
                analysis_text = re.sub(r'\n```$', '', analysis_text)
                
                # Remove extra whitespace and normalize line breaks
                analysis_text = re.sub(r'\n\s*\n\s*\n', '\n\n', analysis_text)  # Max 2 consecutive newlines
                analysis_text = analysis_text.strip()
                
                # Check if this is just placeholder text
                placeholder_indicators = [
                    '…huge string……...',
                    'huge string',
                    '...',
                    'placeholder',
                    'sample text'
                ]
                
                is_placeholder = any(indicator in analysis_text.lower() for indicator in placeholder_indicators)
                
                if is_placeholder and len(analysis_text) < 200:
                    # Generate a meaningful fallback message
                    analysis_text = """**AI Analysis Summary:**

This chart was generated based on your request. The AI model analyzed the data requirements and created an appropriate visualization with the following considerations:

• **Data Structure**: The chart includes properly formatted labels and datasets
• **Visualization Type**: Selected based on the nature of your data and request
• **Configuration**: Optimized chart settings for clarity and readability
• **Interactivity**: Generated as an interactive HTML chart for better user experience

The model processed your request and generated realistic sample data that demonstrates the patterns and relationships you requested."""
                
                if len(analysis_text) > 10:  # Only return if substantial content
                    if self.config.debug:
                        print(f"✅ Extracted analysis text ({len(analysis_text)} chars)")
                    return analysis_text
            
            return None
        
        except Exception as e:
            if self.config.debug:
                print(f"❌ Error extracting analysis text: {e}")
            return None
    
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
