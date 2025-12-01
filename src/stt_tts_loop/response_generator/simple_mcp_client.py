"""
Simplified MCP Integration for Voice WebSocket Server
Uses subprocess calls to MCP server for each tool request
"""

import asyncio
import json
import subprocess
import sys
import os
from typing import Dict, Any, Optional, List
import logging
import tempfile
from dotenv import load_dotenv


# Load environment variables (including GROQ_API_KEY) from a .env file if present
load_dotenv()

logger = logging.getLogger(__name__)

class SimpleMCPClient:
    """Simple MCP Client that can connect to multiple MCP servers"""
    
    def __init__(self, server_configs: List[Dict[str, Any]] = None):
        if server_configs is None:
            server_configs = self._load_server_configs()
        
        self.server_configs = server_configs
        self.available_tools = []
        self.tool_to_server = {}  # Maps tool names to server names
        self.protocol_info = self._load_protocol_json()
    
    def _load_server_configs(self) -> List[Dict[str, Any]]:
        """Load server configurations from servers_config.json"""
        try:
            config_path = "/root/voice_websocket/src/mcp/servers_config.json"
            with open(config_path, 'r') as f:
                config_data = json.load(f)
                return config_data.get("servers", [])
        except Exception as e:
            logger.warning(f"Failed to load server configs: {e}. Using default configs.")
            return [
                {
                    "name": "sample_server",
                    "command": "python",
                    "args": ["-m", "src.mcp.sample_server"]
                },
                {
                    "name": "new_sample_server", 
                    "command": "python",
                    "args": ["-m", "src.mcp.new_sample_server"]
                }
            ]
    
    def _load_protocol_json(self) -> Dict[str, Any]:
        """Load protocol.json file for tool validation"""
        try:
            protocol_path = "/root/voice_websocket/src/mcp/protocol.json"
            with open(protocol_path, 'r') as f:
                protocol_data = json.load(f)
            logger.info(f"Loaded protocol.json: {protocol_data.get('name', 'Unknown')}")
            return protocol_data
        except Exception as e:
            logger.warning(f"Failed to load protocol.json: {e}")
            return {}
        
    async def initialize(self):
        """Initialize and discover available tools from all MCP servers"""
        try:
            logger.info(f"Initializing MCP client for {len(self.server_configs)} servers")
            for config in self.server_configs:
                logger.info(f"  - {config['name']}: {config['command']} {' '.join(config['args'])}")
            
            # Discover available tools from all MCP servers
            self.available_tools = await self._discover_tools()
            logger.info(f"Available tools: {self.available_tools}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize MCP client: {e}")
            logger.error("No fallback tools available - MCP server must be accessible")
            return False
    
    async def _discover_tools(self) -> List[str]:
        """Discover available tools from all MCP servers"""
        all_tools = []
        self.tool_to_server = {}
        
        for server_config in self.server_configs:
            try:
                server_tools = await self._discover_tools_from_server(server_config)
                for tool in server_tools:
                    all_tools.append(tool)
                    self.tool_to_server[tool] = server_config["name"]
                logger.info(f"Discovered {len(server_tools)} tools from {server_config['name']}: {server_tools}")
            except Exception as e:
                logger.warning(f"Failed to discover tools from {server_config['name']}: {e}")
        
        logger.info(f"Total discovered tools: {all_tools}")
        logger.info(f"Tool to server mapping: {self.tool_to_server}")
        return all_tools
    
    async def _discover_tools_from_server(self, server_config: Dict[str, Any]) -> List[str]:
        """Discover tools from a specific MCP server"""
        try:
            # Start MCP server subprocess
            process = await asyncio.create_subprocess_exec(
                server_config["command"], *server_config["args"],
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd="/root/voice_websocket"
            )
            
            # Step 1: Initialize MCP server
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "voice-websocket-client",
                        "version": "1.0.0"
                    }
                }
            }
            
            init_json = json.dumps(init_request) + "\n"
            process.stdin.write(init_json.encode())
            await process.stdin.drain()
            
            # Read initialization response
            init_response_line = await process.stdout.readline()
            init_response = json.loads(init_response_line.decode().strip())
            
            if "error" in init_response:
                logger.error(f"MCP initialization failed for {server_config['name']}: {init_response['error']}")
                raise RuntimeError(f"MCP initialization failed: {init_response['error']}")
            
            # Step 2: List available tools
            list_tools_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list"
            }
            
            list_json = json.dumps(list_tools_request) + "\n"
            process.stdin.write(list_json.encode())
            await process.stdin.drain()
            
            # Read tools list response
            tools_response_line = await process.stdout.readline()
            tools_response = json.loads(tools_response_line.decode().strip())
            
            # Close stdin to signal end of input
            process.stdin.close()
            await process.wait()
            
            if "error" in tools_response:
                logger.error(f"Failed to list tools from {server_config['name']}: {tools_response['error']}")
                raise RuntimeError(f"Failed to list tools: {tools_response['error']}")
            
            # Extract tool names from response
            tools = []
            if "result" in tools_response and "tools" in tools_response["result"]:
                for tool in tools_response["result"]["tools"]:
                    tools.append(tool["name"])
            
            return tools
            
        except Exception as e:
            logger.error(f"Failed to discover tools from {server_config['name']}: {e}")
            raise RuntimeError(f"Cannot discover tools from {server_config['name']}: {e}")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Call a specific MCP tool via subprocess"""
        if tool_name not in self.available_tools:
            available_tools = self.available_tools
            raise ValueError(f"Tool '{tool_name}' not found. Available tools: {available_tools}")
        

        # Validate tool parameters using protocol.json
        self._validate_tool_parameters(tool_name, arguments)
        
        try:
            logger.info(f"Calling tool '{tool_name}' with arguments: {arguments}")
            
            # Create a JSON-RPC request
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            return await self._call_mcp_server(tool_name, arguments)
                
        except Exception as e:
            logger.error(f"Error calling tool '{tool_name}': {e}")
            raise
    
    def _validate_tool_parameters(self, tool_name: str, arguments: Dict[str, Any]) -> None:
        """Validate tool parameters using protocol.json"""
        if not self.protocol_info or "capabilities" not in self.protocol_info:
            logger.warning("No protocol info available for validation")
            return
        
        tools = self.protocol_info["capabilities"].get("tools", [])
        tool_spec = None
        
        for tool in tools:
            if tool["name"] == tool_name:
                tool_spec = tool
                break
        
        if not tool_spec:
            logger.warning(f"Tool '{tool_name}' not found in protocol.json")
            return
        
        # Validate required parameters
        required_params = tool_spec["parameters"].get("required", [])
        for param in required_params:
            if param not in arguments:
                raise ValueError(f"Missing required parameter '{param}' for tool '{tool_name}'")
        
        # Validate parameter types (basic validation)
        properties = tool_spec["parameters"].get("properties", {})
        for param_name, param_value in arguments.items():
            if param_name in properties:
                expected_type = properties[param_name].get("type")
                if expected_type == "integer" and not isinstance(param_value, int):
                    raise ValueError(f"Parameter '{param_name}' must be an integer for tool '{tool_name}'")
                elif expected_type == "string" and not isinstance(param_value, str):
                    raise ValueError(f"Parameter '{param_name}' must be a string for tool '{tool_name}'")
        
        logger.info(f"Tool '{tool_name}' parameters validated successfully using protocol.json")
    
    async def get_available_tools(self) -> List[str]:
        """Get list of available tool names"""
        return self.available_tools.copy()
    
    async def _call_mcp_server(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Call MCP server via subprocess using proper MCP protocol sequence"""
        try:
            logger.info(f"Calling MCP server with tool '{tool_name}' and arguments: {arguments}")
            
            # Find which server has this tool
            if tool_name not in self.tool_to_server:
                raise RuntimeError(f"Tool '{tool_name}' not found in any server")
            
            server_name = self.tool_to_server[tool_name]
            server_config = None
            
            for config in self.server_configs:
                if config["name"] == server_name:
                    server_config = config
                    break
            
            if not server_config:
                raise RuntimeError(f"Server configuration for '{server_name}' not found")
            
            logger.info(f"Calling tool '{tool_name}' on server '{server_name}'")
            
            # Start MCP server subprocess
            process = await asyncio.create_subprocess_exec(
                server_config["command"], *server_config["args"],
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd="/root/voice_websocket"
            )
            
            # Step 1: Initialize MCP server
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "voice-websocket-client",
                        "version": "1.0.0"
                    }
                }
            }
            
            init_json = json.dumps(init_request) + "\n"
            process.stdin.write(init_json.encode())
            await process.stdin.drain()
            
            # Read initialization response
            init_response_line = await process.stdout.readline()
            init_response = json.loads(init_response_line.decode().strip())
            
            if "error" in init_response:
                logger.error(f"MCP initialization failed: {init_response['error']}")
                raise RuntimeError(f"MCP initialization failed: {init_response['error']}")
            
            logger.info("MCP server initialized successfully")
            
            # Step 2: Call the tool
            tool_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            tool_json = json.dumps(tool_request) + "\n"
            process.stdin.write(tool_json.encode())
            await process.stdin.drain()
            
            # Read tool response
            tool_response_line = await process.stdout.readline()
            tool_response_text = tool_response_line.decode().strip()
            logger.info(f"Received MCP server response: {tool_response_text}")
            
            try:
                tool_response = json.loads(tool_response_text)
                
                # Check for JSON-RPC error
                if "error" in tool_response:
                    error_msg = tool_response["error"].get("message", "Unknown error")
                    logger.error(f"JSON-RPC error: {error_msg}")
                    raise RuntimeError(f"MCP tool error: {error_msg}")
                
                # Extract result from response
                if "result" in tool_response and "content" in tool_response["result"]:
                    content = tool_response["result"]["content"]
                    if content and len(content) > 0:
                        # Extract text from content
                        if isinstance(content[0], dict) and "text" in content[0]:
                            result = content[0]["text"]
                            logger.info(f"Tool '{tool_name}' result: {result}")
                            return result
                        else:
                            return str(content[0])
                
                # Fallback: return the entire result as string
                return str(tool_response.get("result", "No result"))
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse MCP server response: {e}")
                logger.error(f"Raw response: {tool_response_text}")
                raise RuntimeError(f"Invalid JSON response from MCP server: {e}")
            
            finally:
                # Close stdin to signal end of input
                process.stdin.close()
                await process.wait()
                
        except Exception as e:
            logger.error(f"Error calling MCP server: {e}")
            raise


class MCPResponseGenerator:
    """Enhanced response generator that uses MCP tools when appropriate"""
    
    def __init__(self, mcp_client: SimpleMCPClient):
        self.mcp_client = mcp_client
        self.groq_client = None
        self.conversation_history = []  # Store last 4 exchanges
        self._init_groq()
    
    def _init_groq(self):
        """Initialize Groq client for fallback responses"""
        try:
            from groq import Groq
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                logger.warning("GROQ_API_KEY not set; Groq fallback responses will be disabled")
                self.groq_client = None
                return
            self.groq_client = Groq(api_key=api_key)
        except ImportError:
            logger.warning("Groq client not available")
    
    async def generate_response(self, user_text: str) -> str:
        """Generate concise response using MCP tools or LLM with conversation history"""
        try:
            # Try tool calling first - direct and simple
            tool_response = await self._try_tool_calling(user_text)
            if tool_response:
                # Add to conversation history
                self._add_to_history(user_text, tool_response)
                return tool_response
            
            # Fallback to LLM for general conversation with history
            llm_response = await self._get_llm_response_with_history(user_text)
            cleaned_response = self._clean_tool_result(llm_response)
            
            # Add to conversation history
            self._add_to_history(user_text, cleaned_response)
            return cleaned_response
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"I encountered an error: {str(e)}"
    
    async def _try_tool_calling(self, user_text: str) -> Optional[str]:
        """Use LLM to decide which tool to call and extract parameters"""
        try:
            # Get available tools from MCP client
            available_tools = await self.mcp_client.get_available_tools()
            
            if not available_tools:
                return None
            
            # Get tool descriptions from protocol.json
            tool_descriptions = self._get_tool_descriptions()
            
            # Use LLM to decide which tool to call and extract parameters
            tool_decision = await self._decide_tool_with_llm(user_text, tool_descriptions)
            
            if tool_decision and tool_decision.get('tool_name') and tool_decision.get('parameters'):
                result = await self.mcp_client.call_tool(tool_decision['tool_name'], tool_decision['parameters'])
                # Return only the clean result, no extra text
                return self._clean_tool_result(result)
            
            return None
            
        except Exception as e:
            logger.error(f"Error in tool calling: {e}")
            return None
    
    def _clean_tool_result(self, result: str) -> str:
        """Clean tool result to remove verbose explanations"""
        if not result:
            return result
        
        # Remove common verbose patterns
        verbose_patterns = [
            r"<think>.*?</think>",  # Remove reasoning blocks
            r"<think>.*?</think>",  # Remove reasoning blocks
            r"I need to check.*?available.*?",
            r"Tool is available.*?",
            r"These are the parameters.*?",
            r"User asked for.*?",
            r"User requested.*?",
            r"Calling tool.*?",
            r"Parameters passed.*?",
            r"Returning result.*?",
            r"\*.*?\*",  # Remove asterisks
            r"\[.*?\]",  # Remove brackets
        ]
        
        import re
        cleaned = result
        for pattern in verbose_patterns:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE | re.DOTALL)
        
        # Clean up extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # Remove any remaining verbose patterns more aggressively
        cleaned = re.sub(r'<.*?>', '', cleaned)  # Remove any XML-like tags
        cleaned = re.sub(r'\(.*?\)', '', cleaned)  # Remove parentheses content
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()  # Clean whitespace again
        
        # If there's still verbose content, try to extract just the final answer
        if len(cleaned) > 200 or 'Okay' in cleaned or 'Let me' in cleaned:
            # Split by common separators and take the last meaningful part
            parts = re.split(r'[.!?]\s+', cleaned)
            if len(parts) > 1:
                # Take the last part that looks like an answer
                for part in reversed(parts):
                    if len(part) > 10 and not any(word in part.lower() for word in ['okay', 'let me', 'i need', 'wait']):
                        cleaned = part.strip()
                        break
        
        # Final cleanup: if there's still verbose content, extract just the last sentence
        if len(cleaned) > 150:
            sentences = cleaned.split('.')
            if len(sentences) > 1:
                # Take the last complete sentence
                cleaned = sentences[-2] + '.' if len(sentences) > 1 else sentences[-1]
        
        # If result is too long, take first sentence
        sentences = cleaned.split('.')
        if len(sentences) > 1 and len(cleaned) > 100:
            cleaned = sentences[0] + '.'
        
        return cleaned
    
    def _add_to_history(self, user_text: str, response: str):
        """Add exchange to conversation history (keep last 2)"""
        self.conversation_history.append({
            "user": user_text,
            "assistant": response
        })
        
        # Keep only last 4 exchanges
        if len(self.conversation_history) > 2:
            self.conversation_history = self.conversation_history[-4:]
    
    def _get_conversation_context(self) -> str:
        """Get conversation history as context string"""
        if not self.conversation_history:
            return ""
        
        context_parts = []
        for exchange in self.conversation_history:
            context_parts.append(f"User: {exchange['user']}")
            context_parts.append(f"Assistant: {exchange['assistant']}")
        
        return "\n".join(context_parts)
    
    async def _get_llm_response_with_history(self, user_text: str, max_tokens: int = 1000) -> str:
        """Get LLM response with conversation history context"""
        if not self.groq_client:
            return "I'm sorry, I can't generate a response right now."
        
        try:
            # Get conversation context
            conversation_context = self._get_conversation_context()
            
            # Create system prompt with history
            if conversation_context:
                system_prompt = (
                    f"You are  Kavach, built by GarudaSec Technologies. Answer in 1-2 sentences only. No explanations, no reasoning, no asterisks, no brackets. "
                    f"Just the direct answer. Always respond in English.\n\n"
                    f"Previous conversation:\n{conversation_context}\n\n"
                    f"Current user message: {user_text}"
                )
            else:
                system_prompt = (
                    f"You are  Kavach, built by GarudaSec Technologies. Answer in 1-2 sentences only. No explanations, no reasoning, no asterisks, no brackets. "
                    f"Just the direct answer. Always respond in English."
                )
            
            response = self.groq_client.chat.completions.create(
                model="qwen/qwen3-32b",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_text}
                ],
                temperature=0.7,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error getting LLM response: {e}")
            return f"I'm sorry, I couldn't generate a response: {str(e)}"
    
    def _get_tool_descriptions(self) -> str:
        """Get tool descriptions from protocol.json"""
        if not self.mcp_client.protocol_info or "capabilities" not in self.mcp_client.protocol_info:
            return ""
        
        tools = self.mcp_client.protocol_info["capabilities"].get("tools", [])
        descriptions = []
        
        for tool in tools:
            name = tool.get("name", "")
            description = tool.get("description", "")
            parameters = tool.get("parameters", {})
            required = parameters.get("required", [])
            properties = parameters.get("properties", {})
            
            param_info = []
            for param in required:
                param_spec = properties.get(param, {})
                param_type = param_spec.get("type", "string")
                param_desc = param_spec.get("description", "")
                param_info.append(f"  - {param} ({param_type}): {param_desc}")
            
            param_str = "\n".join(param_info) if param_info else "  - No parameters required"
            
            descriptions.append(f"Tool: {name}\nDescription: {description}\nParameters:\n{param_str}")
        
        return "\n\n".join(descriptions)
    
    async def _decide_tool_with_llm(self, user_text: str, tool_descriptions: str) -> Optional[Dict[str, Any]]:
        """Use LLM to decide which tool to call and extract parameters"""
        try:
            prompt = f"""You must respond with ONLY valid JSON. No other text.

User request: "{user_text}"

Available tools:
{tool_descriptions}

If a tool matches the request, return:
{{"tool_name": "exact_tool_name", "parameters": {{"param1": "value1"}}}}

If no tool matches, return:
{{"tool_name": null, "parameters": {{}}}}

Response:"""
            
            response = await self._get_llm_response(prompt, max_tokens=300)
            
            # Debug: log what LLM returned
            logger.info(f"LLM tool decision response: {repr(response)}")
            
            # Extract JSON from response (handle cases where LLM adds extra text)
            import json
            import re
            
            # Try to find JSON in the response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                try:
                    decision = json.loads(json_str)
                except json.JSONDecodeError:
                    # If JSON is still invalid, return None to fall back to LLM
                    decision = {"tool_name": None, "parameters": {}}
            else:
                # If no JSON found, try parsing the whole response
                try:
                    decision = json.loads(response.strip())
                except json.JSONDecodeError:
                    decision = {"tool_name": None, "parameters": {}}
            
            return decision
            
        except Exception as e:
            logger.error(f"Failed to decide tool with LLM: {e}")
            return None
    
    def _get_tool_spec(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get tool specification from protocol.json"""
        if not self.mcp_client.protocol_info or "capabilities" not in self.mcp_client.protocol_info:
            return None
        
        tools = self.mcp_client.protocol_info["capabilities"].get("tools", [])
        for tool in tools:
            if tool["name"] == tool_name:
                return tool
        return None
    
    async def _get_llm_response(self, user_text: str, max_tokens: int = 1000) -> str:
        """Get response from LLM"""
        if not self.groq_client:
            return "I'm sorry, I can't generate a response right now."
        
        try:
            # Generate dynamic system prompt based on available tools
            available_tools = await self.mcp_client.get_available_tools()
            tool_descriptions = []
            
            for tool_name in available_tools:
                tool_spec = self._get_tool_spec(tool_name)
                if tool_spec:
                    description = tool_spec.get("description", f"{tool_name} tool")
                    tool_descriptions.append(f"- {tool_name}: {description}")
            
            tools_text = "\n".join(tool_descriptions) if tool_descriptions else "No tools available"
            
            system_prompt = (
                f"You are . Answer in 1-2 sentences only. No explanations, no reasoning, no asterisks, no brackets. "
                f"Just the direct answer. Always respond in English."
            )
            
            response = self.groq_client.chat.completions.create(
                model="qwen/qwen3-32b",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_text}
                ],
                temperature=0.7,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error getting LLM response: {e}")
            return f"I'm sorry, I couldn't generate a response: {str(e)}"


# Global MCP client instance
mcp_client_instance: Optional[SimpleMCPClient] = None
response_generator_instance: Optional[MCPResponseGenerator] = None

async def initialize_mcp():
    """Initialize MCP client and response generator"""
    global mcp_client_instance, response_generator_instance
    
    try:
        # Create MCP client for multiple servers
        mcp_client_instance = SimpleMCPClient()
        
        # Initialize MCP client
        success = await mcp_client_instance.initialize()
        
        if success:
            # Create response generator
            response_generator_instance = MCPResponseGenerator(mcp_client_instance)
            logger.info("MCP system initialized successfully")
            return True
        else:
            logger.error("Failed to initialize MCP client")
            return False
        
    except Exception as e:
        logger.error(f"Failed to initialize MCP: {e}")
        return False

async def get_enhanced_response(user_text: str) -> str:
    """Get response using MCP tools when appropriate"""
    global response_generator_instance
    
    if response_generator_instance:
        return await response_generator_instance.generate_response(user_text)
    else:
        # Fallback to basic LLM response (no MCP tools available)
        try:
            from groq import Groq
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                return "I'm sorry, I can't generate a response right now because GROQ_API_KEY is not configured."
            client = Groq(api_key=api_key)
            
            response = client.chat.completions.create(
                model="qwen/qwen3-32b",
                messages=[
                    {"role": "system", "content": "You are Kavach, built by GarudaSec Technologies. Answer in 1-2 sentences only. No explanations, no reasoning, no asterisks, no brackets. Just the direct answer. Always respond in English."},
                    {"role": "user", "content": user_text}
                ],
                temperature=0.7,
                max_tokens=512
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"I'm sorry, I couldn't generate a response: {str(e)}"

async def cleanup_mcp():
    """Cleanup MCP resources"""
    global mcp_client_instance, response_generator_instance
    
    mcp_client_instance = None
    response_generator_instance = None
    logger.info("MCP resources cleaned up")
