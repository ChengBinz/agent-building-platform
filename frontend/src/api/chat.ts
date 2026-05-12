import apiClient from "./client";

export async function listConversations(agentId?: string) {
  const params = agentId ? { agent_id: agentId } : {};
  return apiClient.get("/conversations", { params });
}

export async function createConversation(data: {
  title?: string;
  model_name?: string;
  provider?: string;
  system_prompt?: string;
  agent_id?: string;
}) {
  return apiClient.post("/conversations", data);
}

export async function getConversation(id: string) {
  return apiClient.get(`/conversations/${id}`);
}

export async function updateConversation(
  id: string,
  data: { title?: string; model_name?: string; provider?: string }
) {
  return apiClient.patch(`/conversations/${id}`, data);
}

export async function deleteConversation(id: string) {
  return apiClient.delete(`/conversations/${id}`);
}

export async function sendMessage(conversationId: string, content: string) {
  return apiClient.post(`/conversations/${conversationId}/send`, { content });
}

export interface ToolCallEvent {
  name: string;
  args: Record<string, any>;
}

export interface ToolResultEvent {
  name: string;
  result: string;
}

export function sendMessageStream(
  conversationId: string,
  content: string,
  onThinkingStart: () => void,
  onThinkingToken: (token: string) => void,
  onThinkingEnd: () => void,
  onToken: (token: string) => void,
  onDone: () => void,
  onError: (err: string) => void,
  enableWebSearch: boolean = false,
  onToolCall?: (event: ToolCallEvent) => void,
  onToolResult?: (event: ToolResultEvent) => void,
): AbortController {
  const controller = new AbortController();
  const token = localStorage.getItem("access_token") || "";
  let inThinking = false;

  fetch(`/api/v1/conversations/${conversationId}/send-stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ content, enable_web_search: enableWebSearch }),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        const text = await response.text();
        onError(text);
        return;
      }
      const reader = response.body?.getReader();
      if (!reader) return;
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";
        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const data = line.slice(6);

          if (data === "[THINKING]") {
            if (!inThinking) {
              inThinking = true;
              onThinkingStart();
            }
            continue;
          }
          if (data === "[/THINKING]") {
            if (inThinking) {
              inThinking = false;
              onThinkingEnd();
            }
            continue;
          }
          if (data.startsWith("[TOOL_CALL]") && onToolCall) {
            try {
              onToolCall(JSON.parse(data.slice(12)));
            } catch { /* ignore parse error */ }
            continue;
          }
          if (data.startsWith("[TOOL_RESULT]") && onToolResult) {
            try {
              onToolResult(JSON.parse(data.slice(14)));
            } catch { /* ignore parse error */ }
            continue;
          }
          if (data === "[DONE]") {
            if (inThinking) {
              onThinkingEnd();
            }
            onDone();
            return;
          }

          if (inThinking) {
            onThinkingToken(data);
          } else {
            onToken(data);
          }
        }
      }
      if (inThinking) {
        onThinkingEnd();
      }
      onDone();
    })
    .catch((err) => {
      if (err.name !== "AbortError") {
        onError(err.message);
      }
    });

  return controller;
}
