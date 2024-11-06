
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
        const { conversation, knowledgeTree, currentQuestion } = req.body;

        const prompt = `
        Your volledige prompt hier...
        `;

        try {
            const response = await axios.post(
                `${endpoint}/openai/deployments/${deployment}/chat/completions?api-version=${apiVersion}`,
                {
                    messages: [{ role: 'user', content: prompt }],
                    temperature: 0.7,
                    response_format: { "type": "json_object" }
                },
                {
                    headers: {
                        'Content-Type': 'application/json',
                        'api-key': apiKey,
                    },
                }
            );

            let updates;
            try {
                const cleanedResponse = cleanResponse(response.data.choices[0].message.content);
                console.log(cleanedResponse);
                updates = JSON.parse(cleanedResponse);
                console.log('Parsed updates:', updates);
            } catch (parseError) {
                console.error('Error parsing OpenAI response:', parseError);
                return res.status(500).json({
                    error: 'Error parsing OpenAI response',
                    details: parseError.message,
                });
            }

            if (Object.keys(updates).length === 0) {
                console.log('No updates to knowledge tree');
                return res.status(200).json({ knowledgeTree });
            }

            // Update de kennisboom
            const knowledgeTreeData = knowledgeTree; // Zorg ervoor dat knowledgeTree correct is
            if (typeof updates === 'object' && !Array.isArray(updates)) {
                updates = [updates];
            }

            updates.forEach(update => {
                const { topic, subtopic, score, status } = update;
                knowledgeTreeData.forEach(topicData => {
                    if (topicData.topic === topic) {
                        topicData.subtopics.forEach(subtopicData => {
                            if (subtopicData.topic === subtopic) {
                                subtopicData.score = score;
                                subtopicData.status = status;
                                console.log(`Subtopic "${subtopic}" in topic "${topic}" bijgewerkt naar score: ${score}, status: ${status}`);
                            }
                        });
                    }
                });
            });

            // Optioneel, sla de bijgewerkte kennisboom op in een bestand
            const knowledgeTreePath = path.join(process.cwd(), 'data', 'knowledgeTree.json');
            console.log('Saving updated knowledgeTree to:', knowledgeTreePath);
            fs.writeFileSync(knowledgeTreePath, JSON.stringify(knowledgeTreeData, null, 2), 'utf-8');
            console.log('Updated knowledgeTree saved successfully.');

            res.status(200).json({ knowledgeTree: knowledgeTreeData });

        } catch (error) {
            console.error('Error in evaluateStudentResponseHandler:', error.response ? error.response.data : error.message);
            res.status(500).json({
                error: 'Error evaluating student response',
                details: error.response ? error.response.data : error.message,
            });
        }
    } else {
        res.status(405).json({ message: 'Only POST method allowed' });
    }
}
