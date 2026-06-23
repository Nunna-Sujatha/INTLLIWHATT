import { useState, useRef, useEffect } from 'react';
import {
    Send,
    Bot,
    User,
    Lightbulb,
    Wallet,
    Trash2,
    Loader2
} from 'lucide-react';
import { chatApi } from '../services/api';

const Chatbot = () => {
    const [messages, setMessages] = useState([
        {
            role: 'assistant',
            content: "Hello! I'm your AI energy assistant. I can help you with:\n\n• Energy-saving tips\n• Budget-based guidance\n• Appliance usage optimization\n• Understanding your electricity bill\n\nHow can I help you today?"
        }
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [conversationId, setConversationId] = useState(null);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = async () => {
        if (!input.trim() || loading) return;

        const userMessage = input.trim();
        setInput('');
        setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
        setLoading(true);

        try {
            const response = await chatApi.sendMessage(userMessage, conversationId);
            setConversationId(response.conversation_id);
            setMessages(prev => [...prev, { role: 'assistant', content: response.response }]);
        } catch (error) {
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: 'Sorry, I encountered an error. Please try again.'
            }]);
        } finally {
            setLoading(false);
        }
    };

    const handleBudgetGuidance = async () => {
        const budget = prompt('Enter your target monthly budget (₹):');
        if (!budget) return;

        setMessages(prev => [...prev, {
            role: 'user',
            content: `Help me keep my electricity bill under ₹${budget}`
        }]);
        setLoading(true);

        try {
            const response = await chatApi.getBudgetGuidance(parseFloat(budget));
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: response.guidance
            }]);
        } catch (error) {
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: 'Sorry, I encountered an error getting budget guidance.'
            }]);
        } finally {
            setLoading(false);
        }
    };

    const handleGetTips = async (category) => {
        setMessages(prev => [...prev, {
            role: 'user',
            content: `Give me ${category || 'general'} energy-saving tips`
        }]);
        setLoading(true);

        try {
            const response = await chatApi.getTips(category);
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: response.tips
            }]);
        } catch (error) {
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: 'Sorry, I encountered an error getting tips.'
            }]);
        } finally {
            setLoading(false);
        }
    };

    const handleClearChat = async () => {
        if (confirm('Clear all chat history?')) {
            await chatApi.clear();
            setMessages([{
                role: 'assistant',
                content: "Chat cleared! How can I help you today?"
            }]);
            setConversationId(null);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const quickActions = [
        { label: '💡 Energy Tips', action: () => handleGetTips() },
        { label: '❄️ AC Tips', action: () => handleGetTips('cooling') },
        { label: '💰 Budget Help', action: handleBudgetGuidance },
        {
            label: '📊 Analyze Usage', action: async () => {
                setLoading(true);
                setMessages(prev => [...prev, { role: 'user', content: 'Analyze my electricity usage' }]);
                try {
                    const response = await chatApi.analyzeUsage();
                    setMessages(prev => [...prev, { role: 'assistant', content: response.analysis }]);
                } catch (error) {
                    setMessages(prev => [...prev, { role: 'assistant', content: 'Error analyzing usage.' }]);
                }
                setLoading(false);
            }
        },
    ];

    return (
        <div className="h-[calc(100vh-120px)] flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
                <div>
                    <h1 className="text-3xl font-bold">AI Energy Assistant</h1>
                    <p className="text-text-secondary mt-1">
                        Get personalized energy-saving advice and budget guidance
                    </p>
                </div>
                <button
                    onClick={handleClearChat}
                    className="btn-secondary flex items-center gap-2"
                >
                    <Trash2 size={18} />
                    Clear Chat
                </button>
            </div>

            {/* Quick Actions */}
            <div className="flex gap-2 mb-4 flex-wrap">
                {quickActions.map((action, index) => (
                    <button
                        key={index}
                        onClick={action.action}
                        disabled={loading}
                        className="px-4 py-2 rounded-full bg-surface border border-border hover:border-primary transition-all text-sm"
                    >
                        {action.label}
                    </button>
                ))}
            </div>

            {/* Chat Container */}
            <div className="glass-card flex-1 flex flex-col overflow-hidden">
                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                    {messages.map((message, index) => (
                        <div
                            key={index}
                            className={`flex items-start gap-3 ${message.role === 'user' ? 'flex-row-reverse' : ''
                                }`}
                        >
                            <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${message.role === 'user'
                                    ? 'gradient-primary'
                                    : 'gradient-accent'
                                }`}>
                                {message.role === 'user' ? (
                                    <User size={20} className="text-white" />
                                ) : (
                                    <Bot size={20} className="text-white" />
                                )}
                            </div>
                            <div className={`chat-message ${message.role}`}>
                                <div className="whitespace-pre-wrap">{message.content}</div>
                            </div>
                        </div>
                    ))}

                    {loading && (
                        <div className="flex items-start gap-3">
                            <div className="w-10 h-10 rounded-full gradient-accent flex items-center justify-center">
                                <Bot size={20} className="text-white" />
                            </div>
                            <div className="chat-message assistant">
                                <Loader2 className="animate-spin" size={20} />
                            </div>
                        </div>
                    )}

                    <div ref={messagesEndRef} />
                </div>

                {/* Input Area */}
                <div className="p-4 border-t border-border">
                    <div className="flex gap-3">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyPress={handleKeyPress}
                            placeholder="Ask me anything about electricity usage..."
                            className="input-field flex-1"
                            disabled={loading}
                        />
                        <button
                            onClick={handleSend}
                            disabled={loading || !input.trim()}
                            className="btn-primary px-6"
                        >
                            <Send size={20} />
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Chatbot;
