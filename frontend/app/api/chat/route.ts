// Return a properly formatted stream for the useChat hook:

import {
  UIMessage,
  appendResponseMessages,
  createDataStreamResponse,
  smoothStream,
  streamText,
} from 'ai';
import { auth } from '@/app/(auth)/auth';
import { systemPrompt } from '@/lib/ai/prompts';
import {
  deleteChatById,
  getChatById,
  saveChat,
  saveMessages,
} from '@/lib/db/queries';
import {
  generateUUID,
  getMostRecentUserMessage,
  getTrailingMessageId,
} from '@/lib/utils';
import { generateTitleFromUserMessage } from '@/app/(chat)/actions';
import { createDocument } from '@/lib/ai/tools/create-document';
import { updateDocument } from '@/lib/ai/tools/update-document';
import { requestSuggestions } from '@/lib/ai/tools/request-suggestions';
import { getWeather } from '@/lib/ai/tools/get-weather';
import { isProductionEnvironment } from '@/lib/constants';
import { myProvider } from '@/lib/ai/providers';

export const maxDuration = 60;

// (chat)/api/chat/route.ts

import { NextResponse } from "next/server";
// (chat)/api/chat/route.ts

export async function POST(req: Request) {
  const { messages } = await req.json();
  const lastMessage = messages[messages.length - 1];
  const userInput = lastMessage.content;

  const backendRes = await fetch("http://localhost:8000/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: userInput })
  });

  const { response } = await backendRes.json();

  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    start(controller) {
      // Stream the assistant message as a single SSE chunk
      controller.enqueue(encoder.encode(`data: ${JSON.stringify({
        id: Date.now().toString(),
        role: "assistant",
        content: response
      })}\n\n`));
      controller.enqueue(encoder.encode("data: [DONE]\n\n"));
      controller.close();
    }
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
      "Cache-Control": "no-cache",
      "Connection": "keep-alive"
    }
  });
}



// export async function POST(request: Request) {
//   try {
//     const {
//       id,
//       messages,
//       selectedChatModel,
//     }: {
//       id: string;
//       messages: Array<UIMessage>;
//       selectedChatModel: string;
//     } = await request.json();

//     const session = await auth();

//     if (!session || !session.user || !session.user.id) {
//       return new Response('Unauthorized', { status: 401 });
//     }

//     const userMessage = getMostRecentUserMessage(messages);

//     if (!userMessage) {
//       return new Response('No user message found', { status: 400 });
//     }

//     // Before making the fetch request
//     console.log('Sending to backend:', {
//       message: userMessage.parts.join(' '),
//       parts: userMessage.parts
//     });

//     // Call the backend /chat endpoint
//     const backendResponse = await fetch('http://127.0.0.1:8000/chat', {
//       method: 'POST',
//       headers: {
//         'Content-Type': 'application/json'
//       },
//       body: JSON.stringify({
//         message: userMessage.parts.join(' '),
//       }),
//     });

//     if (!backendResponse.ok) {
//       // Handle error response from the backend
//       const errorText = await backendResponse.text();
//       console.error('Backend error:', errorText);
//       return new Response('Failed to query backend', { status: backendResponse.status });
//     }

//     /* original code starts here */
//     const chat = await getChatById({ id });
//     if (!chat) {
//       const title = await generateTitleFromUserMessage({
//         message: userMessage,
//       });

//       await saveChat({ id, userId: session.user.id, title });
//     } else {
//       if (chat.userId !== session.user.id) {
//         return new Response('Unauthorized', { status: 401 });
//       }
//     }

//     await saveMessages({
//       messages: [
//         {
//           chatId: id,
//           id: userMessage.id,
//           role: 'user',
//           parts: userMessage.parts,
//           attachments: userMessage.experimental_attachments ?? [],
//           createdAt: new Date(),
//         },
//       ],
//     });

//     /* Added logic to connect to bckend and get response */
//   //   return createDataStreamResponse({
//   //   execute: async (dataStream) => {
//   //     try {
//   //       // Get backend response
//   //       const backendResponse = await getBackendResponse(userMessage);
        
//   //       // Create a unique message ID
//   //       const messageId = generateUUID();
        
//   //       // Send the message to the dataStream directly
//   //       dataStream.append({
//   //         id: messageId,
//   //         role: 'assistant',
//   //         content: backendResponse,
//   //         createdAt: new Date().toISOString(),
//   //       });
        
//   //       // Save message to database
//   //       await saveMessages({
//   //         messages: [
//   //           {
//   //             id: messageId,
//   //             chatId: id,
//   //             role: 'assistant',
//   //             parts: [backendResponse],
//   //             attachments: [],
//   //             createdAt: new Date(),
//   //           },
//   //         ],
//   //       });
//   //     } catch (error) {
//   //       dataStream.append({
//   //         id: generateUUID(),
//   //         role: 'assistant',
//   //         content: "Sorry, I couldn't reach the backend service.",
//   //         createdAt: new Date().toISOString(),
//   //       });
//   //     }
//   //   },
//   //   onError: (error) => {
//   //     console.error('Stream error:', error);
//   //     return 'Oops, an error occurred!';
//   //   },
//   // });

//   /* Original return code starts here */
//     return createDataStreamResponse({
//       execute: (dataStream) => {
//         const result = streamText({
//           model: myProvider.languageModel(selectedChatModel),
//           system: systemPrompt({ selectedChatModel }),
//           messages,
//           maxSteps: 5,
//           experimental_activeTools:
//             selectedChatModel === 'chat-model-reasoning'
//               ? []
//               : [
//                 'getWeather',
//                 'createDocument',
//                 'updateDocument',
//                 'requestSuggestions',
//               ],
//           experimental_transform: smoothStream({ chunking: 'word' }),
//           experimental_generateMessageId: generateUUID,
//           tools: {
//             getWeather,
//             createDocument: createDocument({ session, dataStream }),
//             updateDocument: updateDocument({ session, dataStream }),
//             requestSuggestions: requestSuggestions({
//               session,
//               dataStream,
//             }),
//           },
//           onFinish: async ({ response }) => {
//             if (session.user?.id) {
//               try {
//                 const assistantId = getTrailingMessageId({
//                   messages: response.messages.filter(
//                     (message) => message.role === 'assistant',
//                   ),
//                 });

//                 if (!assistantId) {
//                   throw new Error('No assistant message found!');
//                 }

//                 const [, assistantMessage] = appendResponseMessages({
//                   messages: [userMessage],
//                   responseMessages: response.messages,
//                 });

//                 await saveMessages({
//                   messages: [
//                     {
//                       id: assistantId,
//                       chatId: id,
//                       role: assistantMessage.role,
//                       parts: assistantMessage.parts,
//                       attachments:
//                         assistantMessage.experimental_attachments ?? [],
//                       createdAt: new Date(),
//                     },
//                   ],
//                 });
//               } catch (_) {
//                 console.error('Failed to save chat');
//               }
//             }
//           },
//           experimental_telemetry: {
//             isEnabled: isProductionEnvironment,
//             functionId: 'stream-text',
//           },
//         });

//         result.consumeStream();

//         result.mergeIntoDataStream(dataStream, {
//           sendReasoning: true,
//         });
//       },
//       onError: () => {
//         return 'Oops, an error occured!';
//       },
//     });
//   } catch (error) {
//     return new Response('An error occurred while processing your request!', {
//       status: 404,
//     });
//   }
// }



// export async function DELETE(request: Request) {
//   const { searchParams } = new URL(request.url);
//   const id = searchParams.get('id');

//   if (!id) {
//     return new Response('Not Found', { status: 404 });
//   }

//   const session = await auth();

//   if (!session || !session.user) {
//     return new Response('Unauthorized', { status: 401 });
//   }

//   try {
//     const chat = await getChatById({ id });

//     if (chat.userId !== session.user.id) {
//       return new Response('Unauthorized', { status: 401 });
//     }

//     await deleteChatById({ id });

//     return new Response('Chat deleted', { status: 200 });
//   } catch (error) {
//     return new Response('An error occurred while processing your request!', {
//       status: 500,
//     });
//   }
// }

