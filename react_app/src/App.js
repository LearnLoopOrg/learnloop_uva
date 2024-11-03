// src/App.js
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Expander from './components/Expander';
import './App.css';
import knowledgeTreeData from './data/knowledgeTree.json';
import exampleConversationData from './data/exampleConversation.json';
import Header from './components/Header';

const App = () => {
  const [expanders, setExpanders] = useState(() =>
    knowledgeTreeData.map((topicItem) => ({
      title: topicItem.topic,
      segments: topicItem.subtopics.map((subtopicItem) => ({
        title: subtopicItem.topic,
        text: subtopicItem.theorie || '',
        question: subtopicItem.question || '',
        chatHistory: [],
      })),
      isCompleted: false,
      isOpen: false,
    }))
  );

  const [knowledgeTree, setKnowledgeTree] = useState(knowledgeTreeData);
  const [exampleConversation, setExampleConversation] = useState(exampleConversationData);
  const [conversation, setConversation] = useState([]);

  useEffect(() => {
    setExpanders((prev) =>
      prev.map((expander, index) =>
        index === 0 ? { ...expander, isOpen: true } : expander
      )
    );
  }, []);

  const handleExpanderComplete = async (index) => {
    setExpanders((prev) =>
      prev.map((expander, i) =>
        i === index
          ? { ...expander, isCompleted: true, isOpen: false }
          : expander
      )
    );
    console.log(`Expander "${expanders[index].title}" gemarkeerd als voltooid.`);

    if (index + 1 < expanders.length) {
      setExpanders((prev) =>
        prev.map((expander, i) =>
          i === index + 1 ? { ...expander, isOpen: true } : expander
        )
      );
      console.log(`Volgende expander "${expanders[index + 1].title}" geopend.`);
    }

    const currentExpander = expanders[index];
    const currentSegment = currentExpander.segments.find(segment => !segment.isAnswered);
    const currentQuestion = currentSegment ? currentSegment.question : '';

    console.log('Current question:', currentQuestion);
    console.log('Current segment:', currentSegment);

    try {
      const response = await axios.post('http://localhost:5000/evaluateStudentResponse', {
        conversation,
        knowledgeTree,
        currentQuestion
      });

      const updatedKnowledgeTree = response.data.knowledgeTree;
      setKnowledgeTree(updatedKnowledgeTree);

      const topicData = updatedKnowledgeTree.find(topic => topic.topic === currentExpander.title);
      const subtopicData = topicData ? topicData.subtopics.find(sub => sub.question === currentQuestion) : null;

      let isCurrentQuestionFullyAnswered = false;
      if (subtopicData && subtopicData.score) {
        const [obtained, total] = subtopicData.score.split('/').map(Number);
        isCurrentQuestionFullyAnswered = obtained === total;
        console.log(`Score voor onderwerp "${currentExpander.title}" en subonderwerp "${subtopicData.topic}": ${obtained}/${total}`);
      }

      await generateResponse(updatedKnowledgeTree, isCurrentQuestionFullyAnswered, currentQuestion);
      console.log('Response gegenereerd en toegevoegd aan gesprek.');

    } catch (error) {
      console.error('Error evaluating student response:', error);
    }
  };

  const handleExpanderToggle = (index) => {
    setExpanders((prev) =>
      prev.map((expander, i) =>
        i === index ? { ...expander, isOpen: !expander.isOpen } : expander
      )
    );
  };

  const updateSegmentData = (expanderIndex, segmentIndex, newSegmentData) => {
    setExpanders((prevExpanders) =>
      prevExpanders.map((expander, i) => {
        if (i === expanderIndex) {
          const updatedSegments = expander.segments.map((segment, j) => {
            if (j === segmentIndex) {
              return { ...segment, ...newSegmentData };
            }
            return segment;
          });
          return { ...expander, segments: updatedSegments };
        }
        return expander;
      })
    );

    if (newSegmentData.updatedKnowledgeTree) {
      setKnowledgeTree(newSegmentData.updatedKnowledgeTree);
    }

    if (newSegmentData.chatHistory) {
      setConversation((prevConversation) => [
        ...prevConversation,
        ...newSegmentData.chatHistory,
      ]);
    }
  };

  const generateResponse = async (updatedKnowledgeTree, isQuestionFullyAnswered, currentQuestion) => {
    try {
      const response = await axios.post('http://localhost:5000/generateResponse', {
        conversation,
        knowledgeTree: updatedKnowledgeTree,
        isQuestionCompleted: isQuestionFullyAnswered,
        currentQuestion,
        exampleConversation
      });
      const teacherMessage = response.data.assistantResponse;

      setConversation(prev => [...prev, { role: 'teacher', content: teacherMessage }]);
    } catch (error) {
      console.error('Error in generateResponse:', error.response ? error.response.data : error.message);
    }
  };

  return (
    <>
      <Header />
      <div className="app-container">
        <h1>Neuroplasticiteit</h1>
        <div className="main-content">
          {expanders.map((expander, expanderIndex) => (
            <Expander
              key={expanderIndex}
              title={expander.title}
              segments={expander.segments}
              isCompleted={expander.isCompleted}
              isOpen={expander.isOpen}
              onToggle={() => handleExpanderToggle(expanderIndex)}
              onComplete={() => handleExpanderComplete(expanderIndex)}
              updateSegmentData={(segmentIndex, newSegmentData) =>
                updateSegmentData(expanderIndex, segmentIndex, newSegmentData)
              }
              knowledgeTree={knowledgeTree}
              exampleConversation={exampleConversation}
            />
          ))}
        </div>
        <aside className="sidebar">
          {/* Additional actions or information */}
        </aside>
      </div>
    </>
  );
};

export default App;
