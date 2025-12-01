from mcp.server.fastmcp import FastMCP

mcp = FastMCP("NewSampleServer")

@mcp.tool()
def calculate(expression: str) -> str:
    """Calculate mathematical expressions safely"""
    try:
        # Simple safe evaluation for basic math
        allowed_chars = set('0123456789+-*/.() ')
        if not all(c in allowed_chars for c in expression):
            return "Error: Only basic math operations allowed"
        
        result = eval(expression)
        return f"The result of {expression} is {result}"
    except Exception as e:
        return f"Error calculating {expression}: {str(e)}"

@mcp.tool()
def weather(city: str) -> str:
    """Get weather information for a city"""
    # Mock weather data - in real implementation, you'd call a weather API
    weather_data = {
        "mumbai": "Sunny, 28°C",
        "delhi": "Partly cloudy, 25°C", 
        "bangalore": "Rainy, 22°C",
        "chennai": "Hot, 32°C",
        "kolkata": "Humid, 30°C"
    }
    
    city_lower = city.lower()
    if city_lower in weather_data:
        return f"Weather in {city}: {weather_data[city_lower]}"
    else:
        return f"Weather data not available for {city}. Available cities: {', '.join(weather_data.keys())}"

@mcp.tool()
def translate(text: str, target_language: str) -> str:
    """Translate text to target language"""
    # Mock translation - in real implementation, you'd use a translation API
    translations = {
        "hindi": {
            "hello": "नमस्ते",
            "how are you": "आप कैसे हैं",
            "thank you": "धन्यवाद",
            "good morning": "सुप्रभात"
        },
        "spanish": {
            "hello": "hola",
            "how are you": "¿cómo estás",
            "thank you": "gracias", 
            "good morning": "buenos días"
        },
        "french": {
            "hello": "bonjour",
            "how are you": "comment allez-vous",
            "thank you": "merci",
            "good morning": "bonjour"
        }
    }
    
    text_lower = text.lower()
    target_lower = target_language.lower()
    
    if target_lower in translations and text_lower in translations[target_lower]:
        return f"'{text}' in {target_language}: {translations[target_lower][text_lower]}"
    else:
        available_languages = list(translations.keys())
        return f"Translation not available. Available languages: {', '.join(available_languages)}"


@mcp.tool()
def what_kavach_can_do() -> str:
    """this function just simply return what kavach can do"""
    return "I can perform a wide range of tasks, such as managing user role changes in Kavach and many other operations. I can also help you with your questions and day-to-day tasks. Moreover, I can automate the manual processes you perform — simply by having a conversation with you. I am an advanced AI assistant developed by Garudasec Technologies."



if __name__ == "__main__":
    mcp.run(transport="stdio")
