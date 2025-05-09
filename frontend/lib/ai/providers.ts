import {
customProvider,
extractReasoningMiddleware,
wrapLanguageModel,
} from 'ai';
import { createOpenAI } from '@ai-sdk/openai';
import { isTestEnvironment } from '../constants';
import {
  artifactModel,
  chatModel,
  reasoningModel,
  titleModel,
} from './models.test';

// Create custom OpenAI provider with your configuration
const openaiInstance = createOpenAI({
  apiKey: process.env.OPENAI_API_KEY,
  compatibility: 'strict', // Use strict mode for OpenAI API
});

export const myProvider = isTestEnvironment
  ? customProvider({
      languageModels: {
        'chat-model': chatModel,
        'chat-model-reasoning': reasoningModel,
        'title-model': titleModel,
        'artifact-model': artifactModel,
      },
    })
  : customProvider({
      languageModels: {
        'chat-model': openaiInstance('gpt-4o'),  // Replace with your preferred model
        'chat-model-reasoning': wrapLanguageModel({
          model: openaiInstance('gpt-4o'),  // Use OpenAI for reasoning
          middleware: extractReasoningMiddleware({ tagName: 'think' }),
        }),
        'title-model': openaiInstance('gpt-4o'),
        'artifact-model': openaiInstance('gpt-4o'),
      },
      imageModels: {
        'small-model': openaiInstance.image('dall-e-3'),  // OpenAI's image model
      },
    });

