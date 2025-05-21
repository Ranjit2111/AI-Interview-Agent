import React from 'react';

interface CoachFeedbackProps {
  feedback: {
    conciseness?: string;
    completeness?: string;
    technical_accuracy_depth?: string;
    contextual_alignment?: string;
    fixes_improvements?: string;
    star_support?: string;
    [key: string]: string | undefined; // Allow other keys, though we primarily use the above
  };
}

const CoachFeedbackDisplay: React.FC<CoachFeedbackProps> = ({ feedback }) => {
  const feedbackEntries = Object.entries(feedback).filter(([, value]) => value && value.trim() !== "" && !value.toLowerCase().includes("error: could not generate"));

  if (feedbackEntries.length === 0) {
    return <p className="text-sm text-gray-400 italic">No specific feedback points provided for this turn.</p>;
  }

  // A more descriptive title map
  const titleMap: { [key: string]: string } = {
    conciseness: "Conciseness",
    completeness: "Completeness",
    technical_accuracy_depth: "Technical Accuracy / Depth",
    contextual_alignment: "Contextual Alignment",
    fixes_improvements: "Fixes & Improvements",
    star_support: "STAR Method Application",
  };

  return (
    <div className="space-y-3">
      {feedbackEntries.map(([key, value]) => (
        <div key={key}>
          <h4 className="text-sm font-semibold text-yellow-400 mb-1">
            {titleMap[key] || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
          </h4>
          <p className="text-sm text-gray-200 whitespace-pre-wrap">{value}</p>
        </div>
      ))}
    </div>
  );
};

export default CoachFeedbackDisplay; 