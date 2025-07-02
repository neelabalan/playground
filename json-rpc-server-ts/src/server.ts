import express from 'express';
import bodyParser from 'body-parser';
import { handleRequest } from './handler';

const app = express();
const PORT = process.env.PORT || 4000;

app.use(bodyParser.json());

app.post('/json-rpc', handleRequest);

app.listen(PORT, () => {
    console.log(`JSON-RPC server is running on http://localhost:${PORT}`);
});