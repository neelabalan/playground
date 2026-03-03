import React, { useRef, useEffect } from 'react';

const AutoExpandingTextarea = ({content, setContent}) => {
  const textareaRef = useRef(null);

  useEffect(() => {
    const textarea = textareaRef.current;
    textarea.style.height = 'auto';
    textarea.style.height = `${textarea.scrollHeight}px`;
  }, [content]);

  const handleInput = (e) => {
    setContent({id: content.id, note: e.target.value});
  };

  return (
    <textarea
      ref={textareaRef}
      value={content.note}
      onChange={handleInput}
      placeholder="What's on your mind?"
      rows="2"

    />
  );
};

export default AutoExpandingTextarea;
