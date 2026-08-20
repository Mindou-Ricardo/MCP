export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH' | 'HEAD' | 'OPTIONS';

export interface ParsedEndpoint {
  method: HttpMethod;
  path: string;
  name: string;
  operation_id?: string | null;
  summary?: string | null;
  description?: string | null;
  security: Record<string, string[]>[];
}

export interface SpecParseResult {
  spec_id: number;
  filename: string;
  source_type: string;
  title?: string | null;
  version?: string | null;
  openapi_version: string;
  base_url?: string | null;
  endpoints: ParsedEndpoint[];
  endpoints_count: number;
}

export type ServerStatus = 'pending' | 'generating' | 'ready' | 'regenerating' | 'failed';

export type AuthType = 'none' | 'api_key' | 'bearer' | 'basic';

export interface AuthConfig {
  type: AuthType;
  header_name?: string | null;
  api_key?: string | null;
  username?: string | null;
  password?: string | null;
}

export interface ServerCreateRequest {
  spec_id: number;
  name: string;
  description?: string | null;
  base_url?: string | null;
  auth?: AuthConfig;
  include_endpoints?: string[] | null;
}

export interface GeneratedServer {
  id: number;
  name: string;
  description?: string | null;
  base_url?: string | null;
  auth_type: AuthType;
  status: ServerStatus;
  dir_name?: string | null;
  endpoints_count: number;
  error?: string | null;
  spec_id?: number | null;
  created_at: string;
  updated_at: string;
}

export interface ChatProvider {
  id: string;
  display_name: string;
  default_model: string;
  models: string[];
}

export type ChatRole = 'user' | 'assistant' | 'system' | 'tool';

export interface ChatMessage {
  role: ChatRole;
  content?: string | null;
  tool_calls?: Record<string, unknown>[] | null;
  tool_call_id?: string | null;
  name?: string | null;
}

export interface ChatRequestPayload {
  server_id: number;
  messages: ChatMessage[];
  model?: string | null;
  max_tool_iterations?: number;
}

export interface ToolCallInfo {
  id: string;
  name: string;
  arguments: Record<string, unknown>;
  arguments_raw?: string;
}

export interface ToolResultEvent {
  id: string;
  result: string;
}

export interface ChatEvent {
  kind: 'start' | 'delta' | 'tool_calls' | 'tool_result' | 'done' | 'error';
  data: unknown;
}
