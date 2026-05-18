/**
 * Chatbot L0027 - Script d'intégration
 * Statut Général des Agents de l'État de Guinée
 * 
 * Usage:
 * <script src="https://votre-domaine.com/chatbot/embed.js" 
 *         data-api-url="https://api.votre-domaine.com/api/v1"
 *         data-position="bottom-right"
 *         data-theme="blue">
 * </script>
 */

(function() {
    'use strict';

    // Configuration par défaut
    const DEFAULT_CONFIG = {
        apiUrl: 'http://localhost:8000/api/v1',
        position: 'bottom-right', // bottom-right, bottom-left
        theme: 'blue', // blue, green, dark
        width: '380px',
        height: '600px',
        buttonSize: '60px',
        zIndex: 9999,
        locale: 'fr'
    };

    // Récupérer la configuration depuis les attributs data-*
    function getConfig() {
        const script = document.currentScript || document.querySelector('script[data-api-url]');
        const config = { ...DEFAULT_CONFIG };

        if (script) {
            config.apiUrl = script.getAttribute('data-api-url') || config.apiUrl;
            config.position = script.getAttribute('data-position') || config.position;
            config.theme = script.getAttribute('data-theme') || config.theme;
            config.width = script.getAttribute('data-width') || config.width;
            config.height = script.getAttribute('data-height') || config.height;
        }

        return config;
    }

    // Thèmes de couleurs
    const THEMES = {
        blue: {
            primary: '#1e40af',
            primaryDark: '#1e3a8a',
            primaryLight: '#3b82f6'
        },
        green: {
            primary: '#059669',
            primaryDark: '#047857',
            primaryLight: '#10b981'
        },
        dark: {
            primary: '#374151',
            primaryDark: '#1f2937',
            primaryLight: '#6b7280'
        }
    };

    // Styles CSS
    function getStyles(config) {
        const theme = THEMES[config.theme] || THEMES.blue;
        const isRight = config.position === 'bottom-right';

        return `
            #chatbot-l0027-container {
                position: fixed;
                bottom: 20px;
                ${isRight ? 'right: 20px;' : 'left: 20px;'}
                z-index: ${config.zIndex};
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }

            #chatbot-l0027-button {
                width: ${config.buttonSize};
                height: ${config.buttonSize};
                border-radius: 50%;
                background: linear-gradient(135deg, ${theme.primary}, ${theme.primaryDark});
                border: none;
                cursor: pointer;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.3s ease;
                position: relative;
            }

            #chatbot-l0027-button:hover {
                transform: scale(1.1);
                box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
            }

            #chatbot-l0027-button svg {
                width: 28px;
                height: 28px;
                fill: white;
                transition: transform 0.3s ease;
            }

            #chatbot-l0027-button.open svg {
                transform: rotate(180deg);
            }

            #chatbot-l0027-button .notification-badge {
                position: absolute;
                top: -5px;
                right: -5px;
                width: 20px;
                height: 20px;
                background: #ef4444;
                border-radius: 50%;
                color: white;
                font-size: 12px;
                display: flex;
                align-items: center;
                justify-content: center;
                animation: pulse 2s infinite;
            }

            @keyframes pulse {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.1); }
            }

            #chatbot-l0027-window {
                position: absolute;
                bottom: calc(${config.buttonSize} + 15px);
                ${isRight ? 'right: 0;' : 'left: 0;'}
                width: ${config.width};
                height: ${config.height};
                max-height: calc(100vh - 100px);
                background: white;
                border-radius: 16px;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
                overflow: hidden;
                opacity: 0;
                transform: translateY(20px) scale(0.95);
                transition: all 0.3s ease;
                pointer-events: none;
            }

            #chatbot-l0027-window.open {
                opacity: 1;
                transform: translateY(0) scale(1);
                pointer-events: auto;
            }

            #chatbot-l0027-window iframe {
                width: 100%;
                height: 100%;
                border: none;
            }

            #chatbot-l0027-close {
                position: absolute;
                top: 10px;
                right: 10px;
                width: 30px;
                height: 30px;
                background: rgba(255, 255, 255, 0.9);
                border: none;
                border-radius: 50%;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 10;
                transition: all 0.2s;
            }

            #chatbot-l0027-close:hover {
                background: white;
                transform: scale(1.1);
            }

            #chatbot-l0027-close svg {
                width: 16px;
                height: 16px;
                fill: #64748b;
            }

            /* Responsive */
            @media (max-width: 480px) {
                #chatbot-l0027-window {
                    width: calc(100vw - 40px);
                    height: calc(100vh - 100px);
                    bottom: calc(${config.buttonSize} + 10px);
                    ${isRight ? 'right: 0;' : 'left: 0;'}
                    border-radius: 12px;
                }

                #chatbot-l0027-container {
                    bottom: 15px;
                    ${isRight ? 'right: 15px;' : 'left: 15px;'}
                }
            }

            /* Animation d'entrée */
            #chatbot-l0027-container.loaded #chatbot-l0027-button {
                animation: bounceIn 0.6s ease;
            }

            @keyframes bounceIn {
                0% { transform: scale(0); }
                50% { transform: scale(1.2); }
                100% { transform: scale(1); }
            }
        `;
    }

    // HTML du widget
    function getHTML(config) {
        return `
            <div id="chatbot-l0027-container">
                <div id="chatbot-l0027-window">
                    <button id="chatbot-l0027-close" title="Fermer">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                            <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                        </svg>
                    </button>
                    <iframe 
                        id="chatbot-l0027-iframe"
                        src="${getWidgetUrl(config)}"
                        title="Fomba - Assistant Fonction Publique Guinée"
                        loading="lazy"
                    ></iframe>
                </div>
                <button id="chatbot-l0027-button" title="Ouvrir Fomba - Assistant Fonction Publique">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                        <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/>
                    </svg>
                    <span class="notification-badge" style="display: none;">1</span>
                </button>
            </div>
        `;
    }

    // Construire l'URL du widget
    function getWidgetUrl(config) {
        // Option 1: Widget hébergé sur le même serveur que l'API
        // return `${config.apiUrl.replace('/api/v1', '')}/widget.html`;
        
        // Option 2: Widget inline (data URL) - pour éviter les problèmes CORS
        // Vous pouvez aussi servir widget.html depuis votre serveur
        const widgetUrl = config.apiUrl.replace('/api/v1', '') + '/static/widget.html';
        return widgetUrl + '?api=' + encodeURIComponent(config.apiUrl);
    }

    // Initialisation
    function init() {
        const config = getConfig();

        // Injecter les styles
        const style = document.createElement('style');
        style.textContent = getStyles(config);
        document.head.appendChild(style);

        // Injecter le HTML
        const container = document.createElement('div');
        container.innerHTML = getHTML(config);
        document.body.appendChild(container.firstElementChild);

        // Récupérer les éléments
        const chatbotContainer = document.getElementById('chatbot-l0027-container');
        const chatbotButton = document.getElementById('chatbot-l0027-button');
        const chatbotWindow = document.getElementById('chatbot-l0027-window');
        const chatbotClose = document.getElementById('chatbot-l0027-close');
        const chatbotIframe = document.getElementById('chatbot-l0027-iframe');

        // État
        let isOpen = false;

        // Ouvrir/Fermer
        function toggle() {
            isOpen = !isOpen;
            chatbotWindow.classList.toggle('open', isOpen);
            chatbotButton.classList.toggle('open', isOpen);
            
            // Focus sur l'iframe quand ouvert
            if (isOpen && chatbotIframe.contentWindow) {
                chatbotIframe.contentWindow.focus();
            }
        }

        function close() {
            isOpen = false;
            chatbotWindow.classList.remove('open');
            chatbotButton.classList.remove('open');
        }

        // Event listeners
        chatbotButton.addEventListener('click', toggle);
        chatbotClose.addEventListener('click', close);

        // Fermer avec Echap
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && isOpen) {
                close();
            }
        });

        // Fermer en cliquant en dehors
        document.addEventListener('click', (e) => {
            if (isOpen && !chatbotContainer.contains(e.target)) {
                close();
            }
        });

        // Communication avec l'iframe
        window.addEventListener('message', (event) => {
            // Vérifier l'origine si nécessaire
            if (event.data.type === 'chatbot-l0027-close') {
                close();
            }
            if (event.data.type === 'chatbot-l0027-notification') {
                const badge = chatbotButton.querySelector('.notification-badge');
                if (badge) {
                    badge.style.display = 'flex';
                    badge.textContent = event.data.count || '1';
                }
            }
        });

        // Passer la config API à l'iframe
        chatbotIframe.addEventListener('load', () => {
            chatbotIframe.contentWindow.postMessage({
                type: 'chatbot-l0027-config',
                apiUrl: config.apiUrl
            }, '*');
            
            // Injecter l'URL de l'API dans l'iframe
            if (chatbotIframe.contentWindow.ChatbotL0027) {
                chatbotIframe.contentWindow.ChatbotL0027.setApiUrl(config.apiUrl);
            }
        });

        // Animation d'entrée
        setTimeout(() => {
            chatbotContainer.classList.add('loaded');
        }, 100);

        // API publique
        window.ChatbotL0027 = {
            open: () => { if (!isOpen) toggle(); },
            close: close,
            toggle: toggle,
            isOpen: () => isOpen,
            setApiUrl: (url) => {
                config.apiUrl = url;
                if (chatbotIframe.contentWindow.ChatbotL0027) {
                    chatbotIframe.contentWindow.ChatbotL0027.setApiUrl(url);
                }
            },
            askQuestion: (question) => {
                if (!isOpen) toggle();
                setTimeout(() => {
                    if (chatbotIframe.contentWindow.ChatbotL0027) {
                        chatbotIframe.contentWindow.ChatbotL0027.askQuestion(question);
                    }
                }, 500);
            }
        };

        console.log('🇬🇳 Chatbot L0027 initialisé');
    }

    // Démarrer quand le DOM est prêt
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
