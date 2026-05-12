import apiClient from "./client";

export interface ToolInfo {
  name: string;
  description: string;
  source: "builtin" | "mcp";
}

export async function listTools() {
  return apiClient.get<ToolInfo[]>("/tools");
}
