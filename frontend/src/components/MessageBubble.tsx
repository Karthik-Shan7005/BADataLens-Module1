import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import ChartPanel from './ChartPanel';
import type { Message } from '../types';

interface Props {
  message: Message;
}

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === 'user';

  return (
    <div className={`message-row ${isUser ? 'message-row--user' : 'message-row--ai'}`}>
      <div className={`message-avatar ${isUser ? 'message-avatar--user' : 'message-avatar--ai'}`}>
        {isUser ? 'You' : 'AI'}
      </div>
      <div className={`message-bubble ${isUser ? 'bubble--user' : 'bubble--ai'}`}>
        {isUser ? (
          <p className="message-text">{message.content}</p>
        ) : (
          <>
            <div className="message-markdown">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content}
              </ReactMarkdown>
            </div>
            {message.chart && <ChartPanel chart={message.chart} />}
          </>
        )}
        <div className="message-time">
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
    </div>
  );
}
