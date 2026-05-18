/**
 * Chatbot L0027 - Composant React
 * Statut Général des Agents de l'État de Guinée
 * 
 * Installation:
 * npm install
 * 
 * Usage:
 * import { ChatbotL0027, ChatbotButton, useChatbot } from './ChatbotL0027';
 * 
 * // Option 1: Composant complet avec bouton flottant
 * <ChatbotL0027 apiUrl="http://localhost:8000/api/v1" />
 * 
 * // Option 2: Bouton personnalisé
 * const { isOpen, toggle, askQuestion } = useChatbot();
 * <button onClick={toggle}>Ouvrir le chatbot</button>
 * 
 * // Option 3: Widget intégré (sans bouton flottant)
 * <ChatbotWidget apiUrl="..." embedded />
 */

import React, { useState, useRef, useEffect, useCallback, createContext, useContext } from 'react';

// ============================================
// Types
// ============================================

/**
 * @typedef {Object} Message
 * @property {string} id
 * @property {'user' | 'assistant'} role
 * @property {string} content
 * @property {SuggestedQuestion[]} [suggestions]
 * @property {boolean} [cached]
 * @property {string} [provider]
 */

/**
 * @typedef {Object} ArticleReference
 * @property {number} numero
 * @property {string} contenu
 * @property {string} [theme_principal]
 * @property {number} [score]
 */

/**
 * @typedef {Object} SuggestedQuestion
 * @property {string} question
 * @property {string} [category]
 */

// ============================================
// Context
// ============================================

const ChatbotContext = createContext(null);

export const useChatbot = () => {
    const context = useContext(ChatbotContext);
    if (!context) {
        throw new Error('useChatbot must be used within ChatbotProvider');
    }
    return context;
};

// ============================================
// Styles
// ============================================

const styles = {
    // Container
    container: {
        position: 'fixed',
        bottom: '20px',
        right: '20px',
        zIndex: 9999,
        fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
    },
    
    // Floating Button
    floatingButton: {
        width: '60px',
        height: '60px',
        borderRadius: '50%',
        background: 'linear-gradient(135deg, #1e40af, #1e3a8a)',
        border: 'none',
        cursor: 'pointer',
        boxShadow: '0 4px 15px rgba(0, 0, 0, 0.2)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        transition: 'all 0.3s ease',
    },
    
    // Chat Window
    chatWindow: {
        position: 'absolute',
        bottom: '75px',
        right: '0',
        width: '380px',
        height: '600px',
        maxHeight: 'calc(100vh - 100px)',
        background: 'white',
        borderRadius: '16px',
        boxShadow: '0 10px 40px rgba(0, 0, 0, 0.15)',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
    },
    
    // Header - Style officiel et professionnel
    header: {
        background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%)',
        color: 'white',
        padding: '18px 24px',
        display: 'flex',
        alignItems: 'center',
        gap: '14px',
        boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
        borderBottom: '3px solid #dc2626',
    },
    
    // Messages Container
    messagesContainer: {
        flex: 1,
        overflowY: 'auto',
        padding: '20px',
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
        backgroundColor: '#f8fafc',
    },
    
    // Message Bubble - Design professionnel
    messageBubble: {
        maxWidth: '80%',
        padding: '16px 20px',
        borderRadius: '18px',
        lineHeight: 1.65,
        fontSize: '15px',
        wordWrap: 'break-word',
        overflowWrap: 'break-word',
    },
    
    userMessage: {
        alignSelf: 'flex-end',
        background: 'linear-gradient(135deg, #1e40af, #1e3a8a)',
        color: 'white',
        borderBottomRightRadius: '4px',
        boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    },
    
    assistantMessage: {
        alignSelf: 'flex-start',
        background: 'white',
        color: '#1e293b',
        borderBottomLeftRadius: '4px',
        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        border: '1px solid #f1f5f9',
    },
    
    // Input Area
    inputArea: {
        padding: '16px 20px',
        background: 'white',
        borderTop: '1px solid #e2e8f0',
        display: 'flex',
        gap: '12px',
    },
    
    input: {
        flex: 1,
        padding: '12px 16px',
        border: '2px solid #e2e8f0',
        borderRadius: '12px',
        fontSize: '14px',
        outline: 'none',
        resize: 'none',
        fontFamily: 'inherit',
    },
    
    sendButton: {
        width: '48px',
        height: '48px',
        background: '#1e40af',
        color: 'white',
        border: 'none',
        borderRadius: '12px',
        cursor: 'pointer',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
    },
    
    // Suggestions - Design professionnel
    suggestion: {
        display: 'block',
        width: '100%',
        textAlign: 'left',
        padding: '12px 16px',
        margin: '8px 0',
        background: '#f8fafc',
        border: '1.5px solid #e2e8f0',
        borderRadius: '10px',
        cursor: 'pointer',
        fontSize: '14px',
        color: '#1e293b',
        transition: 'all 0.3s ease',
        fontWeight: 500,
    },
    
    // Article Badge
    articleBadge: {
        display: 'inline-block',
        background: '#f8fafc',
        color: '#1e40af',
        padding: '4px 10px',
        borderRadius: '12px',
        fontSize: '12px',
        margin: '2px',
        cursor: 'pointer',
        border: '1px solid #e2e8f0',
    },
    
    // Typing Indicator
    typingIndicator: {
        display: 'flex',
        gap: '4px',
        padding: '12px 16px',
        background: 'white',
        borderRadius: '16px',
        width: 'fit-content',
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)',
    },
    
    typingDot: {
        width: '8px',
        height: '8px',
        background: '#64748b',
        borderRadius: '50%',
    },
};

// ============================================
// Components
// ============================================

// Message Component
const Message = ({ message, onSuggestionClick, onArticleClick }) => {
    const isUser = message.role === 'user';
    
    return (
        <div style={{
            ...styles.messageBubble,
            ...(isUser ? styles.userMessage : styles.assistantMessage),
        }}>
            <div dangerouslySetInnerHTML={{ __html: formatText(message.content) }} />
            
            {/* Suggestions uniquement (pas de confidence ni articles_references) */}
            {message.suggestions && message.suggestions.length > 0 && (
                <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid #f1f5f9' }}>
                    <div style={{ fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.5px', color: '#64748b', marginBottom: '12px', fontWeight: 600 }}>
                        Questions connexes
                    </div>
                    {message.suggestions.map((s, idx) => (
                        <button
                            key={idx}
                            style={styles.suggestion}
                            onClick={() => onSuggestionClick?.(s.question)}
                        >
                            {s.question}
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
};

// Typing Indicator
const TypingIndicator = () => (
    <div style={styles.typingIndicator}>
        <span style={{ ...styles.typingDot, animation: 'bounce 1.4s infinite ease-in-out -0.32s' }} />
        <span style={{ ...styles.typingDot, animation: 'bounce 1.4s infinite ease-in-out -0.16s' }} />
        <span style={{ ...styles.typingDot, animation: 'bounce 1.4s infinite ease-in-out' }} />
    </div>
);

// Chat Widget Component
export const ChatbotWidget = ({ 
    apiUrl = 'http://localhost:8000/api/v1',
    embedded = false,
    onClose,
    sessionId: externalSessionId,
    style: customStyle = {}
}) => {
    const [messages, setMessages] = useState([]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [starterQuestions, setStarterQuestions] = useState([]);
    const [sessionId] = useState(externalSessionId || generateSessionId());
    const messagesEndRef = useRef(null);
    const inputRef = useRef(null);

    // Load starter questions
    useEffect(() => {
        fetchStarterQuestions();
    }, [apiUrl]);

    // Scroll to bottom
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const fetchStarterQuestions = async () => {
        try {
            const response = await fetch(`${apiUrl}/suggestions/starter`);
            const data = await response.json();
            setStarterQuestions(data.slice(0, 4));
        } catch (error) {
            console.error('Error loading starter questions:', error);
            setStarterQuestions([
                { question: "Qu'est-ce qu'un agent de l'État ?" },
                { question: "Quel est l'âge de la retraite ?" },
                { question: "Comment fonctionne l'avancement ?" },
            ]);
        }
    };

    const sendMessage = async (question) => {
        if (!question.trim() || isLoading) return;

        const userMessage = {
            id: Date.now().toString(),
            role: 'user',
            content: question.trim(),
        };

        setMessages(prev => [...prev, userMessage]);
        setInputValue('');
        setIsLoading(true);

        try {
            const response = await fetch(`${apiUrl}/ask`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question: question.trim(),
                    session_id: sessionId,
                    include_suggestions: true,
                }),
            });

            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const data = await response.json();

            const assistantMessage = {
                id: data.response_id,
                role: 'assistant',
                content: data.answer,
                suggestions: data.suggested_questions,
                // Suppression de articles_references, confidence, processingTime, cached, provider
            };

            setMessages(prev => [...prev, assistantMessage]);
        } catch (error) {
            console.error('Error:', error);
            setMessages(prev => [...prev, {
                id: Date.now().toString(),
                role: 'assistant',
                content: "Désolé, une erreur s'est produite. Veuillez réessayer.",
            }]);
        } finally {
            setIsLoading(false);
            inputRef.current?.focus();
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage(inputValue);
        }
    };

    const handleArticleClick = async (article) => {
        try {
            const response = await fetch(`${apiUrl}/articles/${article.numero}`);
            const data = await response.json();
            alert(`Article ${data.numero}\n\n${data.contenu}\n\nThème: ${data.theme_principal}`);
        } catch (error) {
            console.error('Error:', error);
        }
    };

    return (
        <div style={{ ...styles.chatWindow, ...(embedded ? { position: 'relative', bottom: 0 } : {}), ...customStyle }}>
            {/* Header */}
            <div style={styles.header}>
                <span style={{ fontSize: '28px' }}>🇬🇳</span>
                <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '18px', fontWeight: 700 }}>Fomba</div>
                    <div style={{ fontSize: '13px', opacity: 0.9 }}>Assistant pour la Loi L/2019/0027/AN - Statut des Agents de l'État</div>
                </div>
                {onClose && (
                    <button
                        onClick={onClose}
                        style={{
                            background: 'rgba(255,255,255,0.2)',
                            border: 'none',
                            color: 'white',
                            width: '30px',
                            height: '30px',
                            borderRadius: '50%',
                            cursor: 'pointer',
                        }}
                    >
                        ✕
                    </button>
                )}
            </div>

            {/* Messages */}
            <div style={styles.messagesContainer}>
                {messages.length === 0 && (
                    <div style={{ textAlign: 'center', padding: '30px' }}>
                        <div style={{ fontSize: '48px', marginBottom: '16px' }}>⚖️</div>
                        <h2 style={{ fontSize: '18px', marginBottom: '8px' }}>Bienvenue !</h2>
                        <p style={{ fontSize: '14px', color: '#64748b', marginBottom: '20px' }}>
                            Je suis votre assistant pour comprendre le Statut des Agents de l'État.
                        </p>
                        <div>
                            {starterQuestions.map((q, idx) => (
                                <button
                                    key={idx}
                                    style={{ ...styles.suggestion, marginBottom: '8px' }}
                                    onClick={() => sendMessage(q.question)}
                                >
                                    💡 {q.question}
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                {messages.map((msg) => (
                    <Message
                        key={msg.id}
                        message={msg}
                        onSuggestionClick={sendMessage}
                        onArticleClick={handleArticleClick}
                    />
                ))}

                {isLoading && <TypingIndicator />}
                <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div style={styles.inputArea}>
                <textarea
                    ref={inputRef}
                    style={styles.input}
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Posez votre question..."
                    rows={1}
                    disabled={isLoading}
                />
                <button
                    style={{
                        ...styles.sendButton,
                        opacity: isLoading ? 0.5 : 1,
                        cursor: isLoading ? 'not-allowed' : 'pointer',
                    }}
                    onClick={() => sendMessage(inputValue)}
                    disabled={isLoading}
                >
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
                    </svg>
                </button>
            </div>
        </div>
    );
};

// Floating Button Component
export const ChatbotButton = ({ onClick, isOpen }) => (
    <button
        style={{
            ...styles.floatingButton,
            transform: isOpen ? 'rotate(180deg)' : 'none',
        }}
        onClick={onClick}
    >
        <svg width="28" height="28" viewBox="0 0 24 24" fill="white">
            <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z" />
        </svg>
    </button>
);

// Main Chatbot Component (with floating button)
export const ChatbotL0027 = ({ 
    apiUrl = 'http://localhost:8000/api/v1',
    position = 'bottom-right',
    defaultOpen = false,
}) => {
    const [isOpen, setIsOpen] = useState(defaultOpen);

    const containerStyle = {
        ...styles.container,
        ...(position === 'bottom-left' ? { right: 'auto', left: '20px' } : {}),
    };

    return (
        <ChatbotContext.Provider value={{ isOpen, setIsOpen, toggle: () => setIsOpen(!isOpen) }}>
            <div style={containerStyle}>
                {isOpen && (
                    <ChatbotWidget
                        apiUrl={apiUrl}
                        onClose={() => setIsOpen(false)}
                    />
                )}
                <ChatbotButton
                    onClick={() => setIsOpen(!isOpen)}
                    isOpen={isOpen}
                />
            </div>
            
            {/* Global styles for animations */}
            <style>{`
                @keyframes bounce {
                    0%, 80%, 100% { transform: scale(0); }
                    40% { transform: scale(1); }
                }
            `}</style>
        </ChatbotContext.Provider>
    );
};

// Provider for custom implementations
export const ChatbotProvider = ({ children, apiUrl }) => {
    const [isOpen, setIsOpen] = useState(false);
    
    const askQuestion = useCallback((question) => {
        // This would need a ref to the widget or state management
        console.log('Ask question:', question);
    }, []);

    return (
        <ChatbotContext.Provider value={{
            isOpen,
            setIsOpen,
            toggle: () => setIsOpen(!isOpen),
            open: () => setIsOpen(true),
            close: () => setIsOpen(false),
            askQuestion,
            apiUrl,
        }}>
            {children}
        </ChatbotContext.Provider>
    );
};

// Utility functions
function generateSessionId() {
    return 'session_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
}

function formatText(text) {
    if (!text) return '';
    
    // Formatage markdown amélioré pour un rendu professionnel et étatique
    let formatted = text
        // Headers
        .replace(/^### (.*$)/gim, '<h3>$1</h3>')
        .replace(/^## (.*$)/gim, '<h2>$1</h2>')
        .replace(/^# (.*$)/gim, '<h1>$1</h1>')
        // Gras
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/__(.*?)__/g, '<strong>$1</strong>')
        // Italique
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/_(.*?)_/g, '<em>$1</em>')
        // Code inline
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        // Blockquote
        .replace(/^> (.*$)/gim, '<blockquote>$1</blockquote>')
        // Listes numérotées
        .replace(/^\d+\.\s+(.+)$/gm, '<li>$1</li>')
        // Listes à puces
        .replace(/^[-•*]\s+(.+)$/gm, '<li>$1</li>')
        // Ligne horizontale
        .replace(/^---+$/gm, '<hr>')
        // Saut de ligne double = nouveau paragraphe
        .replace(/\n\n+/g, '</p><p>')
        // Saut de ligne simple = <br>
        .replace(/\n/g, '<br>');

    // Encapsuler les listes
    formatted = formatted.replace(/(<li>.*<\/li>)/s, function(match) {
        if (/^\d+\./.test(match)) {
            return '<ol>' + match + '</ol>';
        }
        return '<ul>' + match + '</ul>';
    });

    // Encapsuler dans des paragraphes si nécessaire
    if (!formatted.startsWith('<')) {
        formatted = '<p>' + formatted;
    }
    if (!formatted.endsWith('>')) {
        formatted = formatted + '</p>';
    }

    // Nettoyer les balises vides
    formatted = formatted
        .replace(/<p><\/p>/g, '')
        .replace(/<p>(<[^>]+>)/g, '$1')
        .replace(/(<\/[^>]+>)<\/p>/g, '$1')
        .replace(/<p><p>/g, '<p>')
        .replace(/<\/p><\/p>/g, '</p>')
        .replace(/<ul><\/ul>/g, '')
        .replace(/<ol><\/ol>/g, '')
        .replace(/<p>(<[uo]l>)/g, '$1')
        .replace(/(<\/[uo]l>)<\/p>/g, '$1');

    return formatted;
}

// Default export
export default ChatbotL0027;
