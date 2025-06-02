import { UIMessage, JSONValue } from 'ai';
import { PreviewMessage } from './message';
import { useScrollToBottom } from './use-scroll-to-bottom';
import { Overview } from './overview';
import { memo } from 'react';
import { Vote } from '@/lib/db/schema';
import equal from 'fast-deep-equal';
import { UseChatHelpers } from '@ai-sdk/react';
import { generateUUID } from '@/lib/utils'; // Make sure this import is present

interface MessagesProps {
  chatId: string;
  status: UseChatHelpers['status'];
  votes: Array<Vote> | undefined;
  messages: Array<UIMessage>;
  data?: Array<JSONValue>;
  setMessages: UseChatHelpers['setMessages'];
  reload: UseChatHelpers['reload'];
  isReadonly: boolean;
  isArtifactVisible: boolean;
}

function PureMessages({
  chatId,
  status,
  votes,
  messages,
  data,
  setMessages,
  reload,
  isReadonly,
}: MessagesProps) {
  const [messagesContainerRef, messagesEndRef] =
    useScrollToBottom<HTMLDivElement>();

  // Create a combined array of messages in proper order
  const renderMessages = () => {
    const allMessages: UIMessage[] = [];
    
    // Add all user messages first (to maintain their order)
    const userMessages = messages.filter(message => message.role !== 'assistant');
    
    // Create assistant messages from backend data or fallback to AI messages
    let assistantMessages: UIMessage[] = [];
    
    if (data && data.length > 0) {
      // Use backend data for assistant responses
      assistantMessages = data
        .map((dataItem, index) => {
          if (typeof dataItem === 'object' && dataItem !== null && 'content' in dataItem) {
            const item = dataItem as { type?: string; content: string };
            
            if (item.content && item.content.trim() !== '') {
              return {
                id: `backend-msg-${index}`,
                role: 'assistant' as const,
                content: item.content,
                createdAt: new Date(),
                parts: [{ type: 'text' as const, text: item.content }],
              };
            }
          }
          return null;
        })
        .filter(msg => msg !== null); // Changed this line
    } else {
      // Fallback to AI assistant messages if no backend data
      assistantMessages = messages.filter(message => message.role === 'assistant');
    }
    
    // Interleave user and assistant messages
    const maxLength = Math.max(userMessages.length, assistantMessages.length);
    
    for (let i = 0; i < maxLength; i++) {
      if (i < userMessages.length) {
        allMessages.push(userMessages[i]);
      }
      if (i < assistantMessages.length) {
        allMessages.push(assistantMessages[i]);
      }
    }
    
    return allMessages;
  };

  const messagesToRender = renderMessages();

  return (
    <div
      ref={messagesContainerRef}
      className="flex flex-col min-w-0 gap-6 flex-1 overflow-y-scroll pt-4"
    >
      {messages.length === 0 && !data?.length && <Overview />}

      {/* Render messages in proper conversational order */}
      {messagesToRender.map((message, index) => (
        <PreviewMessage
          key={message.id}
          chatId={chatId}
          message={message}
          isLoading={
            message.role === 'assistant' && 
            status === 'streaming' && 
            index === messagesToRender.length - 1 &&
            !data?.length // Only show loading for AI messages, not backend data
          }
          vote={
            votes
              ? votes.find((vote) => vote.messageId === message.id)
              : undefined
          }
          setMessages={setMessages}
          reload={reload}
          isReadonly={isReadonly}
        />
      ))}

      <div
        ref={messagesEndRef}
        className="shrink-0 min-w-[24px] min-h-[24px]"
      />
    </div>
  );
}

export const Messages = memo(PureMessages, (prevProps, nextProps) => {
  if (prevProps.isArtifactVisible && nextProps.isArtifactVisible) return true;

  if (prevProps.status !== nextProps.status) return false;
  if (prevProps.messages.length !== nextProps.messages.length) return false;
  if (!equal(prevProps.messages, nextProps.messages)) return false;
  if (!equal(prevProps.votes, nextProps.votes)) return false;
  if (!equal(prevProps.data, nextProps.data)) return false;

  return true;
});
