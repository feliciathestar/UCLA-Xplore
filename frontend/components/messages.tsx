import { UIMessage, JSONValue } from 'ai';
import { PreviewMessage, ThinkingMessage } from './message';
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

  return (
    <div
      ref={messagesContainerRef}
      className="flex flex-col min-w-0 gap-6 flex-1 overflow-y-scroll pt-4"
    >
      {messages.length === 0 && !data?.length && <Overview />}

      {messages.map((message, index) => (
        <PreviewMessage
          key={message.id}
          chatId={chatId}
          message={message}
          isLoading={status === 'streaming' && messages.length - 1 === index}
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

      {/* THIS IS THE CORRECTED SECTION TO RENDER DATA ITEMS AS CHAT BUBBLES */}
      {data?.map((dataItem, index) => {
        if (typeof dataItem === 'object' && dataItem !== null && 'content' in dataItem) {
          const item = dataItem as { type?: string; content: string };
          
          // Transform dataItem to a UIMessage-like object
          const assistantMessageFromData: UIMessage = {
            id: `data-msg-${generateUUID()}`, // Ensure a unique ID
            role: 'assistant', // Treat it as an assistant message
            content: item.content, // Keep content for potential direct use or display
            createdAt: new Date(), // Optional: for consistency
            parts: [{ type: 'text', text: item.content }], // <<< FIXED: Use 'text' instead of 'value'
          };

          // Render using your existing PreviewMessage component
          return (
            <PreviewMessage
              key={assistantMessageFromData.id}
              chatId={chatId}
              message={assistantMessageFromData}
              isLoading={false} // These messages are not actively streaming
              vote={undefined} // Pass undefined as vote is required
              setMessages={setMessages} 
              reload={reload}
              isReadonly={isReadonly}
            />
          );
        }
        // Fallback for unexpected data structures (optional, consider logging instead)
        return (
          <div key={`data-fallback-${index}`} className="px-4">
            <pre className="bg-gray-100 p-2 text-xs">
              Unexpected data format: {JSON.stringify(dataItem, null, 2)}
            </pre>
          </div>
        );
      })}

      {status === 'submitted' &&
        messages.length > 0 &&
        messages[messages.length - 1].role === 'user' && <ThinkingMessage />}

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
