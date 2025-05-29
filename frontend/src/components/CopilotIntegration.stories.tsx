import type { Meta, StoryContext, StoryObj } from '@storybook/react';
import { ResponseComposition, rest, RestContext, RestRequest } from 'msw';

import { CopilotProviderDecorator } from '../../.storybook/copilot-decorator'; // Adjust path as needed
import CopilotIntegration from './CopilotIntegration';

// --- MSW Handlers ---
const MOCK_API_BASE = '/api';

const createTaskSuccess = rest.post(`${MOCK_API_BASE}/tasks`, async (req, res, ctx) => {
  const { title, description } = await req.json() as { title: string, description?: string };
  return res(
    ctx.status(201),
    ctx.json({
      id: `tskmsw_integ_${Date.now()}`,
      title,
      description: description || 'No description provided',
      status: 'success'
    })
  );
});

const createTaskError = rest.post(`${MOCK_API_BASE}/tasks`, (req, res, ctx) => {
  return res(
    ctx.status(500),
    ctx.json({
      message: "Failed to create task (mocked server error from integration story)",
      status: 'error'
    })
  );
});

// Define explicit types for the request and response payloads
interface CopilotExecuteRequest {
  message: string;
  conversationId?: string | null;
}

interface CopilotExecuteResponse {
  reply: string;
}

// Factory function to create MSW handlers with context/args
function createCopilotMockHandler(context: { userMessage?: string }) {
  return rest.post< CopilotExecuteRequest, CopilotExecuteResponse >(
    '/copilot/execute',
    (req: RestRequest<CopilotExecuteRequest>, res: ResponseComposition<CopilotExecuteResponse>, ctx: RestContext) => {
      // Use the context or args passed to the factory
      const reply = `Echo: ${context.userMessage ?? req.body?.message ?? 'No message'}`;
      return res(
        ctx.status(200),
        ctx.json({ reply })
      );
    }
  );
}

// Variable to hold story context, captured by a decorator.
// This allows MSW handlers to be somewhat dynamic based on story args.
let storyBookContext: StoryContext | null = null;

const copilotMockHandler = rest.post('/copilot/mock', async (req, res, ctx) => {
  const { messages } = await req.json() as { messages: {content: string, role: string}[] }; // Assuming messages is an array
  const lastMessage = messages[messages.length - 1];
  let reply = `Mock AI response to: "${lastMessage.content.substring(0, 50)}..." (Integration Mock)`;

  if (lastMessage.content.toLowerCase().includes("page title")) {
    const pageTitle =
      storyBookContext?.args?.initialPageTitle ||
      // Accessing nested props if defined in args directly, e.g. args: { sidebarProps: { initialPageTitle: '...' }}
      // This part might need adjustment based on actual arg structure for nested props.
      (storyBookContext?.args?.sidebarProps as any)?.initialPageTitle ||
      "Default Integrated Page Title";
    reply = `The current page title is "${pageTitle}". (Simulated from mock context in integration story)`;
  } else if (lastMessage.content.toLowerCase().includes("summarize this text:")) {
    reply = "Okay, I will summarize that text for you. (Action: summarizeText invoked via Integration)";
  } else if (lastMessage.content.toLowerCase().includes("create a new task") || lastMessage.content.toLowerCase().includes("create task")) {
    reply = "Sure, I can create that task. (Action: createTask invoked via Integration)";
  } else if (lastMessage.content.toLowerCase().includes("notify me")) {
    reply = "Alright, I'll send that notification. (Action: notifyUser invoked via Integration)";
  }
  return res(ctx.delay(200), ctx.json({ reply }));
});


// --- Storybook Meta Configuration ---

export default {
  title: 'Components/CopilotIntegration',
  component: CopilotIntegration,
  decorators: [
    CopilotProviderDecorator, // Provides CopilotKit context
  ],
  tags: ['autodocs'],
  parameters: {
    layout: 'fullscreen', // Uses the full screen for this integrated view
    msw: {
      handlers: [copilotMockHandler, createTaskSuccess], // Default handlers for all stories
    },
    backgrounds: { // Configure the backgrounds addon
      default: 'light',
      values: [
        { name: 'light', value: '#ffffff' },
        { name: 'dark', value: '#333333' },
        { name: 'blue', value: '#cceeff' },
      ],
    },
    docs: {
      description: {
        component: `
This component demonstrates the integration of \`CopilotSidebar\` and \`CopilotActions\`.
It simulates a full application page where a user can interact with the Copilot (sidebar)
which can then invoke actions defined elsewhere (actions component).

- **CopilotKitProvider:** Assumed to be applied by the \`CopilotProviderDecorator\`.
- **MSW Mocking:** API calls from actions (like \`createTask\`) and Copilot interactions (\`/copilot/mock\`) are mocked.
- **Context Simulation:** The \`copilotMockHandler\` attempts to use story arguments to simulate context-aware responses (e.g., for "page title" queries).
`,
      },
    },
  },
  argTypes: {
    // Example of controlling nested props. Storybook's dot notation for argTypes keys.
    'sidebarProps.defaultOpen': {
      name: 'Sidebar Default Open',
      control: 'boolean',
      description: 'Controls if the CopilotSidebar is open by default.',
      defaultValue: true,
    },
    'actionsProps.currentDocumentId': {
      name: 'Actions Current Document ID',
      control: 'text',
      description: 'An example document ID passed to CopilotActions for context.',
      defaultValue: 'doc_integration_default',
    },
    initialPageTitle: {
      name: 'Initial Page Title (Context)',
      control: 'text',
      description: 'Sets the document.title and can be read by useCopilotReadable in Sidebar if it is configured to do so (e.g., reads document.title or receives it as a prop). The mock handler also uses this for "page title" queries.',
      defaultValue: 'Integrated Copilot Page',
    },
  },
} satisfies Meta<typeof CopilotIntegration>;

type Story = StoryObj<typeof CopilotIntegration>;

// --- Story Definitions ---

/**
 * Default experience for the integrated Copilot components.
 * The sidebar is open, and actions are available.
 * Try commands like:
 * - "Summarize this text: Storybook is a great tool for UI development."
 * - "Create task: title='Finalize integration story' description='Ensure all parts work together'."
 * - "What is the current page title?"
 */
export const DefaultExperience: Story = {
  args: {
    sidebarProps: { defaultOpen: true },
    actionsProps: { currentDocumentId: "doc_integration_default" },
    initialPageTitle: "My Integrated Test Page"
  },
  parameters: {
    docs: {
      description: {
        story: 'The full Copilot experience. The sidebar interacts with actions, and context (like page title) can be queried. MSW mocks backend calls.',
      },
    },
  },
};

/**
 * Tests the error flow for the `createTask` action.
 * When you try to create a task via the sidebar, the mocked backend will return an error.
 * Example command: "Create task title ErrorProneTask description This should show an error"
 */
export const CreateTaskErrorFlow: Story = {
  args: {
    ...DefaultExperience.args, // Reuse args from DefaultExperience
    initialPageTitle: "Task Error Test Page"
  },
  parameters: {
    msw: { handlers: [copilotMockHandler, createTaskError] }, // Override createTask handler
    docs: {
      description: {
        story: 'This story configures the mock API for `createTask` to return an error. Use the sidebar to try creating a task. The action output in the `CopilotActions` component area should display the error.'
      },
    },
  },
};

/**
 * Demonstrates the integrated components on a dark background.
 * Useful for checking theme compatibility and visual styles.
 */
export const DarkBackground: Story = {
  args: {
    ...DefaultExperience.args,
    initialPageTitle: "Dark Mode Test Page"
  },
  parameters: {
    backgrounds: { default: 'dark' }, // Set dark background for this story
    docs: {
      description: {
        story: 'Shows the integrated components on a dark background. Helps in identifying theming issues for UI elements.'
      }
    },
  },
};

/**
 * Simulates a scenario with potentially many messages in the sidebar.
 * This is for manual observation of UI performance and responsiveness as the conversation grows.
 * The mock AI responses are fast to facilitate many interactions quickly.
 */
export const ManyMessagesSimulation: Story = {
  args: {
    ...DefaultExperience.args,
    initialPageTitle: "Long Conversation Test"
  },
  parameters: {
    msw: {
      handlers: [
        rest.post('/copilot/mock', async (req, res, ctx) => {
          const { messages } = await req.json() as { messages: {content: string}[] };
          const lastMessage = messages[messages.length - 1];
          let reply = `Simulated response #${messages.length} to "${lastMessage.content.substring(0, 20)}..."`;
          if (messages.length > 10) {
            reply = "This is getting to be a long conversation! Still responsive?";
          }
          return res(ctx.delay(50), ctx.json({ reply })); // Fast responses
        }),
        createTaskSuccess, // Keep other actions functional
      ],
    },
    docs: {
      description: {
        story: "This story uses a mock handler that provides quick, iterative responses to simulate a long conversation. Interact repeatedly with the sidebar. Observe for any UI lag or performance degradation in the sidebar or action processing. (Manual observation or external Storybook performance addons would be needed for quantitative measurement).",
      },
    },
  },
  // play: async ({ canvasElement }) => {
  //   // Conceptual: Advanced interaction testing to send many messages.
  //   // Requires robust selectors for sidebar input and send button,
  //   // and careful handling of component updates.
  //   // const canvas = within(canvasElement);
  //   // const input = await canvas.findByRole('textbox', { name: /message/i }); // Example selector
  //   // const sendButton = await canvas.findByRole('button', { name: /send/i }); // Example selector
  //   // for (let i = 0; i < 15; i++) {
  //   //   await userEvent.type(input, `Test message ${i + 1}`, { delay: 10 });
  //   //   await userEvent.click(sendButton);
  //   //   await new Promise(r => setTimeout(r, 100)); // Wait for mock response and UI update
  //   // }
  // }
};
