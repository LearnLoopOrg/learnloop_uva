const fs = require('fs');
const path = require('path');

const resetKnowledgeTree = () => {
    const knowledgeTreePath = path.join(__dirname, 'data', 'knowledgeTree.json');

    // Lees de huidige kennisboom
    const data = fs.readFileSync(knowledgeTreePath, 'utf-8');
    const knowledgeTree = JSON.parse(data);

    // Iterate over alle topics en subtopics
    knowledgeTree.forEach(topic => {
        topic.subtopics.forEach(subtopic => {
            // Zet status naar "not asked"
            subtopic.status = "not asked";

            // Split de score en zet behaalde punten naar 0
            const scoreParts = subtopic.score.split('/');
            if (scoreParts.length === 2) {
                subtopic.score = `0/${scoreParts[1]}`;
            }
        });
    });

    // Schrijf de bijgewerkte kennisboom terug naar het bestand
    fs.writeFileSync(knowledgeTreePath, JSON.stringify(knowledgeTree, null, 2), 'utf-8');

    console.log('Kennisboom succesvol gereset.');
};

// Voer de resetfunctie uit
resetKnowledgeTree();
