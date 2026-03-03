import React from "react";
import { useModal } from "../provider/ModalContext";
import AutoExpandingTextarea from "./AutoExpandingTextArea";

export default function Modal({ addThought, ...props }) {
  const { modalIsOpen, handleClose, content, setContent } = useModal();


  const handleClickOverlay = (event) => {
    if (event.target === event.currentTarget) {
      handleClose(event);
    }
  };

  const handleSave = (event) => {
    event.preventDefault();
    console.log(content)
    addThought(content);
    setContent({id: '', note: ''});
    handleClose(event);
  };

  return (
    <dialog onClick={handleClickOverlay} open={modalIsOpen} {...props}>
      <article>
        <AutoExpandingTextarea
          content={content}
          setContent={setContent}
        ></AutoExpandingTextarea>
        <footer>
          <button className="secondary" onClick={handleClose}>
            Cancel
          </button>
          <button onClick={handleSave}>Save</button>
        </footer>
      </article>
    </dialog>
  );
}
