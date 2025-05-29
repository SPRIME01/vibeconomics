import React, { useState } from 'react';
import { useCopilotAction } from '@copilotkit/react-core'; // Assuming import path

/**
 * Props for the CopilotActions component.
 * These can be used to pass context or configuration to the actions.
 */
export interface CopilotActionsProps {
  /**
   * An optional ID of the current document, which could be used by actions
   * like summarizeText if they were to fetch document content.
   */
  currentDocumentId?: string;
}

/**
 * CopilotActions is a component that defines a set of custom actions
 * available to the CopilotKit system. These actions can be invoked by the AI
 * based on user commands or other triggers. This component itself doesn't
 * render much UI, but serves as a host for `useCopilotAction` hooks.
 *
 * The `actionOutput` state is used for demonstrating in this component's UI
 * that an action was called and what its output was. In a real application,
 * action results might be handled differently (e.g., updating application state,
 * showing notifications, etc.).
 */
const CopilotActions: React.FC<CopilotActionsProps> = ({ currentDocumentId }) => {
  const [actionOutput, setActionOutput] = useState<string>('');

  /**
   * @CopilotAction summarizeText
   * @description Summarizes the provided text using a client-side simulation.
   * @param text The text to summarize.
   */
  useCopilotAction({
    name: "summarizeText",
    description: "Summarizes the provided text.",
    parameters: [
      { name: "text", type: "string", description: "The text to summarize.", required: true },
    ],
    handler: async ({ text }) => {
      // Simulate client-side summarization
      const summary = `Summary of "${text.substring(0, Math.min(text.length, 30))}...": The text appears to be about various topics based on its content. (mock client-side summary).`;
      const outputMessage = `Action "summarizeText" called.
Input Text: "${text}"
Output: ${summary}`;
      setActionOutput(outputMessage);
      console.log(outputMessage); // For debugging in console
      // alert(outputMessage); // Alert can be disruptive; using console and UI state instead.
    },
  });

  /**
   * @CopilotAction createTask
   * @description Creates a new task with the given title and description by simulating a backend API call.
   * @param title The title of the task.
   * @param description Optional description for the task.
   */
  useCopilotAction({
    name: "createTask",
    description: "Creates a new task with the given title and description.",
    parameters: [
      { name: "title", type: "string", description: "The title of the task.", required: true },
      { name: "description", type: "string", description: "The description of the task.", required: false },
    ],
    handler: async ({ title, description = "" }) => {
      const loadingMessage = `Attempting to create task: "${title}"...`;
      setActionOutput(loadingMessage);
      console.log(loadingMessage);

      try {
        // In a real app, this would be an actual API call.
        // For this component, we simulate it.
        // The Storybook stories will use MSW to mock this at the network level.
        // Here, we just simulate the fetch call structure.
        const response = await fetch('/api/tasks', { 
          method: 'POST', 
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title, description }) 
        });

        if (!response.ok) {
          // Try to parse error from backend if available
          let errorData;
          try {
            errorData = await response.json();
          } catch (e) {
            // Ignore if error response is not JSON
          }
          throw new Error(errorData?.message || `Network response was not ok (status: ${response.status})`);
        }
        
        const mockResult = await response.json(); // Should match MSW mock structure
        const successMessage = `Task "${mockResult.title}" (ID: ${mockResult.id}) created successfully via mock API.`;
        setActionOutput(successMessage);
        console.log(successMessage);
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : "Unknown error occurred";
        const failureMessage = `Failed to create task "${title}": ${errorMessage}`;
        setActionOutput(failureMessage);
        console.error(failureMessage);
      }
    },
  });

  /**
   * @CopilotAction notifyUser
   * @description Shows a notification message to the user (simulated via state update and console).
   * @param message The message to display in the notification.
   * @param type The type of notification (e.g., 'info', 'warning', 'error').
   */
  useCopilotAction({
    name: "notifyUser",
    description: "Shows a notification message to the user.",
    parameters: [
      { name: "message", type: "string", description: "The message to display.", required: true },
      { name: "type", type: "string", description: "Type of notification (e.g., 'info', 'warning', 'error')", enum: ['info', 'warning', 'error'], required: false }
    ],
    handler: async ({ message, type = 'info' }) => {
      const notification = `Notification (${type}): "${message}"`;
      setActionOutput(notification);
      console.log(notification); // Simulate showing a toast or UI message
      // alert(notification); // Alert can be disruptive
    }
  });

  return (
    <div style={{ border: '1px solid #eee', padding: '10px', marginTop: '10px', fontFamily: 'sans-serif' }}>
      <h3>Copilot Actions Host Component</h3>
      <p>This component defines several Copilot actions. These actions are made available to the Copilot system (e.g., a Copilot Sidebar) when this component is rendered within the application.</p>
      <p>To test, use a Copilot interface and try commands like:</p>
      <ul>
        <li>"Summarize this text: The quick brown fox jumps over the lazy dog."</li>
        <li>"Create a new task titled 'Buy groceries' with description 'Milk, eggs, bread'."</li>
        <li>"Notify me with the message 'Deployment successful!' type info."</li>
      </ul>
      {currentDocumentId && <p><strong>Current Document ID:</strong> {currentDocumentId}</p>}
      <div>
        <strong>Last Action Output/Log:</strong>
        <pre style={{ backgroundColor: '#f5f5f5', padding: '10px', borderRadius: '4px', whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
          {actionOutput || "No actions triggered yet."}
        </pre>
      </div>
    </div>
  );
};

export default CopilotActions;
