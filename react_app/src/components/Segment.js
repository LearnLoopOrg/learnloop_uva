// src/components/Segment.js
import React, { useState, useRef, forwardRef, useImperativeHandle } from 'react';
import axios from 'axios';
import { FaArrowCircleUp } from 'react-icons/fa'; // Import the icon
import '../App.css';

const knowledgeTree = await axios.get('/api/getKnowledgeTree');

const Segment = forwardRef(({ data, onComplete, index, updateSegmentData, exampleConversation, topicTitle }, ref) => {
    const [answer, setAnswer] = useState('');
    const [isBlurry, setIsBlurry] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const inputRef = useRef(null);

    const chatHistory = data.chatHistory || [];

    const handleChange = (e) => {
        const value = e.target.value;
        setAnswer(value);
        setIsBlurry(value.length > 0);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        setIsLoading(true);

        const newChatHistory = [...chatHistory, { role: 'student', content: answer }];
        updateSegmentData(index, { chatHistory: newChatHistory });

        setAnswer('');
        setIsBlurry(false);

        const conversation = newChatHistory;
        let currentQuestion = data.question;

        try {
            await axios.post('/api/evaluateStudentResponse', {
                conversation,
                knowledgeTree,
                currentQuestion
            });

            const knowledgeTreeResponse = await axios.get('/api/getKnowledgeTree');
            const updatedKnowledgeTree = knowledgeTreeResponse.data;
            console.log('Updated knowledge tree:', updatedKnowledgeTree);

            updateSegmentData(index, { updatedKnowledgeTree });

            const topicData = updatedKnowledgeTree.find(topic => topic.topic === topicTitle);
            console.log('Topic data:', topicData);

            const subtopicData = topicData ? topicData.subtopics.find(subtopic => subtopic.question === currentQuestion) : null;

            let isCurrentQuestionFullyAnswered = false;
            console.log('Subtopic data:', subtopicData);
            if (subtopicData) {
                if (subtopicData.score) {
                    console.log('Subtopic score:', subtopicData.score);
                    const [obtained, total] = subtopicData.score.split('/').map(Number);
                    console.log('Score obtained:', obtained, 'Score total:', total);
                    isCurrentQuestionFullyAnswered = obtained === total;
                    console.log('Is current question fully answered:', isCurrentQuestionFullyAnswered);
                }
            }

            console.log('Generating teacher response');
            const generateResponse = await axios.post('/api/generateResponse', {
                conversation,
                knowledgeTree: updatedKnowledgeTree,
                exampleConversation,
                currentQuestion,
                isQuestionCompleted: isCurrentQuestionFullyAnswered
            });
            const teacherMessage = generateResponse.data.assistantResponse;

            const updatedChatHistory = [...newChatHistory, { role: 'teacher', content: teacherMessage }];
            updateSegmentData(index, { chatHistory: updatedChatHistory });

            if (isCurrentQuestionFullyAnswered) {
                console.log(`Vraag "${currentQuestion}" volledig beantwoord. Overgaan naar het volgende segment.`);
                onComplete(index);
            } else {
                console.log(`Vraag "${currentQuestion}" niet volledig beantwoord. Blijven op het huidige segment.`);
            }
        } catch (error) {
            console.error('Error in handleSubmit:', error.response ? error.response.data : error.message);
            const errorMessage = error.response && error.response.data && error.response.data.error
                ? `${error.response.data.error}: ${error.response.data.details}`
                : 'An error occurred. Please try again.';
            updateSegmentData(index, {
                chatHistory: [
                    ...newChatHistory,
                    { role: 'system', content: errorMessage },
                ],
            });
        } finally {
            setIsLoading(false);
        }
    };

    useImperativeHandle(ref, () => ({
        focusInput() {
            if (inputRef.current) {
                inputRef.current.focus();
                inputRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        },
    }));

    return (
        <div className="segment">
            <h3>{data.title}</h3>
            <p className={isBlurry ? 'blurry' : ''} dangerouslySetInnerHTML={{ __html: data.text }}></p>
            {data.question && (
                <p className="question">
                    <span className="circle">⚫</span>
                    {data.question}
                </p>
            )}
            {chatHistory.map((chat, idx) => (
                <div key={idx} className={`chat-message ${chat.role}`}>
                    <div className="message-content">
                        {chat.content}
                    </div>
                </div>
            ))}

            {isLoading && (
                <div className="loading-dots">
                    <span>●</span>
                    <span>●</span>
                    <span>●</span>
                </div>
            )}

            <form onSubmit={handleSubmit}>
                <input
                    type="text"
                    name="answer"
                    value={answer}
                    onChange={handleChange}
                    ref={inputRef}
                    autoComplete="off"
                    required
                />
                <button type="submit" aria-label="Verstuur">
                    <FaArrowCircleUp /> {/* Use the imported icon */}
                </button>
            </form>
        </div>
    );
});

export default Segment;
