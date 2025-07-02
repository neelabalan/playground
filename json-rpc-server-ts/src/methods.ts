import { JsonRpcResponse, JsonRpcRequest } from "./types";
export const getServerTime = (req: JsonRpcRequest): JsonRpcResponse => {
    return {
        jsonrpc: '2.0',
        id: req.id,
        result: {
            serverTime: new Date().toISOString(),
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        },
    };
};