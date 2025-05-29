import React from 'react';
import type { Meta, StoryObj } from '@storybook/react';
import { rest } from 'msw';

import CopilotActions from './CopilotActions';
import { CopilotProviderDecorator } from '../../.storybook/copilot-decorator'; // Adjust path as needed

// --- MSW Handlers for createTask action ---
const MOCK_API_BASE = '/api'; // Using a relative path for MSW

const createTaskSuccess = rest.post(`${MOCK_API_BASE}/tasks`, async (req, res, ctx) => {
  try {
    const body = await req.json();
    const { title, description } = body as { title: string, description?: string };
    
    if (!title || typeof title !== 'string') {
      return res(
        ctx.status(400),
        ctx.json({ message: 'Title is required and must be a string' })
      );
    }
    
    return res(
      ctx.status(201),
      ctx.json({
        id: `tskmsw_${Date.now()}`,
        title,
        description: description || 'No description',
        status: 'success'
      })
    );
  } catch (error) {
    return res(
      ctx.status(400),
      ctx.json({ message: 'Invalid JSON in request body' })
    );
  }
});

const createTaskError = rest.post(`${MOCK_API_BASE}/tasks`, (req, res, ctx) => {
  return res(
    ctx.status(500), 
    ctx.json({ 
      message: "Failed to create task (mocked server error)", 
      status: 'error' 
    })
  );
});

const createTaskLoading = rest.post(`${MOCK_API_BASE}/tasks`, (req, res, ctx) => {
  return res(
    ctx.delay('infinite'), // Simulate perpetual loading
    ctx.json({ message: "This response should not be seen if delay is infinite." }) 
  );
});

// --- Storybook Meta Configuration ---

const meta: Meta<typeof CopilotActions> = {
  title: 'Components/CopilotActions',
  component: CopilotActions,
  decorators: [CopilotProviderDecorator],
  tags: ['autodocs'],
  parameters: {
    // Default MSW handlers for stories in this file.
    // Individual stories can override these.
    // summarizeText and notifyUser actions are client-side and don't need MSW here.
    msw: { 
      handlers: [createTaskSuccess] // Default to success for createTask
    },
    viewport: {
      // Example viewports - ensure @storybook/addon-viewport is installed or part of essentials
      viewports: {
        small: { name: 'Small Mobile', styles: { width: '360px', height: '640px' } },
        medium: { name: 'Tablet', styles: { width: '768px', height: '1024px' } },
        large: { name: 'Desktop', styles: { width: '1280px', height: '800px' } },
      },
      defaultViewport: 'medium', // Set a default viewport for these stories
    },
    docs: {
      description: {
        component: `
The \`CopilotActions\` component serves as a host for defining custom actions available to the CopilotKit system.
It uses the \`useCopilotAction\` hook to register actions like client-side text summarization,
simulated backend calls for task creation, and UI notifications.

- **Testing Actions:** These actions are primarily designed to be invoked by the AI (e.g., through a Copilot sidebar or chat interface). The component itself provides minimal UI, mainly for displaying the output of the last triggered action for debugging.
- **MSW Integration:** For actions involving backend calls (like \`createTask\`), MSW is used to mock API responses in Storybook.
- **Client-Side Actions:** Actions like \`summarizeText\` and \`notifyUser\` are handled client-side within their handlers.
`,
      },
    },
  },
  argTypes: {
    currentDocumentId: { 
      control: 'text', 
      description: 'Optional document ID to simulate context for actions. This prop is for demonstration and not directly used by the current mock action handlers but illustrates how context could be passed.',
      defaultValue: 'doc_example_123',
    },
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

// --- Story Definitions ---

/**
 * Default view of the CopilotActions component.
 * This story primarily shows the informational UI of the CopilotActions component.
 * To test the defined actions, you would typically use a Copilot chat interface 
 * (like the CopilotSidebar) connected to the same CopilotKit instance.
 * 
 * Example commands for a Copilot UI:
 * - "Summarize this: The quick brown fox jumps over the lazy dog."
 * - "Create a task: title='Deploy to production' description='Final deployment steps for v2.0'."
 * - "Notify me: 'Build completed successfully!' type='info'."
 */
export const DefaultView: Story = {
  args: {
    currentDocumentId: "doc_default_view_456",
  },
  parameters: {
    docs: {
      description: {
        story: `
The \`CopilotActions\` component itself renders a simple UI displaying the output of the last action.
The core functionality is defining actions available to the Copilot system.
Test by interacting with a Copilot UI (e.g., sidebar) and issuing commands related to the defined actions.
The \`createTask\` action will use the default MSW handler (success) unless overridden.
`,
      },
    },
  },
};

/**
 * Demonstrates the \`createTask\` action with a **successful** backend response.
 * When "createTask" is invoked by the AI, MSW will return a 201 status.
 * 
 * Example Copilot command: "Create a new task with title 'Review PR #123'."
 */
export const CreateTaskSuccess: Story = {
  args: {
    currentDocumentId: "doc_task_success_789",
  },
  parameters: {
    msw: { handlers: [createTaskSuccess] }, // Override default with specific success handler
    docs: {
      description: {
        story: `
Tests the \`createTask\` action with a successful mock API response (201 Created).
Use a Copilot UI to trigger the action, e.g., "Create task: title='Submit report' description='Finalize and submit Q3 report'."
The output area in the component should reflect the successful task creation.
`,
      },
    },
  },
};

/**
 * Demonstrates the \`createTask\` action with a **failed** backend response.
 * When "createTask" is invoked by the AI, MSW will return a 500 status.
 * 
 * Example Copilot command: "Create task: title='This will fail'."
 */
export const CreateTaskError: Story = {
  args: {
    currentDocumentId: "doc_task_error_101",
  },
  parameters: {
    msw: { handlers: [createTaskError] }, // Override with error handler
    docs: {
      description: {
        story: `
Tests the \`createTask\` action with a failed mock API response (500 Internal Server Error).
Use a Copilot UI, e.g., "Create task: title='Book conference room' description='For team meeting on Friday'."
The output area should display the error message from the mock API.
`,
      },
    },
  },
};

/**
 * Demonstrates the \`createTask\` action in a **loading** state.
 * When "createTask" is invoked by the AI, MSW will simulate a long delay.
 * Visual feedback for loading depends on how the Copilot UI (e.g., sidebar) handles pending actions.
 * 
 * Example Copilot command: "Create task: title='Long running process'."
 */
export const CreateTaskLoading: Story = {
  args: {
    currentDocumentId: "doc_task_loading_112",
  },
  parameters: {
    msw: { handlers: [createTaskLoading] }, // Override with loading handler
    docs: {
      description: {
        story: `
Tests the \`createTask\` action with a perpetual loading state from the mock API.
Use a Copilot UI, e.g., "Create task: title='Generate annual report'."
The Copilot UI calling this action should indicate a loading or pending state. The \`CopilotActions\` component's output area will show the "Attempting to create task..." message.
`,
      },
    },
  },
};
