import { useEffect, useRef } from 'react';
import MessageBubble from './MessageBubble';
import type { Message } from '../types';

const SAMPLE_QUESTIONS = [
  'What % of respondents plan to travel in the next 12 months?',
  'Show the gender breakdown of all respondents',
  'What is the top source of travel inspiration?',
  'How do male and female respondents differ in destination preferences?',
];

interface Props {
  messages: Message[];
  loading: boolean;
  input: string;
  onInputChange: (value: string) => void;
  onSend: () => void;
}

export default function ChatWindow({ messages, loading, input, onInputChange, onSend }: Props) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (input.trim() && !loading) onSend();
    }
  };

  return (
    <div className="chat-window">
      <div className="messages-area">
        {messages.length === 0 && !loading && (
          <div className="chat-empty">
            <div className="chat-empty-icon">💬</div>
            <h3>Ask a question about your survey data</h3>
            <p>
              Type a natural language question to get instant insights with weighted
              percentages, means, and auto-generated charts.
            </p>
            <div className="sample-questions">
              {SAMPLE_QUESTIONS.map(q => (
                <button
                  key={q}
                  className="sample-chip"
                  onClick={() => onInputChange(q)}
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map(msg => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {loading && (
          <div className="message-row message-row--ai">
            <div className="message-avatar message-avatar--ai">AI</div>
            <div className="message-bubble bubble--ai bubble--loading">
              <span className="dot" />
              <span className="dot" />
              <span className="dot" />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="input-area">
        <textarea
          className="chat-input"
          value={input}
          onChange={e => onInputChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question about the survey data… (Enter to send, Shift+Enter for new line)"
          rows={2}
          disabled={loading}
        />
        <button
          className="send-button"
          onClick={onSend}
          disabled={!input.trim() || loading}
        >
          {loading ? 'Thinking…' : 'Send →'}
        </button>
      </div>
    </div>
  );
}
