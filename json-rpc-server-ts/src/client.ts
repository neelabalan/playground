import { 
  JsonRpcRequestSchema, 
  JsonRpcResponseSchema, 
  JsonRpcRequest, 
  JsonRpcResponse 
} from "./types";


export async function jsonRpcCall<TParams = any, TResult = any>(
  url: string,
  method: string,
  id: string,
  params?: TParams
): Promise<TResult> {
  const request: JsonRpcRequest = {
    jsonrpc: "2.0",
    method,
    params,
    id
  };

  // Validate request before sending (optional)
  const reqValidation = JsonRpcRequestSchema.safeParse(request);
  if (!reqValidation.success) {
    throw new Error("Invalid JSON-RPC request: " + JSON.stringify(reqValidation.error.format()));
  }

  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  const data = await response.json();

  // Validate response at runtime
  const resValidation = JsonRpcResponseSchema.safeParse(data);
  if (!resValidation.success) {
    throw new Error("Invalid JSON-RPC response: " + JSON.stringify(resValidation.error.format()));
  }

  const jsonRpcResponse: JsonRpcResponse = resValidation.data;

  if (jsonRpcResponse.error) {
    throw new Error(`JSON-RPC Error: ${jsonRpcResponse.error.message}`);
  }

  return jsonRpcResponse.result as TResult;
}


const simpleUUID = () => Math.random().toString(16).slice(2) + Date.now().toString(16);
async function main() {
  try {
    const result = await jsonRpcCall<{}, { serverTime: string; timezone: string }>(
      "http://localhost:4000/json-rpc",
      "getServerTime",
      simpleUUID(),
      {}
    );
    console.log("Server time:", result.serverTime, "Timezone:", result.timezone);
  } catch (err) {
    console.error("RPC call failed:", err);
  }
}

main();