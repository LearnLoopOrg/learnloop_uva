
const axios = require('axios');
const fs = require('fs');
const path = require('path');
require('dotenv').config({ path: '../.env', override: true });

const endpoint = process.env.AZURE_OPENAI_ENDPOINT || process.env.LL_OPENAI_API_ENDPOINT;
const apiKey = process.env.OPENAI_API_KEY || process.env.LL_OPENAI_API_KEY;
const deployment = process.env.AZURE_OPENAI_ENDPOINT ? "learnloop-4o" : "LLgpt-4o";
const apiVersion = '2024-08-01-preview'; // Specify the API version

const cleanResponse = (response) => {
    // Verwijder Markdown-formattering en andere ongewenste tekens
    return response.replace(/```json/g, '').replace(/```/g, '').trim();
};

export default async function handler(req, res) {
    // CORS headers instellen
    res.setHeader('Access-Control-Allow-Origin', 'https://learnloop-uva.vercel.app');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE');
    res.setHeader('Access-Control-Allow-Credentials', 'true');

    if (req.method === 'POST') {
        const { conversation, knowledgeTree, exampleConversation, currentQuestion, isQuestionCompleted } = req.body;

        const prompt = `
        Your volledige prompt hier...
        `;

        try {
            const response = await axios.post(
                `${endpoint}/openai/deployments/${deployment}/chat/completions?api-version=${apiVersion}`,
                {
                    messages: [{ role: 'user', content: prompt }],
                    temperature: 0.7,
                },
                {
                    headers: {
                        'Content-Type': 'application/json',
                        'api-key': apiKey,
                    },
                }
            );
            const assistantResponse = response.data.choices[0].message.content;
            res.status(200).json({ assistantResponse });
        } catch (error) {
            console.error('Error in generateResponseHandler:', error.response ? error.response.data : error.message);
            res.status(500).json({
                error: 'Error generating response',
                details: error.response ? error.response.data : error.message,
            });
        }
    } else {
        res.status(405).json({ message: 'Only POST method allowed' });
    }
}
