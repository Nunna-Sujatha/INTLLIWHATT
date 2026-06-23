"""Chatbot service using OpenRouter API."""

import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODEL
from services.data_service import add_chat_message, get_latest_conversation, get_appliances


def get_system_prompt() -> str:
    """Get the system prompt for the chatbot."""
    return """You are an AI assistant specialized in electricity consumption and bill management. 
Your role is to help users:
1. Understand their electricity usage patterns
2. Provide energy-saving tips and recommendations
3. Answer questions about electricity billing
4. Help with budget-based guidance for electricity consumption
5. Explain appliance power consumption

Be helpful, concise, and provide practical advice. When discussing costs, use Indian Rupees (₹).
Always encourage energy-efficient practices."""


def get_budget_prompt(budget: float, current_usage: float, days_remaining: int, appliances: List[Dict]) -> str:
    """Get prompt for budget-based guidance."""
    appliance_summary = "\n".join([
        f"- {a['name']}: {a['power_rating']}W, {a.get('quantity', 1)} unit(s), ~{a.get('average_daily_hours', 0)} hours/day"
        for a in appliances
    ])
    
    return f"""The user wants to keep their electricity bill under ₹{budget}.
    
Current estimated usage: ₹{current_usage:.2f}
Days remaining in billing cycle: {days_remaining}
Daily budget remaining: ₹{(budget - current_usage) / max(days_remaining, 1):.2f}

Current appliances:
{appliance_summary}

Please provide specific, actionable recommendations to help them stay within budget. 
Include:
1. Which appliances to reduce usage on
2. Optimal usage hours for each appliance
3. Estimated savings from each recommendation
4. Priority actions (what will save the most)"""


def call_openrouter(messages: List[Dict], max_tokens: int = 1000) -> Dict:
    """Make a call to OpenRouter API."""
    if not OPENROUTER_API_KEY:
        return {
            "status": "error",
            "message": "OpenRouter API key not configured"
        }
    
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5173",
            "X-Title": "Electricity Bill Predictor"
        }
        
        payload = {
            "model": OPENROUTER_MODEL,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.7
        }
        
        response = requests.post(
            OPENROUTER_BASE_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                "status": "success",
                "content": result["choices"][0]["message"]["content"],
                "model": result.get("model", OPENROUTER_MODEL)
            }
        else:
            return {
                "status": "error",
                "message": f"API error: {response.status_code} - {response.text}"
            }
    
    except requests.exceptions.Timeout:
        return {"status": "error", "message": "Request timed out"}
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": f"Request error: {str(e)}"}
    except Exception as e:
        return {"status": "error", "message": f"Unexpected error: {str(e)}"}


def send_message(user_message: str, conversation_id: Optional[str] = None) -> Dict:
    """Send a message and get AI response."""
    # Get conversation context
    conversation = get_latest_conversation() if not conversation_id else None
    
    # Build messages list
    messages = [{"role": "system", "content": get_system_prompt()}]
    
    # Add conversation history (last 10 messages for context)
    if conversation:
        for msg in conversation.get("messages", [])[-10:]:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
    
    # Add current message
    messages.append({"role": "user", "content": user_message})
    
    # Call OpenRouter
    response = call_openrouter(messages)
    
    if response["status"] == "success":
        # Save messages to history
        saved_user = add_chat_message(conversation_id, "user", user_message)
        saved_assistant = add_chat_message(
            saved_user["conversation_id"], 
            "assistant", 
            response["content"]
        )
        
        return {
            "status": "success",
            "response": response["content"],
            "conversation_id": saved_user["conversation_id"]
        }
    
    return response


def get_budget_guidance(budget: float, current_usage: float = 0, days_in_cycle: int = 30) -> Dict:
    """Get budget-based guidance from AI."""
    # Calculate days remaining
    today = datetime.now()
    days_passed = today.day
    days_remaining = days_in_cycle - days_passed
    
    # Get current appliances
    appliances = get_appliances()
    
    # Calculate estimated current usage if not provided
    if current_usage == 0:
        # Simple estimation based on appliances
        for app in appliances:
            power_w = app.get('power_rating', 0)
            hours = app.get('average_daily_hours', 0)
            quantity = app.get('quantity', 1)
            daily_kwh = (power_w * hours * quantity) / 1000
            daily_cost = daily_kwh * 8  # Assuming ₹8/kWh average
            current_usage += daily_cost * days_passed
    
    # Build budget guidance prompt
    budget_prompt = get_budget_prompt(budget, current_usage, days_remaining, appliances)
    
    messages = [
        {"role": "system", "content": get_system_prompt()},
        {"role": "user", "content": budget_prompt}
    ]
    
    response = call_openrouter(messages, max_tokens=1500)
    
    if response["status"] == "success":
        # Save to chat history
        add_chat_message(None, "user", f"Help me stay under ₹{budget} budget")
        add_chat_message(None, "assistant", response["content"])
        
        return {
            "status": "success",
            "guidance": response["content"],
            "budget_info": {
                "target_budget": budget,
                "current_estimated_usage": round(current_usage, 2),
                "days_remaining": days_remaining,
                "daily_budget_remaining": round((budget - current_usage) / max(days_remaining, 1), 2)
            }
        }
    
    return response


def get_energy_tips(category: Optional[str] = None) -> Dict:
    """Get energy-saving tips."""
    categories = {
        "cooling": "tips for reducing air conditioner electricity consumption",
        "lighting": "tips for efficient lighting usage",
        "appliances": "general tips for reducing appliance electricity consumption",
        "peak_hours": "tips for shifting usage to off-peak hours",
        "maintenance": "appliance maintenance tips for energy efficiency"
    }
    
    if category and category in categories:
        topic = categories[category]
    else:
        topic = "top 5 practical electricity saving tips for Indian households"
    
    messages = [
        {"role": "system", "content": get_system_prompt()},
        {"role": "user", "content": f"Give me {topic}. Be specific and practical."}
    ]
    
    response = call_openrouter(messages, max_tokens=800)
    
    if response["status"] == "success":
        return {
            "status": "success",
            "tips": response["content"],
            "category": category or "general"
        }
    
    return response


def analyze_usage_pattern(appliances: List[Dict], historical_data: List[Dict] = None) -> Dict:
    """Analyze usage patterns and provide insights."""
    appliance_summary = "\n".join([
        f"- {a['name']}: {a.get('power_rating', 0)}W, used {a.get('average_daily_hours', 0)} hours/day"
        for a in appliances
    ])
    
    history_summary = ""
    if historical_data:
        avg_bill = sum(h.get('total_bill', 0) for h in historical_data) / len(historical_data)
        history_summary = f"\nAverage monthly bill: ₹{avg_bill:.2f}"
    
    prompt = f"""Analyze this household's electricity usage pattern and provide insights:

Appliances:
{appliance_summary}
{history_summary}

Provide:
1. Which appliances are consuming the most electricity
2. Patterns that could be optimized
3. Comparison with typical Indian household usage
4. Specific recommendations for this household"""

    messages = [
        {"role": "system", "content": get_system_prompt()},
        {"role": "user", "content": prompt}
    ]
    
    response = call_openrouter(messages, max_tokens=1000)
    
    if response["status"] == "success":
        return {
            "status": "success",
            "analysis": response["content"]
        }
    
    return response
