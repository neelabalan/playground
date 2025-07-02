import { z } from "zod";

export const JsonRpcErrorSchema = z.object({
  code: z.number(),
  message: z.string(),
  data: z.optional(z.any()),
});

export const JsonRpcRequestSchema = z.object({
  jsonrpc: z.literal("2.0"),
  method: z.string(),
  params: z.optional(z.any()),
  id: z.union([z.string(), z.null()]),
});

export const JsonRpcResponseSchema = z.object({
  jsonrpc: z.literal("2.0"),
  result: z.optional(z.any()),
  error: z.optional(JsonRpcErrorSchema),
  id: z.union([z.number(), z.string(), z.null()]),
});

export const JsonRpcNotificationSchema = z.object({
  jsonrpc: z.literal("2.0"),
  method: z.string(),
  params: z.optional(z.any()),
});

export type JsonRpcError = z.infer<typeof JsonRpcErrorSchema>;
export type JsonRpcRequest = z.infer<typeof JsonRpcRequestSchema>;
export type JsonRpcResponse = z.infer<typeof JsonRpcResponseSchema>;
export type JsonRpcNotification = z.infer<typeof JsonRpcNotificationSchema>;

export const isJsonRpcRequest = (value: unknown): value is JsonRpcRequest =>
  JsonRpcRequestSchema.safeParse(value).success;

export const isJsonRpcResponse = (value: unknown): value is JsonRpcResponse =>
  JsonRpcRequestSchema.safeParse(value).success;

export const isJsonRpcNotification = (
  value: unknown
): value is JsonRpcNotification =>
  JsonRpcNotificationSchema.safeParse(value).success;
