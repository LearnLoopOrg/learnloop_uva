
const fs = require('fs');
const path = require('path');

const resetKnowledgeTree = () => {
    const knowledgeTreePath = path.join(process.cwd(), 'data', 'knowledgeTree.json');

    const data = fs.readFileSync(knowledgeTreePath, 'utf-8');
    const knowledgeTree = JSON.parse(data);

    knowledgeTree.forEach(topic => {
        topic.subtopics.forEach(subtopic => {
            subtopic.status = "not asked";
            const scoreParts = subtopic.score.split('/');
            if (scoreParts.length === 2) {
                subtopic.score = `0/${scoreParts[1]}`;
            }
        });
    });

    fs.writeFileSync(knowledgeTreePath, JSON.stringify(knowledgeTree, null, 2), 'utf-8');
    console.log('Kennisboom succesvol gereset.');
};

export default async function handler(req, res) {
    // CORS headers instellen
    res.setHeader('Access-Control-Allow-Origin', 'https://learnloop-uva.vercel.app');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE');
    res.setHeader('Access-Control-Allow-Credentials', 'true');

    if (req.method === 'POST') {
        resetKnowledgeTree();
        res.status(200).json({ message: 'Knowledge tree reset successfully.' });
    } else {
        res.status(405).json({ message: 'Only POST method allowed' });
    }
}
