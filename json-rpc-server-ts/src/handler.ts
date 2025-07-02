import { Request, Response } from 'express';
import { JsonRpcRequest, JsonRpcResponse} from './types';
import { getServerTime } from './methods';



const methodHandlers: { [key: string]: (req: JsonRpcRequest) => JsonRpcResponse } = {
    'getServerTime': getServerTime,
};

export const handleRequest = (req: Request, res: Response): void => {
    const jsonRpcRequest: JsonRpcRequest = req.body;

    // Validate JSON-RPC request format
    if (!jsonRpcRequest.jsonrpc || jsonRpcRequest.jsonrpc !== '2.0') {
        const errorResponse: JsonRpcResponse = {
            jsonrpc: '2.0',
            id: jsonRpcRequest.id || null,
            error: {
                code: -32600,
                message: 'Invalid Request',
                data: 'Missing or invalid jsonrpc version'
            }
        };
        res.status(400).json(errorResponse);
        return;
    }

    if (!jsonRpcRequest.method) {
        const errorResponse: JsonRpcResponse = {
            jsonrpc: '2.0',
            id: jsonRpcRequest.id || null,
            error: {
                code: -32600,
                message: 'Invalid Request',
                data: 'Missing method'
            }
        };
        res.status(400).json(errorResponse);
        return;
    }

    // Check if method exists
    const handler = methodHandlers[jsonRpcRequest.method];
    if (!handler) {
        const errorResponse: JsonRpcResponse = {
            jsonrpc: '2.0',
            id: jsonRpcRequest.id || null,
            error: {
                code: -32601,
                message: 'Method not found',
                data: `Method '${jsonRpcRequest.method}' is not supported`
            }
        };
        res.status(404).json(errorResponse);
        return;
    }

    try {
        const response = handler(jsonRpcRequest);
        res.json(response);
    } catch (error) {
        const errorResponse: JsonRpcResponse = {
            jsonrpc: '2.0',
            id: jsonRpcRequest.id || null,
            error: {
                code: -32603,
                message: 'Internal error',
                data: error instanceof Error ? error.message : 'Unknown error'
            }
        };
        res.status(500).json(errorResponse);
    }
};