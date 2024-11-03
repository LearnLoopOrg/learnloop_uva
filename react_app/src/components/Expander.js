// src/components/Expander.js
import React, { useRef, useEffect } from 'react';
import Segment from './Segment';

const Expander = ({
    title,
    segments,
    isCompleted,
    onComplete,
    isOpen,
    onToggle,
    updateSegmentData,
    knowledgeTree,
    exampleConversation,
}) => {
    const segmentRefs = useRef([]);

    // Focus on the first segment's input when the expander opens
    useEffect(() => {
        if (isOpen && segmentRefs.current[0]) {
            segmentRefs.current[0].focusInput();
        }
    }, [isOpen]);

    const handleSegmentComplete = (segmentIndex) => {
        console.log('Segment complete at index:', segmentIndex);

        // Als er meer segments zijn, ga naar de volgende
        if (segmentIndex + 1 < segments.length) {
            const nextIndex = segmentIndex + 1;
            console.log('Setting focus to next segment at index:', nextIndex);
            if (segmentRefs.current[nextIndex]) {
                segmentRefs.current[nextIndex].focusInput();
                console.log(`Focus verplaatst naar segment ${nextIndex}`);
            } else {
                console.warn(`Segment referentie voor index ${nextIndex} niet gevonden.`);
            }
        } else {
            // Alle segments in deze expander zijn voltooid
            console.log('All segments answered. Closing expander.');
            handleComplete();
        }
    };

    const handleComplete = () => {
        onComplete();
    };

    return (
        <div className="expander">
            <h2 onClick={onToggle}>
                {title} {isCompleted && <span>✅</span>}
            </h2>
            {isOpen && (
                <div>
                    {segments.map((segment, segmentIndex) => (
                        <Segment
                            key={segmentIndex}
                            ref={(ref) => {
                                segmentRefs.current[segmentIndex] = ref;
                            }}
                            data={segment}
                            index={segmentIndex}
                            onComplete={handleSegmentComplete}
                            updateSegmentData={updateSegmentData}
                            knowledgeTree={knowledgeTree} // Pass knowledgeTree as prop
                            exampleConversation={exampleConversation} // Pass exampleConversation as prop
                            topicTitle={title} // Pass title as topicTitle prop
                        />
                    ))}
                </div>
            )}
        </div>
    );
};

export default Expander;
