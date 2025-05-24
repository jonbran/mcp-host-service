# UI Changes for Displaying Human-Readable Titles

## Overview

The following changes are required in the UI to support displaying human-readable titles for conversations while maintaining UUIDs as unique identifiers for API interactions.

---

## Changes Required

### 1. Fetch Conversations with Titles

- Update the API call to fetch conversations to include the `title` field in the response.
- Example API Response:
  ```json
  [
    {
      "id": "6bc898b1-4c08-469e-8e33-25a1db2d1729",
      "title": "What is the weather today?",
      "messages": [...]
    },
    {
      "id": "72f87e2a-8573-4242-adda-3da48a792057",
      "title": "New Conversation",
      "messages": [...]
    }
  ]
  ```

### 2. Update Conversation List

- Display the `title` field in the conversation list instead of the UUID.
- Example:
  ```
  - What is the weather today?
  - New Conversation
  ```

### 3. Use UUID for API Calls

- When interacting with a specific conversation (e.g., retrieving messages, adding a message, or deleting a conversation), continue using the `id` (UUID) as the unique identifier.

### 4. Fallback for Missing Titles

- If the `title` field is missing or empty, display a default value like "Untitled Conversation".

### 5. Optional Enhancements

- Allow users to edit the title of a conversation directly from the UI.
- Save the updated title to the backend using a dedicated API endpoint (if implemented).

---

## Example Workflow

1. **Fetch Conversations**:

   - The UI fetches the list of conversations from the backend.
   - Each conversation includes a `title` and `id`.

2. **Display Titles**:

   - The UI displays the `title` in the conversation list.
   - If the `title` is missing, the UI displays "Untitled Conversation".

3. **Interact with Conversations**:

   - When a user selects a conversation, the UI uses the `id` to fetch or update the conversation.

4. **Edit Titles (Optional)**:
   - If supported, the user can edit the title of a conversation.
   - The UI sends the updated title to the backend via an API call.

---

## Notes

- Ensure the UI gracefully handles cases where the `title` field is missing or empty.
- Maintain backward compatibility with existing API responses that may not include the `title` field.

---

## Testing

- Verify that the conversation list displays titles correctly.
- Test interactions with conversations using their UUIDs.
- Ensure fallback titles are displayed for conversations without a `title` field.
- If title editing is implemented, test the workflow for updating titles and persisting changes to the backend.
