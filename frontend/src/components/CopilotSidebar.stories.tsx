import React from 'react';
import type { Meta, StoryObj } from '@storybook/react';
import { rest } from 'msw';
// import { userEvent, within, expect } from '@storybook/test'; // For interaction testing

import CopilotSidebar from './CopilotSidebar';
import { CopilotProviderDecorator } from '../../.storybook/copilot-decorator';

// --- MSW Handlers ---

/**
 * Simulates a successful backend response for Copilot.
 * It attempts to echo the last user message.
 */
const mockSuccessHandler = rest.post('/copilot/mock', async (req, res, ctx) => {
  const body = await req.json() as { messages: { role: string, content: string }[] };
  const lastMessage = body.messages?.[body.messages.length - 1];
  const responseText = lastMessage?.content 
    ? `Mock response to: "${lastMessage.content}" (Sidebar)` 
    : "This is a successful mock response from the sidebar mock.";
  return res(ctx.delay(500), ctx.json({ reply: responseText }));
});

/**
 * Simulates a server error from the Copilot backend.
 */
const mockErrorHandler = rest.post('/copilot/mock', (req, res, ctx) => {
  return res(ctx.delay(500), ctx.status(500), ctx.json({ 
    error: "Simulated server error for sidebar.",
    message: "The AI backend is currently experiencing issues. Please try again later." 
  }));
});

/**
 * Simulates a perpetual loading state from the Copilot backend.
 */
const mockLoadingHandler = rest.post('/copilot/mock', (req, res, ctx) => {
  return res(ctx.delay('infinite'), ctx.json({ reply: "This should not appear due to infinite delay." }));
});

/**
 * MSW handler for the ConversationExample story.
 * Provides more specific conversational responses.
 */
const mockConversationHandler = rest.post('/copilot/mock', async (req, res, ctx) => {
    const body = await req.json() as { messages: { role: string, content: string }[] };
    const userMessage = body.messages?.find((m: any) => m.role === 'user')?.content?.toLowerCase() || "";
    let aiResponse = "How can I help you with that today?";

    if (userMessage.includes("hello") || userMessage.includes("hi")) {
        aiResponse = "Hi there! What can I assist you with?";
    } else if (userMessage.includes("context") || userMessage.includes("page")) {
        aiResponse = "I see your current page context. For example, the page title might be available to me if exposed via useCopilotReadable. What specifically would you like to know or do with this context?";
    } else if (userMessage.includes("test")) {
        aiResponse = "Test acknowledged! I'm responding as expected.";
    }
    return res(ctx.delay(300), ctx.json({ reply: aiResponse }));
});


// --- Storybook Meta Configuration ---

const meta: Meta<typeof CopilotSidebar> = {
  title: 'Components/CopilotSidebar',
  component: CopilotSidebar,
  decorators: [CopilotProviderDecorator],
  tags: ['autodocs'],
  parameters: {
    a11y: {
      // Optional: configure a11y checks
      // element: '#storybook-root', // Default is fine
      // config: { rules: [] },
    },
    // Default MSW handlers for all stories in this file.
    // Individual stories can override these.
    msw: {
      handlers: [mockSuccessHandler],
    },
    docs: {
      description: {
        component: 'The `CopilotSidebar` component integrates the CopilotKit UI sidebar. It can be configured with props and uses `useCopilotReadable` to expose application context to the AI. Ensure this component is wrapped by a `CopilotKitProvider` (handled by `CopilotProviderDecorator` in Storybook).',
      },
    },
  },
  argTypes: {
    defaultOpen: { 
      control: 'boolean', 
      description: 'Whether the sidebar is open by default when the component mounts.',
      defaultValue: true,
    },
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

// --- Story Definitions ---

/**
 * Default view of the Copilot Sidebar. 
 * It should be open and ready to interact, using the `mockSuccessHandler`.
 */
export const Default: Story = {
  args: {
    defaultOpen: true,
  },
  parameters: {
    docs: {
      description: {
        story: 'The default state of the Copilot Sidebar. It uses a mock handler that provides a simple successful response. The sidebar should be open.',
      },
    },
  },
};

/**
 * Sidebar in a loading state.
 * This story uses `mockLoadingHandler` to simulate a perpetually loading response,
 * showcasing how the sidebar might look while waiting for the AI.
 */
export const Loading: Story = {
  args: {
    ...Default.args,
  },
  parameters: {
    msw: { handlers: [mockLoadingHandler] },
    docs: {
      description: {
        story: 'Demonstrates the sidebar in a loading state, for example, when waiting for an initial response or during a long generation process from the AI. Uses an MSW handler with an infinite delay.',
      },
    },
  },
};

/**
 * Sidebar displaying an error message.
 * This story uses `mockErrorHandler` to simulate a backend error,
 * showing how the sidebar might present such issues to the user.
 */
export const ErrorState: Story = {
  args: {
    ...Default.args,
  },
  parameters: {
    msw: { handlers: [mockErrorHandler] },
    docs: {
      description: {
        story: 'Demonstrates the sidebar when an error occurs on the backend. Uses an MSW handler that returns a 500 status code and an error message.',
      },
    },
  },
};

/**
 * Sidebar in a closed state by default.
 * Demonstrates the `defaultOpen` prop.
 */
export const ClosedByDefault: Story = {
  args: {
    defaultOpen: false,
  },
  parameters: {
    docs: {
      description: {
        story: 'The sidebar when configured to be closed by default. The user would need to manually open it.',
      },
    },
  },
};

/**
 * Demonstrates a simple conversation flow.
 * Type a message (e.g., "hello", "context") and see the mocked response from `mockConversationHandler`.
 * Interaction testing with the `play` function is commented out due to potential complexity
 * with CopilotKit's internal state management but illustrates the approach.
 */
export const ConversationExample: Story = {
  args: {
    ...Default.args,
    defaultOpen: true,
  },
  parameters: {
    msw: {
      handlers: [mockConversationHandler],
    },
    docs: {
      description: {
        story: 'This story uses a more dynamic MSW handler (`mockConversationHandler`) to simulate a conversation. Try typing "hello" or "context" into the sidebar. The `play` function shows how one might write interaction tests, though these are commented out as they can be complex to implement correctly with third-party UI components.',
      },
    },
  },
  play: async ({ canvasElement, step }) => {
    // NOTE: Interaction testing with complex third-party components like CopilotKit's sidebar
    // can be challenging. Selectors may change, and internal state management can interfere.
    // The following is a conceptual example and would need careful adaptation and testing
    // with the actual CKCopilotSidebar component structure.

    // await step("Wait for sidebar to potentially load/initialize", async () => {
    //   // Add a small delay if needed for the sidebar to become fully interactive
    //   await new Promise(resolve => setTimeout(resolve, 1000)); 
    // });

    // await step("Type a message and check for a response", async () => {
    //   try {
    //     const canvas = within(canvasElement);
          
    //     // Finding the input textbox. The accessibility name or placeholder might vary.
    //     // Inspect the rendered CKCopilotSidebar component to get the correct selector.
    //     const input = await canvas.findByRole('textbox', { name: /message/i }); // Placeholder selector
    //     if (!input) throw new Error("Input textbox not found");

    //     await userEvent.type(input, "Hello there, Copilot!", { delay: 50 });
          
    //     // Finding the send button. The name or icon might vary.
    //     const sendButton = await canvas.findByRole('button', { name: /send/i }); // Placeholder selector
    //     if (!sendButton) throw new Error("Send button not found");
          
    //     await userEvent.click(sendButton);
          
    //     // Check for the mocked response. Text may vary based on mockConversationHandler.
    //     // This requires the response to be visible in the DOM.
    //     const expectedResponse = "Hi there! What can I assist you with?";
    //     const responseElement = await canvas.findByText(expectedResponse, {}, { timeout: 5000 });
    //     expect(responseElement).toBeVisible();

    //   } catch (error) {
    //     console.error("Interaction test failed:", error);
    //     // Optionally re-throw or handle if the test should fail in the Storybook UI
    //   }
    // });
    
    // await step("Type another message checking context", async () => {
    //   // Similar to the above, type "context" and check for the relevant response.
    // });
  },
};
