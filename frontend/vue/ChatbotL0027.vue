<!--
  Chatbot L0027 - Composant Vue.js
  Statut Général des Agents de l'État de Guinée
  
  Usage:
  <template>
    <ChatbotL0027 api-url="http://localhost:8000/api/v1" />
  </template>
  
  <script>
  import ChatbotL0027 from './ChatbotL0027.vue';
  export default {
    components: { ChatbotL0027 }
  }
  </script>
-->

<template>
  <div class="chatbot-container" :class="{ 'position-left': position === 'bottom-left' }">
    <!-- Chat Window -->
    <Transition name="slide-up">
      <div v-if="isOpen" class="chat-window">
        <!-- Header -->
        <div class="chat-header">
          <span class="flag">🇬🇳</span>
          <div class="header-text">
            <h3>Fomba</h3>
            <p>Assistant pour la Loi L/2019/0027/AN - Statut des Agents de l'État</p>
          </div>
          <button class="close-btn" @click="close" title="Fermer">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
            </svg>
          </button>
        </div>

        <!-- Messages -->
        <div class="messages-container" ref="messagesContainer">
          <!-- Welcome -->
          <div v-if="messages.length === 0" class="welcome-section">
            <div class="welcome-icon">⚖️</div>
            <h2>Bonjour, je suis Fomba</h2>
            <p>Votre assistant virtuel pour comprendre le Statut Général des Agents de l'État de la République de Guinée. Posez-moi vos questions sur la loi L0027.</p>
            <div class="starter-questions">
              <button 
                v-for="q in starterQuestions" 
                :key="q.question"
                class="starter-btn"
                @click="sendMessage(q.question)"
              >
                💡 {{ q.question }}
              </button>
            </div>
          </div>

          <!-- Messages List -->
          <div 
            v-for="msg in messages" 
            :key="msg.id"
            class="message"
            :class="msg.role"
          >
            <div class="message-content" v-html="formatText(msg.content)"></div>
            
            <!-- Suggestions uniquement (pas de confidence ni articles_references) -->
            <div v-if="msg.suggestions && msg.suggestions.length" class="suggestions-section">
              <div class="section-title">Questions connexes</div>
              <button 
                v-for="s in msg.suggestions" 
                :key="s.question"
                class="suggestion-btn"
                @click="sendMessage(s.question)"
              >
                {{ s.question }}
              </button>
            </div>
          </div>

          <!-- Typing Indicator -->
          <div v-if="isLoading" class="message assistant">
            <div class="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>

        <!-- Input -->
        <div class="input-area">
          <textarea
            v-model="inputValue"
            @keydown.enter.prevent="handleEnter"
            placeholder="Posez votre question..."
            rows="1"
            :disabled="isLoading"
            ref="inputField"
          ></textarea>
          <button 
            class="send-btn" 
            @click="sendMessage(inputValue)"
            :disabled="isLoading || !inputValue.trim()"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
            </svg>
          </button>
        </div>
      </div>
    </Transition>

    <!-- Floating Button -->
    <button 
      class="floating-btn" 
      :class="{ open: isOpen }"
      @click="toggle"
      :title="isOpen ? 'Fermer' : 'Ouvrir l\'assistant'"
    >
      <svg width="28" height="28" viewBox="0 0 24 24" fill="currentColor">
        <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/>
      </svg>
    </button>
  </div>
</template>

<script>
export default {
  name: 'ChatbotL0027',
  
  props: {
    apiUrl: {
      type: String,
      default: 'http://localhost:8000/api/v1'
    },
    position: {
      type: String,
      default: 'bottom-right',
      validator: (val) => ['bottom-right', 'bottom-left'].includes(val)
    },
    defaultOpen: {
      type: Boolean,
      default: false
    }
  },

  data() {
    return {
      isOpen: this.defaultOpen,
      messages: [],
      inputValue: '',
      isLoading: false,
      starterQuestions: [],
      sessionId: this.generateSessionId()
    };
  },

  mounted() {
    this.loadStarterQuestions();
  },

  watch: {
    messages: {
      handler() {
        this.$nextTick(() => {
          this.scrollToBottom();
        });
      },
      deep: true
    }
  },

  methods: {
    generateSessionId() {
      return 'session_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
    },

    async loadStarterQuestions() {
      try {
        const response = await fetch(`${this.apiUrl}/suggestions/starter`);
        const data = await response.json();
        this.starterQuestions = data.slice(0, 4);
      } catch (error) {
        console.error('Error loading starter questions:', error);
        this.starterQuestions = [
          { question: "Qu'est-ce qu'un agent de l'État ?" },
          { question: "Quel est l'âge de la retraite ?" },
          { question: "Comment fonctionne l'avancement ?" }
        ];
      }
    },

    toggle() {
      this.isOpen = !this.isOpen;
      if (this.isOpen) {
        this.$nextTick(() => {
          this.$refs.inputField?.focus();
        });
      }
    },

    open() {
      this.isOpen = true;
    },

    close() {
      this.isOpen = false;
    },

    handleEnter(e) {
      if (!e.shiftKey) {
        this.sendMessage(this.inputValue);
      }
    },

    async sendMessage(question) {
      if (!question?.trim() || this.isLoading) return;

      const userMessage = {
        id: Date.now().toString(),
        role: 'user',
        content: question.trim()
      };

      this.messages.push(userMessage);
      this.inputValue = '';
      this.isLoading = true;

      try {
        const response = await fetch(`${this.apiUrl}/ask`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            question: question.trim(),
            session_id: this.sessionId,
            include_suggestions: true
          })
        });

        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = await response.json();

        this.messages.push({
          id: data.response_id,
          role: 'assistant',
          content: data.answer,
          suggestions: data.suggested_questions
          // Suppression de articles, confidence, processingTime, cached, provider
        });

      } catch (error) {
        console.error('Error:', error);
        this.messages.push({
          id: Date.now().toString(),
          role: 'assistant',
          content: "Désolé, une erreur s'est produite. Veuillez réessayer."
        });
      } finally {
        this.isLoading = false;
        this.$refs.inputField?.focus();
      }
    },

    async showArticle(article) {
      try {
        const response = await fetch(`${this.apiUrl}/articles/${article.numero}`);
        const data = await response.json();
        alert(`Article ${data.numero}\n\n${data.contenu}\n\nThème: ${data.theme_principal}`);
      } catch (error) {
        console.error('Error:', error);
      }
    },

    formatText(text) {
      if (!text) return '';
      
      // Formatage markdown amélioré pour un rendu professionnel
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
    },

    // Méthode getConfidenceClass supprimée (confidence n'est plus affichée)

    scrollToBottom() {
      const container = this.$refs.messagesContainer;
      if (container) {
        container.scrollTop = container.scrollHeight;
      }
    },

    // Public methods for external control
    askQuestion(question) {
      if (!this.isOpen) this.open();
      this.$nextTick(() => {
        this.sendMessage(question);
      });
    }
  }
};
</script>

<style scoped>
.chatbot-container {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 9999;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
}

.chatbot-container.position-left {
  right: auto;
  left: 20px;
}

/* Floating Button */
.floating-btn {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(135deg, #1e40af, #1e3a8a);
  border: none;
  cursor: pointer;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  color: white;
}

.floating-btn:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
}

.floating-btn.open {
  transform: rotate(180deg);
}

/* Chat Window */
.chat-window {
  position: absolute;
  bottom: 75px;
  right: 0;
  width: 380px;
  height: 600px;
  max-height: calc(100vh - 100px);
  background: white;
  border-radius: 16px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.position-left .chat-window {
  right: auto;
  left: 0;
}

/* Header - Style officiel et professionnel */
.chat-header {
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
  color: white;
  padding: 18px 24px;
  display: flex;
  align-items: center;
  gap: 14px;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
  border-bottom: 3px solid #dc2626;
}

.chat-header .flag {
  font-size: 32px;
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));
}

.chat-header .header-text {
  flex: 1;
}

.chat-header h3 {
  font-size: 18px;
  font-weight: 700;
  margin: 0 0 2px 0;
  letter-spacing: -0.02em;
}

.chat-header p {
  font-size: 13px;
  opacity: 0.9;
  margin: 0;
  font-weight: 400;
}

.close-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  transition: background 0.2s;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

/* Messages */
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: #f8fafc;
}

.welcome-section {
  text-align: center;
  padding: 30px;
}

.welcome-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.welcome-section h2 {
  font-size: 22px;
  margin-bottom: 12px;
  color: #1e293b;
  font-weight: 700;
}

.welcome-section p {
  font-size: 15px;
  color: #475569;
  margin-bottom: 32px;
  line-height: 1.6;
  max-width: 500px;
  margin-left: auto;
  margin-right: auto;
}

.starter-questions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.starter-btn {
  padding: 12px 16px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  cursor: pointer;
  font-size: 13px;
  color: #1e293b;
  text-align: left;
  transition: all 0.2s;
}

.starter-btn:hover {
  background: #1e40af;
  color: white;
  border-color: #1e40af;
}

/* Message */
.message {
  max-width: 85%;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.message.user {
  align-self: flex-end;
}

.message.assistant {
  align-self: flex-start;
}

.message-content {
  padding: 16px 20px;
  border-radius: 18px;
  line-height: 1.65;
  font-size: 15px;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.message-content p {
  margin-bottom: 12px;
  text-align: justify;
}

.message-content p:last-child {
  margin-bottom: 0;
}

.message-content strong {
  color: #1e3a8a;
  font-weight: 600;
}

.message-content em {
  font-style: italic;
  color: #475569;
}

.message-content ul,
.message-content ol {
  margin: 12px 0;
  padding-left: 24px;
}

.message-content li {
  margin: 6px 0;
  line-height: 1.6;
}

.message-content ul {
  list-style-type: disc;
}

.message-content ol {
  list-style-type: decimal;
}

.message-content blockquote {
  border-left: 4px solid #1e40af;
  padding-left: 16px;
  margin: 12px 0;
  color: #475569;
  font-style: italic;
  background: #f8fafc;
  padding: 12px 16px;
  border-radius: 4px;
}

.message-content code {
  background: #f8fafc;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 0.9em;
  color: #1e3a8a;
}

.message-content pre {
  background: #f8fafc;
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 12px 0;
  border: 1px solid #e2e8f0;
}

.message-content pre code {
  background: none;
  padding: 0;
}

.message-content h1,
.message-content h2,
.message-content h3,
.message-content h4 {
  margin: 16px 0 8px 0;
  color: #1e3a8a;
  font-weight: 600;
}

.message-content h1 { font-size: 1.5em; }
.message-content h2 { font-size: 1.3em; }
.message-content h3 { font-size: 1.1em; }

.message-content hr {
  border: none;
  border-top: 1px solid #e2e8f0;
  margin: 16px 0;
}

.message.user .message-content {
  background: linear-gradient(135deg, #1e40af, #1e3a8a);
  color: white;
  border-bottom-right-radius: 4px;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}

.message.assistant .message-content {
  background: white;
  color: #1e293b;
  border-bottom-left-radius: 4px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  border: 1px solid #f1f5f9;
}

/* Suggestions - Design professionnel */
.suggestions-section {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #f1f5f9;
}

.section-title {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #64748b;
  margin-bottom: 12px;
  font-weight: 600;
}

.suggestion-btn {
  display: block;
  width: 100%;
  text-align: left;
  padding: 12px 16px;
  margin: 8px 0;
  background: #f8fafc;
  border: 1.5px solid #e2e8f0;
  border-radius: 10px;
  cursor: pointer;
  font-size: 13px;
  color: #1e293b;
  transition: all 0.2s;
}

.suggestion-btn:hover {
  background: #3b82f6;
  color: white;
  border-color: #3b82f6;
  transform: translateX(4px);
}

/* Metadata */
.message-meta {
  font-size: 10px;
  color: #64748b;
  margin-top: 8px;
}

/* Styles de confidence supprimés - confidence n'est plus affichée */

/* Typing Indicator */
.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
  background: white;
  border-radius: 16px;
  width: fit-content;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: #64748b;
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

/* Input Area */
.input-area {
  padding: 16px 20px;
  background: white;
  border-top: 1px solid #e2e8f0;
  display: flex;
  gap: 12px;
}

.input-area textarea {
  flex: 1;
  padding: 12px 16px;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  font-size: 14px;
  resize: none;
  outline: none;
  font-family: inherit;
  max-height: 120px;
  transition: border-color 0.2s;
}

.input-area textarea:focus {
  border-color: #1e40af;
}

.send-btn {
  width: 48px;
  height: 48px;
  background: #1e40af;
  color: white;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.send-btn:hover:not(:disabled) {
  background: #1e3a8a;
}

.send-btn:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}

/* Transition */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}

/* Scrollbar */
.messages-container::-webkit-scrollbar {
  width: 6px;
}

.messages-container::-webkit-scrollbar-track {
  background: transparent;
}

.messages-container::-webkit-scrollbar-thumb {
  background: #e2e8f0;
  border-radius: 3px;
}

/* Responsive */
@media (max-width: 480px) {
  .chatbot-container {
    bottom: 15px;
    right: 15px;
  }

  .chatbot-container.position-left {
    left: 15px;
  }

  .chat-window {
    width: calc(100vw - 40px);
    height: calc(100vh - 100px);
  }
}
</style>
